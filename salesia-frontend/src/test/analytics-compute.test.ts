import { describe, expect, it } from "vitest";

import {
  buildHistogram,
  buildTimeline,
  groupByPlan,
  groupByRegion,
  orderAmount,
  ticketStats,
} from "../modules/analytics/compute";
import type { Customer, OrderListItem } from "../types/api";

function order(overrides: Partial<OrderListItem>): OrderListItem {
  return {
    code: "PED-0001",
    company_name: "Acme",
    plan_name: "Web Negocio",
    monthly_total: 100,
    setup_total: 0,
    status: "confirmado",
    risk: "bajo",
    created_at: "2026-10-01T10:00:00",
    ...overrides,
  };
}

function customer(company: string, region: string): Customer {
  return {
    company_name: company,
    ruc: "20601234561",
    contact_name: "Contacto",
    email: "contacto@example.com",
    phone: null,
    region,
  };
}

describe("analytics compute", () => {
  it("computes the order amount as monthly plus setup", () => {
    expect(orderAmount(order({ monthly_total: 1490, setup_total: 500 }))).toBe(1990);
  });

  it("computes ticket statistics for confirmed orders", () => {
    const stats = ticketStats([
      order({ monthly_total: 1000 }),
      order({ monthly_total: 2000 }),
      order({ monthly_total: 3000 }),
      order({ monthly_total: 4000 }),
    ]);
    expect(stats.count).toBe(4);
    expect(stats.revenue).toBe(10000);
    expect(stats.average).toBe(2500);
    expect(stats.median).toBe(2500);
    expect(stats.min).toBe(1000);
    expect(stats.max).toBe(4000);
    expect(stats.stdDev).toBeCloseTo(1118.0339, 3);
  });

  it("returns empty statistics when there are no orders", () => {
    expect(ticketStats([])).toEqual({
      count: 0,
      revenue: 0,
      average: 0,
      median: 0,
      stdDev: 0,
      min: 0,
      max: 0,
    });
  });

  it("groups orders by plan ordered by revenue", () => {
    const slices = groupByPlan([
      order({ plan_name: "Arranque", monthly_total: 89 }),
      order({ plan_name: "Negocio", monthly_total: 189 }),
      order({ plan_name: "Negocio", monthly_total: 189 }),
    ]);
    expect(slices[0]).toEqual({ name: "Negocio", count: 2, revenue: 378 });
    expect(slices[1]).toEqual({ name: "Arranque", count: 1, revenue: 89 });
  });

  it("groups orders by the customer region", () => {
    const slices = groupByRegion(
      [
        order({ company_name: "Andes Café", monthly_total: 100 }),
        order({ company_name: "Desconocida", monthly_total: 50 }),
      ],
      [customer("Andes Café", "Lima")],
    );
    const lima = slices.find((slice) => slice.region === "Lima");
    const unknown = slices.find((slice) => slice.region === "Sin región");
    expect(lima).toEqual({ region: "Lima", count: 1, revenue: 100 });
    expect(unknown).toEqual({ region: "Sin región", count: 1, revenue: 50 });
  });

  it("builds a daily timeline sorted by date", () => {
    const points = buildTimeline([
      order({ created_at: "2026-10-03T09:00:00", monthly_total: 300 }),
      order({ created_at: "2026-10-01T09:00:00", monthly_total: 100 }),
      order({ created_at: "2026-10-01T15:00:00", monthly_total: 50 }),
    ]);
    expect(points).toEqual([
      { dia: "1 oct", valor: 150 },
      { dia: "3 oct", valor: 300 },
    ]);
  });

  it("buckets ticket amounts into thousands", () => {
    const buckets = buildHistogram([order({ monthly_total: 1490 })]);
    expect(buckets).toEqual([
      { rango: "0–1 mil", cantidad: 0 },
      { rango: "1–2 mil", cantidad: 1 },
    ]);
  });
});
