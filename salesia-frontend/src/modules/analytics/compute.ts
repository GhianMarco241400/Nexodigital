import { formatSoles } from "@/modules/orders/format";
import type { Customer, OrderCounts, OrderListItem } from "@/types/api";

const MONTHS_SHORT = [
  "ene",
  "feb",
  "mar",
  "abr",
  "may",
  "jun",
  "jul",
  "ago",
  "sep",
  "oct",
  "nov",
  "dic",
] as const;

export const orderAmount = (order: OrderListItem): number =>
  order.monthly_total + order.setup_total;

export interface TicketStats {
  count: number;
  revenue: number;
  average: number;
  median: number;
  stdDev: number;
  min: number;
  max: number;
}

export interface PlanSlice {
  name: string;
  count: number;
  revenue: number;
}

export interface RegionSlice {
  region: string;
  count: number;
  revenue: number;
}

export interface TimelinePoint {
  dia: string;
  valor: number;
}

export interface HistogramBucket {
  rango: string;
  cantidad: number;
}

export interface SeriesPoint {
  label: string;
  revenue: number;
  count: number;
}

export interface InsightCard {
  titulo: string;
  observacion: string;
  valor: string;
  cambio: string;
  tipo: string;
  evidencia: Record<string, string>;
}

export interface AnalyticsModel {
  ticket: TicketStats;
  plans: PlanSlice[];
  regions: RegionSlice[];
  timeline: TimelinePoint[];
  monthly: SeriesPoint[];
  histogram: HistogramBucket[];
  insights: InsightCard[];
  confirmed: OrderListItem[];
  counts: OrderCounts | undefined;
}

function dayLabel(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const month = MONTHS_SHORT[date.getMonth()] ?? "";
  return `${date.getDate()} ${month}`;
}

export function ticketStats(orders: OrderListItem[]): TicketStats {
  const tickets = orders.map(orderAmount);
  const count = tickets.length;
  if (count === 0) {
    return { count: 0, revenue: 0, average: 0, median: 0, stdDev: 0, min: 0, max: 0 };
  }
  const revenue = tickets.reduce((total, value) => total + value, 0);
  const average = revenue / count;
  const sorted = [...tickets].sort((a, b) => a - b);
  const middle = Math.floor(count / 2);
  const median =
    count % 2 === 0
      ? ((sorted[middle - 1] ?? 0) + (sorted[middle] ?? 0)) / 2
      : (sorted[middle] ?? 0);
  const variance = tickets.reduce((total, value) => total + (value - average) ** 2, 0) / count;
  return {
    count,
    revenue,
    average,
    median,
    stdDev: Math.sqrt(variance),
    min: sorted[0] ?? 0,
    max: sorted[count - 1] ?? 0,
  };
}

export function groupByPlan(orders: OrderListItem[]): PlanSlice[] {
  const slices = new Map<string, PlanSlice>();
  for (const order of orders) {
    const slice = slices.get(order.plan_name) ?? { name: order.plan_name, count: 0, revenue: 0 };
    slice.count += 1;
    slice.revenue += orderAmount(order);
    slices.set(order.plan_name, slice);
  }
  return [...slices.values()].sort((a, b) => b.revenue - a.revenue);
}

export function groupByRegion(orders: OrderListItem[], customers: Customer[]): RegionSlice[] {
  const lookup = new Map(
    customers.map((customer) => [customer.company_name, customer.region ?? "Sin región"]),
  );
  const slices = new Map<string, RegionSlice>();
  for (const order of orders) {
    const region = lookup.get(order.company_name) ?? "Sin región";
    const slice = slices.get(region) ?? { region, count: 0, revenue: 0 };
    slice.count += 1;
    slice.revenue += orderAmount(order);
    slices.set(region, slice);
  }
  return [...slices.values()].sort((a, b) => b.revenue - a.revenue);
}

export function buildTimeline(orders: OrderListItem[]): TimelinePoint[] {
  const points = new Map<string, TimelinePoint>();
  for (const order of orders) {
    const day = order.created_at.slice(0, 10);
    const point = points.get(day) ?? { dia: dayLabel(order.created_at), valor: 0 };
    point.valor += orderAmount(order);
    points.set(day, point);
  }
  return [...points.entries()].sort((a, b) => a[0].localeCompare(b[0])).map(([, point]) => point);
}

export function buildMonthly(orders: OrderListItem[], months = 6): SeriesPoint[] {
  const base = new Date();
  return Array.from({ length: months }, (_, index) => {
    const reference = new Date(base.getFullYear(), base.getMonth() - (months - 1 - index), 1);
    const ordersInMonth = orders.filter((order) => {
      const date = new Date(order.created_at);
      return (
        date.getFullYear() === reference.getFullYear() && date.getMonth() === reference.getMonth()
      );
    });
    const label = MONTHS_SHORT[reference.getMonth()] ?? "";
    return {
      label: label.charAt(0).toUpperCase() + label.slice(1),
      revenue: ordersInMonth.reduce((total, order) => total + orderAmount(order), 0),
      count: ordersInMonth.length,
    };
  });
}

