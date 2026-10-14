const TOKEN_KEY = "salesia.access_token";

let memoryToken: string | null = null;

function storage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

export function getToken(): string | null {
  const store = storage();
  if (!store) return memoryToken;
  return store.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  memoryToken = token;
  storage()?.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  memoryToken = null;
  storage()?.removeItem(TOKEN_KEY);
}

export function hasToken(): boolean {
  return getToken() !== null;
}
