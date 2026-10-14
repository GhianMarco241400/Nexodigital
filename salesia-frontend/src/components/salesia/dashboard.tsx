import { useMemo, useState } from "react";
import { Link } from "@tanstack/react-router";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ArrowRight,
  ArrowUpRight,
  ClipboardList,
  CreditCard,
  ReceiptText,
  Sparkles,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { canView } from "@/data/access";
import { useAuth } from "@/modules/auth/AuthProvider";
import { formatDateTime, formatSoles, statusLabel } from "@/modules/orders/format";
import { useOrdersOverview } from "@/modules/orders/queries";
import { ApiError } from "@/services/api";
import type { OrderListItem } from "@/types/api";
import { DataTable, PageHeading, StateMenu, Status, type VisualState } from "./ui";
import { PedidoPanel } from "./panels";
import { useDemoRole } from "./shell";

const icons = {
  ventas: CreditCard,
  ticket: ReceiptText,
  pedidos: ClipboardList,
  clientes: Users,
} as const;

const MONTHS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];

const amountOf = (order: OrderListItem) => order.monthly_total + order.setup_total;

const sumAmounts = (orders: OrderListItem[]) =>
  orders.reduce((total, order) => total + amountOf(order), 0);

const sameMonth = (date: Date, reference: Date) =>
  date.getFullYear() === reference.getFullYear() && date.getMonth() === reference.getMonth();

const shortSoles = (value: number) =>
  value >= 1000 ? `S/ ${(value / 1000).toFixed(value % 1000 === 0 ? 0 : 1)}k` : `S/ ${value}`;

function topPlanName(orders: OrderListItem[]): string | null {
  const tally = new Map<string, number>();
  for (const order of orders) tally.set(order.plan_name, (tally.get(order.plan_name) ?? 0) + 1);
  let best: string | null = null;
  let bestCount = 0;
  for (const [name, count] of tally) {
    if (count > bestCount) {
      best = name;
      bestCount = count;
    }
  }
  return best;
}

