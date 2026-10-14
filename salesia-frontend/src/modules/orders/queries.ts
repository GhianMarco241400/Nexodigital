import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, request } from "@/services/api";
import type { OrderCounts, OrderDetail, OrderListResponse, OrderStatus } from "@/types/api";

export interface OrderListParams {
  status: OrderStatus | null;
  excludeStatus?: OrderStatus | null;
  q: string;
  page: number;
  pageSize: number;
}

export const ORDER_PAGE_SIZE = 20;

function retry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError) {
    if (error.status === 0) return failureCount < 2;
    return error.status >= 500 && failureCount < 1;
  }
  return failureCount < 1;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export const orderKeys = {
  all: ["orders"] as const,
  list: (params: OrderListParams) => ["orders", "list", params] as const,
  counts: ["orders", "counts"] as const,
  overview: ["orders", "overview"] as const,
  detail: (code: string) => ["orders", "detail", code] as const,
};

export function useOrders(params: OrderListParams) {
  return useQuery({
    queryKey: orderKeys.list(params),
    queryFn: ({ signal }) =>
      request<OrderListResponse>(
        `/orders${buildQuery({
          status: params.status ?? undefined,
          exclude_status: params.excludeStatus ?? undefined,
          q: params.q.trim() || undefined,
          page: params.page,
          page_size: params.pageSize,
        })}`,
        { signal },
      ),
    placeholderData: (previous) => previous,
    retry,
  });
}

export function useOrderCounts(enabled = true) {
  return useQuery({
    queryKey: orderKeys.counts,
    queryFn: ({ signal }) => request<OrderListResponse>(`/orders?page=1&page_size=1`, { signal }),
    select: (data): OrderCounts => data.counts,
    enabled,
    staleTime: 60_000,
    retry,
  });
}

export function useOrdersOverview() {
  return useQuery({
    queryKey: orderKeys.overview,
    queryFn: ({ signal }) => request<OrderListResponse>(`/orders?page=1&page_size=100`, { signal }),
    staleTime: 60_000,
    retry,
  });
}

export function useOrder(code: string | null) {
  return useQuery({
    queryKey: orderKeys.detail(code ?? ""),
    enabled: code !== null,
    queryFn: ({ signal }) =>
      request<OrderDetail>(`/orders/${encodeURIComponent(code ?? "")}`, { signal }),
    retry,
  });
}

function useOrderAction<Variables>(
  code: string,
  run: (variables: Variables) => Promise<OrderDetail>,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: run,
    onSuccess: (detail) => {
      queryClient.setQueryData(orderKeys.detail(detail.code), detail);
      void queryClient.invalidateQueries({ queryKey: ["orders", "list"] });
      void queryClient.invalidateQueries({ queryKey: orderKeys.counts });
      void queryClient.invalidateQueries({ queryKey: orderKeys.overview });
    },
  });
}

function postOrder(code: string, path: string, body?: unknown): Promise<OrderDetail> {
  return request<OrderDetail>(`/orders/${encodeURIComponent(code)}${path}`, {
    method: "POST",
    body,
  });
}

export function useRunReview(code: string) {
  return useOrderAction<void>(code, () => postOrder(code, "/review"));
}

export function useConfirmOrder(code: string) {
  return useOrderAction<void>(code, () => postOrder(code, "/confirm"));
}

export function useRejectOrder(code: string) {
  return useOrderAction<string>(code, (reason) => postOrder(code, "/reject", { reason }));
}