export function buildHistogram(orders: OrderListItem[], width = 1000): HistogramBucket[] {
  const tickets = orders.map(orderAmount);
  if (tickets.length === 0) return [];
  const top = Math.max(...tickets);
  const buckets = Math.max(1, Math.ceil(top / width));
  const counts = new Array<number>(buckets).fill(0);
  for (const ticket of tickets) {
    const index = Math.min(buckets - 1, Math.max(0, Math.floor(ticket / width)));
    counts[index] = (counts[index] ?? 0) + 1;
  }
  return counts.map((cantidad, index) => ({ rango: `${index}–${index + 1} mil`, cantidad }));
}

export function buildInsights(
  input: Pick<AnalyticsModel, "ticket" | "plans" | "regions" | "monthly">,
): InsightCard[] {
  const { ticket, plans, regions, monthly } = input;
  const cards: InsightCard[] = [];

  const last = monthly[monthly.length - 1];
  const previous = monthly[monthly.length - 2];
  if (last && previous && previous.revenue > 0) {
    const change = ((last.revenue - previous.revenue) / previous.revenue) * 100;
    cards.push({
      titulo: change >= 0 ? "El mes va en ascenso" : "El mes está por debajo del anterior",
      observacion: `Las ventas ${
        change >= 0 ? "crecieron" : "cayeron"
      } ${Math.abs(change).toFixed(1)}% frente al mes anterior.`,
      valor: `${change >= 0 ? "+" : ""}${change.toFixed(1)}%`,
      cambio: "vs. mes anterior",
      tipo: "Tendencia",
      evidencia: {
        "Mes actual": formatSoles(last.revenue),
        "Mes anterior": formatSoles(previous.revenue),
        "Pedidos del mes": String(last.count),
      },
    });
  }

  const topPlan = plans[0];
  if (topPlan && ticket.count > 0) {
    const share = (topPlan.count / ticket.count) * 100;
    cards.push({
      titulo: `${topPlan.name} lidera la demanda`,
      observacion: `${topPlan.count} de ${ticket.count} pedidos confirmados corresponden a ${topPlan.name}.`,
      valor: `${share.toFixed(0)}%`,
      cambio: "de las ventas",
      tipo: "Productos",
      evidencia: {
        Combo: topPlan.name,
        Pedidos: String(topPlan.count),
        Ingresos: formatSoles(topPlan.revenue),
      },
    });
  }

  const topRegion = regions[0];
  if (topRegion && ticket.revenue > 0) {
    const share = (topRegion.revenue / ticket.revenue) * 100;
    cards.push({
      titulo: `${topRegion.region} concentra los ingresos`,
      observacion: `${topRegion.region} aporta el ${share.toFixed(0)}% de los ingresos confirmados.`,
      valor: `${share.toFixed(0)}%`,
      cambio: "de los ingresos",
      tipo: "Regiones",
      evidencia: {
        Región: topRegion.region,
        Pedidos: String(topRegion.count),
        Ingresos: formatSoles(topRegion.revenue),
      },
    });
  }

  if (ticket.count > 0) {
    cards.push({
      titulo: "Ticket promedio del periodo",
      observacion: `El ticket promedio es ${formatSoles(ticket.average)} y la mediana ${formatSoles(ticket.median)}.`,
      valor: formatSoles(ticket.average),
      cambio: "ticket promedio",
      tipo: "Estadística",
      evidencia: {
        "Ventas confirmadas": String(ticket.count),
        Ingresos: formatSoles(ticket.revenue),
        Media: formatSoles(ticket.average),
        Mediana: formatSoles(ticket.median),
        "Desviación estándar": formatSoles(ticket.stdDev),
      },
    });
  }

  return cards;
}

export function computeAnalytics(
  orders: OrderListItem[],
  customers: Customer[],
  counts?: OrderCounts,
): AnalyticsModel {
  const confirmed = orders.filter((order) => order.status === "confirmado");
  const ticket = ticketStats(confirmed);
  const plans = groupByPlan(confirmed);
  const regions = groupByRegion(confirmed, customers);
  const monthly = buildMonthly(confirmed);
  return {
    ticket,
    plans,
    regions,
    monthly,
    timeline: buildTimeline(confirmed),
    histogram: buildHistogram(confirmed),
    confirmed,
    counts,
    insights: buildInsights({ ticket, plans, regions, monthly }),
  };
}
