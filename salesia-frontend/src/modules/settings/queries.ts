import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { request } from "@/services/api";
import type { ReviewConfig, ReviewMode, ReviewProvider, ReviewTestResult } from "@/types/api";

export const reviewConfigKey = ["settings", "review"] as const;

export interface ReviewConfigUpdate {
  mode?: ReviewMode;
  provider?: ReviewProvider;
  model?: string;
}

export function useReviewConfig(enabled = true) {
  return useQuery({
    queryKey: reviewConfigKey,
    queryFn: ({ signal }) => request<ReviewConfig>("/settings/review", { signal }),
    enabled,
    staleTime: 30_000,
  });
}

export function useUpdateReviewConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (update: ReviewConfigUpdate) =>
      request<ReviewConfig>("/settings/review", { method: "PUT", body: update }),
    onSuccess: (config) => {
      queryClient.setQueryData(reviewConfigKey, config);
    },
  });
}

export function useTestReview() {
  return useMutation({
    mutationFn: () => request<ReviewTestResult>("/settings/review/test", { method: "POST" }),
  });
}
