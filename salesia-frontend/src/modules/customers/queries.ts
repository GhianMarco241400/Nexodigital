import { useQuery } from "@tanstack/react-query";
import { ApiError, request } from "@/services/api";
import type { Customer } from "@/types/api";

function retry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError) {
    if (error.status === 0) return failureCount < 2;
    return error.status >= 500 && failureCount < 1;
  }
  return failureCount < 1;
}

export const customerKeys = {
  all: ["customers"] as const,
};

export function useCustomers() {
  return useQuery({
    queryKey: customerKeys.all,
    queryFn: ({ signal }) => request<Customer[]>("/customers", { signal }),
    staleTime: 5 * 60_000,
    retry,
  });
}
