import { clearToken, getToken } from "@/modules/auth/token";

const rawBaseUrl = import.meta.env["VITE_API_URL"] as string | undefined;

export const API_BASE_URL =
  rawBaseUrl && rawBaseUrl.trim() ? rawBaseUrl.trim().replace(/\/$/, "") : "http://127.0.0.1:8000";

export const UNAUTHORIZED_EVENT = "salesia:unauthorized";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  auth?: boolean;
  signal?: AbortSignal;
}

function messageFromDetail(detail: unknown): string | null {
  if (typeof detail === "string" && detail.trim()) return detail.trim();
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          const msg = (item as { msg?: unknown }).msg;
          return typeof msg === "string" ? msg : null;
        }
        return null;
      })
      .filter((value): value is string => Boolean(value));
    if (parts.length > 0) return parts.join(" ");
  }
  return null;
}

async function parseErrorMessage(response: Response): Promise<string> {
  if (response.status === 401) return "Tu sesión venció. Inicia sesión de nuevo.";
  if (response.status === 403) return "No tienes permiso para ver esta sección.";

  let detail: unknown;
  try {
    const payload = (await response.json()) as { detail?: unknown };
    detail = payload.detail;
  } catch {
    detail = undefined;
  }

  const detailMessage = messageFromDetail(detail);
  if (detailMessage) return detailMessage;

  if (response.status === 404) return "No se encontró el recurso solicitado.";
  if (response.status === 429) return "Demasiados intentos. Intenta de nuevo en un momento.";
  return "Ocurrió un error inesperado. Intenta de nuevo.";
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true, signal } = options;

  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const init: RequestInit = { method, headers };
  if (body !== undefined) init.body = JSON.stringify(body);
  if (signal) init.signal = signal;

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError("No se pudo conectar con el servidor.", 0);
  }

  if (!response.ok) {
    if (response.status === 401) {
      clearToken();
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
      }
    }
    throw new ApiError(await parseErrorMessage(response), response.status);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  return request<T>(path, signal ? { signal } : {});
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body, auth: false });
}