export function Dashboard() {
  const [detailCode, setDetailCode] = useState<string | null>(null);
  const [state, setState] = useState<VisualState>("normal");
  const { role } = useDemoRole();
  const { user } = useAuth();
  const overview = useOrdersOverview();

  const ready = overview.isSuccess;
  const forbidden = overview.error instanceof ApiError && overview.error.status === 403;
  const items = useMemo(() => overview.data?.items ?? [], [overview.data]);
  const counts = overview.data?.counts;

  const summary = useMemo(() => {
    const confirmed = items.filter((order) => order.status === "confirmado");
    const now = new Date();
    const thisMonth = confirmed.filter((order) => sameMonth(new Date(order.created_at), now));

    const ventasMes = sumAmounts(thisMonth);
    const ticket = confirmed.length ? sumAmounts(confirmed) / confirmed.length : 0;
    const pendientes = (counts?.pendiente ?? 0) + (counts?.en_revision ?? 0);
    const clientes = new Set(items.map((order) => order.company_name)).size;

    const spark = (orders: OrderListItem[]) =>
      orders.length >= 2 ? orders.slice(0, 8).map(amountOf).reverse() : [];

    const metrics = [
      {
        label: "Ventas del mes",
        valor: ready ? formatSoles(ventasMes) : "—",
        cambio: `${thisMonth.length} confirmados`,
        nota: "en el mes en curso",
        icono: "ventas" as const,
        spark: ready ? spark(thisMonth) : [],
      },
      {
        label: "Ticket promedio",
        valor: ready ? formatSoles(ticket) : "—",
        cambio: `${confirmed.length} confirmados`,
        nota: "por pedido",
        icono: "ticket" as const,
        spark: ready ? spark(confirmed) : [],
      },
      {
        label: "Pedidos pendientes",
        valor: ready ? String(pendientes) : "—",
        cambio: "por revisar",
        nota: "requieren tu atención",
        icono: "pedidos" as const,
        spark: [],
      },
      {
        label: "Clientes activos",
        valor: ready ? String(clientes) : "—",
        cambio: `${counts?.total ?? 0} pedidos`,
        nota: "con solicitudes registradas",
        icono: "clientes" as const,
        spark: [],
      },
    ];

    const base = new Date();
    const chartData = Array.from({ length: 6 }, (_, index) => {
      const reference = new Date(base.getFullYear(), base.getMonth() - (5 - index), 1);
      const valor = sumAmounts(
        confirmed.filter((order) => sameMonth(new Date(order.created_at), reference)),
      );
      return { dia: MONTHS[reference.getMonth()] ?? "", valor };
    });
    const chartTotal = chartData.reduce((total, point) => total + point.valor, 0);

    const topPlan = topPlanName(confirmed);
    const insight = !ready
      ? "Estamos calculando el resumen de tu negocio."
      : pendientes > 0
        ? `Tienes ${pendientes} pedido${pendientes === 1 ? "" : "s"} esperando revisión.${
            topPlan ? ` ${topPlan} lidera la demanda.` : ""
          }`
        : confirmed.length > 0
          ? `Sumas ${formatSoles(sumAmounts(confirmed))} en ${confirmed.length} pedido${
              confirmed.length === 1 ? "" : "s"
            } confirmado${confirmed.length === 1 ? "" : "s"}.${
              topPlan ? ` ${topPlan} lidera la demanda.` : ""
            }`
          : "Aún no hay pedidos confirmados. Cuando lleguen, verás aquí tu resumen.";

    const rows = items.slice(0, 5).map((order) => ({
      codigo: order.code,
      cliente: order.company_name,
      combo: order.plan_name,
      total: amountOf(order),
      estado: statusLabel(order.status),
    }));

    const latest = items.reduce<OrderListItem | null>(
      (acc, order) => (!acc || order.created_at > acc.created_at ? order : acc),
      null,
    );

    return { metrics, chartData, chartTotal, insight, rows, latest, pendientes };
  }, [items, counts, ready]);

  const tableState: VisualState = forbidden
    ? "normal"
    : overview.isLoading
      ? "loading"
      : overview.isError
        ? "error"
        : summary.rows.length === 0
          ? "empty"
          : "normal";
  const displayState = state === "normal" ? tableState : state;

  const firstName = (user?.full_name ?? "equipo").split(" ")[0] ?? "equipo";

  return (
    <>
      <PageHeading
        title="Dashboard"
        description="Una vista clara de cómo va tu negocio."
        showDemoLabel={false}
        action={
          <Button asChild>
            <Link to={canView(role, "/pedidos") ? "/pedidos" : "/ventas"}>
              <ArrowUpRight />
              Ver {canView(role, "/pedidos") ? "pedidos" : "ventas"}
            </Link>
          </Button>
        }
      />
      <div className="welcome-line">
        <span>
          Buen día, {firstName}
          <span className="welcome-divider">/</span>
          <span className="text-muted-foreground">Aquí está tu resumen de tu negocio.</span>
        </span>
        {summary.latest ? (
          <span className="update-time">
            Actualizado {formatDateTime(summary.latest.created_at)}
          </span>
        ) : null}
      </div>
      <div className="metric-grid">
        {summary.metrics.map((metric, index) => {
          const Icon = icons[metric.icono];
          return (
            <article className="metric-card" key={metric.label}>
              <div className="metric-top">
                <span>{metric.label}</span>
                <div className={`metric-icon metric-icon-${metric.icono}`}>
                  <Icon />
                </div>
              </div>
              <div className="metric-value">{metric.valor}</div>
              <div className="metric-bottom">
                <div>
                  <span className={index === 2 ? "metric-attention" : "metric-change"}>
                    {index !== 2 && <ArrowUpRight />}
                    {metric.cambio}
                  </span>
                  <small>{metric.nota}</small>
                </div>
                {metric.spark.length > 0 && (
                  <div className="sparkline">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={metric.spark.map((value) => ({ v: value }))}>
                        <Area
                          dataKey="v"
                          stroke="var(--chart-cyan)"
                          fill="var(--cyan-soft)"
                          strokeWidth={1.6}
                          isAnimationActive={false}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>
            </article>
          );
        })}
      </div>
      <section className="sales-chart-section">
        <div className="section-heading">
          <div>
            <h2>Ventas por mes</h2>
            <p>Importe confirmado en los últimos seis meses.</p>
          </div>
        </div>
        <div className="chart-summary">
          <strong>{ready ? formatSoles(summary.chartTotal) : "—"}</strong>
          <div className="chart-legend">
            <span>
              <i className="legend-current" />
              Pedidos confirmados
            </span>
          </div>
        </div>
        <div className="main-chart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={summary.chartData} margin={{ top: 15, right: 12, left: 0, bottom: 4 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="3 5" vertical={false} />
              <XAxis
                dataKey="dia"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                dy={12}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                tickFormatter={shortSoles}
                width={63}
                tickCount={5}
              />
              <Tooltip
                formatter={(value) => formatSoles(Number(value))}
                contentStyle={{
                  background: "var(--card)",
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                  fontSize: 12,
                }}
              />
              <Line
                isAnimationActive={false}
                name="Confirmado"
                type="monotone"
                dataKey="valor"
                stroke="var(--primary)"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>
      <div className="dashboard-insight">
        <div className="insight-symbol">
          <Sparkles />
        </div>
        <div>
          <strong>
            {summary.pendientes > 0 ? "Revisa los pedidos pendientes" : "Resumen de tu negocio"}
          </strong>
          <p>{summary.insight}</p>
        </div>
        {canView(role, "/insights") && (
          <Button asChild variant="ghost">
            <Link to="/insights">
              Ver insights
              <ArrowRight />
            </Link>
          </Button>
        )}
      </div>
      <DataTable
        compact
        searchable={false}
        title={
          <div>
            <h2>Últimos pedidos</h2>
            <p className="section-description">Los movimientos más recientes de tu equipo.</p>
          </div>
        }
        toolbar={
          <>
            {canView(role, "/pedidos") && (
              <Button asChild variant="ghost" className="text-primary">
                <Link to="/pedidos">
                  Ver todos
                  <ArrowRight />
                </Link>
              </Button>
            )}
            <StateMenu onState={setState} />
          </>
        }
        state={displayState}
        forbidden={forbidden}
        rows={summary.rows}
        onRow={(row) => setDetailCode(String(row["codigo"]))}
        errorTitle="No pudimos cargar los pedidos"
        errorMessage={
          overview.error instanceof ApiError
            ? overview.error.message
            : "No pudimos cargar los pedidos."
        }
        onRetry={() => {
          void overview.refetch();
        }}
        columns={[
          {
            key: "codigo",
            label: "Pedido",
            render: (row) => <span className="table-code">{String(row["codigo"])}</span>,
          },
          {
            key: "cliente",
            label: "Cliente",
            render: (row) => (
              <div className="company-cell">
                <span className="company-avatar">
                  {String(row["cliente"])
                    .split(" ")
                    .map((part) => part[0])
                    .slice(0, 2)
                    .join("")}
                </span>
                <strong>{String(row["cliente"])}</strong>
              </div>
            ),
          },
          { key: "combo", label: "Combo" },
          {
            key: "total",
            label: "Total",
            render: (row) => (
              <span className="table-amount">{formatSoles(Number(row["total"]))}</span>
            ),
          },
          {
            key: "estado",
            label: "Estado",
            render: (row) => <Status>{String(row["estado"])}</Status>,
          },
        ]}
      />
      <PedidoPanel code={detailCode} onClose={() => setDetailCode(null)} />
    </>
  );
}
