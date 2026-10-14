import { useMemo } from "react";

import { useCustomers } from "@/modules/customers/queries";
import { useOrdersOverview } from "@/modules/orders/queries";
import { ApiError } from "@/services/api";
import { computeAnalytics, type AnalyticsModel } from "./compute";

export function useAnalytics() {
  const orders = useOrdersOverview();
  const customers = useCustomers();

  const model = useMemo<AnalyticsModel>(
    () => computeAnalytics(orders.data?.items ?? [], customers.data ?? [], orders.data?.counts),
    [orders.data, customers.data],
  );

  const error = orders.error ?? customers.error;
  const forbidden = error instanceof ApiError && error.status === 403;

  return {
    model,
    error,
    forbidden,
    isLoading: orders.isLoading || customers.isLoading,
    isError: orders.isError || customers.isError,
    orders,
    customers,
    refetch: () => Promise.all([orders.refetch(), customers.refetch()]),
  };
}
