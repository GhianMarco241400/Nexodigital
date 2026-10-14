import { useQuery } from "@tanstack/react-query";
import { ApiError, request } from "@/services/api";
import type { ExtraInfo, PlanInfo } from "@/types/api";

function retry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError) {
    if (error.status === 0) return failureCount < 2;
    return error.status >= 500 && failureCount < 1;
  }
  return failureCount < 1;
}

export const catalogKeys = {
  plans: ["catalog", "plans"] as const,
  extras: ["catalog", "extras"] as const,
};

export function usePlans() {
  return useQuery({
    queryKey: catalogKeys.plans,
    queryFn: ({ signal }) => request<PlanInfo[]>("/plans", { signal }),
    staleTime: 5 * 60_000,
    retry,
  });
}

export function useExtras() {
  return useQuery({
    queryKey: catalogKeys.extras,
    queryFn: ({ signal }) => request<ExtraInfo[]>("/extras", { signal }),
    staleTime: 5 * 60_000,
    retry,
  });
}
