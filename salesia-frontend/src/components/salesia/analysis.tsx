import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ArrowUpRight,
  CheckCircle2,
  Download,
  Eye,
  FileChartColumn,
  Printer,
  Save,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { bayes } from "@/data/access";
import { useAuth } from "@/modules/auth/AuthProvider";
import { useAnalytics } from "@/modules/analytics/queries";
import { usePlans } from "@/modules/catalog/queries";
import { useCustomers } from "@/modules/customers/queries";
import { useOrdersOverview } from "@/modules/orders/queries";
import { formatSoles } from "@/modules/orders/format";
import { ApiError } from "@/services/api";
import type { PlanInfo } from "@/types/api";
import {
  DataTable,
  Field,
  FilterButton,
  InsightNote,
  PageHeading,
  StateMenu,
  TabBar,
  type Column,
  type VisualState,
} from "./ui";
import { RecordPanel } from "./panels";

const axis = { fill: "var(--muted-foreground)", fontSize: 12 };
const tip = {
  background: "var(--card)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  fontSize: 12,
};

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
];
const MONTHS_LONG = [
  "enero",
  "febrero",
  "marzo",
  "abril",
  "mayo",
  "junio",
  "julio",
  "agosto",
  "septiembre",
  "octubre",
  "noviembre",
  "diciembre",
];

function todayLabel(): string {
  const date = new Date();
  return `${date.getDate()} ${MONTHS_SHORT[date.getMonth()] ?? ""} ${date.getFullYear()}`;
}

function periodLabel(): string {
  const date = new Date();
  const days = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  const month = MONTHS_LONG[date.getMonth()] ?? "";
  return `01–${days} ${month} ${date.getFullYear()}`;
}

function monthLabel(): string {
  const date = new Date();
  return `${MONTHS_LONG[date.getMonth()] ?? ""} ${date.getFullYear()}`.replace(/^./, (c) =>
    c.toUpperCase(),
  );
}

function visualState(
  forbidden: boolean,
  isLoading: boolean,
  isError: boolean,
  isEmpty: boolean,
  manual: VisualState,
): VisualState {
  if (manual !== "normal") return manual;
  if (forbidden) return "normal";
  if (isLoading) return "loading";
  if (isError) return "error";
  if (isEmpty) return "empty";
  return "normal";
}

interface SavedAnalysis {
  nombre: string;
  tipo: string;
  fecha: string;
  usuario: string;
}

const SAVED_KEY = "salesia.analytics.saved";

function useSavedAnalyses() {
  const [items, setItems] = useState<SavedAnalysis[]>([]);

  useEffect(() => {
    const raw = typeof window === "undefined" ? null : window.localStorage.getItem(SAVED_KEY);
    if (!raw) return;
    try {
      setItems(JSON.parse(raw) as SavedAnalysis[]);
    } catch {
      window.localStorage.removeItem(SAVED_KEY);
    }
  }, []);

  const save = (item: SavedAnalysis) => {
    setItems((current) => {
      const next = [item, ...current].slice(0, 12);
      if (typeof window !== "undefined")
        window.localStorage.setItem(SAVED_KEY, JSON.stringify(next));
      return next;
    });
  };

  return { items, save };
}

export function Analytics() {
  const [tab, setTab] = useState("Resumen");
  const [manualState, setManualState] = useState<VisualState>("normal");
  const [a, setA] = useState("0.4");
  const [ba, setBa] = useState("0.75");
  const [b, setB] = useState("0.5");
  const [result, setResult] = useState<number | null>(null);
  const [error, setError] = useState(false);
  const [record, setRecord] = useState<Record<string, unknown> | null>(null);
  const [filter, setFilter] = useState("");
  const { user } = useAuth();
  const { model, forbidden, isLoading, isError, error: queryError } = useAnalytics();
  const { items: saved, save } = useSavedAnalyses();

  const displayState = visualState(
    forbidden,
    isLoading,
    isError,
    model.ticket.count === 0,
    manualState,
  );

  const peakBucket = useMemo(
    () =>
      model.histogram.reduce((best, bucket) => (bucket.cantidad > best.cantidad ? bucket : best), {
        rango: "—",
        cantidad: 0,
      }),
    [model.histogram],
  );

  const metrics = [
    {
      label: "Media de ventas",
      value: formatSoles(model.ticket.average),
      note: "Promedio del importe por venta",
    },
    {
      label: "Mediana",
      value: formatSoles(model.ticket.median),
      note: "Valor central de las ventas",
    },
    { label: "Cantidad de ventas", value: String(model.ticket.count), note: "Pedidos confirmados" },
    {
      label: "Desviación estándar",
      value: formatSoles(model.ticket.stdDev),
      note: "Dispersión respecto a la media",
    },
  ];

  const distribution = model.plans.map((slice) => ({ nombre: slice.name, valor: slice.count }));

  const onSave = () => {
    save({
      nombre: `Análisis de ${monthLabel()}`,
      tipo: tab,
      fecha: todayLabel(),
      usuario: user?.full_name ?? "Equipo",
    });
    toast.success("Análisis guardado", { description: "Se guardó en tu historial." });
  };

  return (
    <>
      <PageHeading
        title="Analytics"
        description="Transforma tus datos comerciales en decisiones informadas."
        showDemoLabel={false}
        action={
          <Button onClick={onSave}>
            <Save />
            Guardar análisis
          </Button>
        }
      >
        <FilterButton onApply={setFilter} />
        <StateMenu onState={setManualState} />
      </PageHeading>
      <TabBar
        items={["Resumen", "Variables", "Probabilidad y Bayes", "Historial"]}
        value={tab}
        onChange={setTab}
      />
      {filter && (
        <div className="filter-summary">
          Vista filtrada: {filter === "__previous__" ? "Septiembre 2026" : filter}
        </div>
      )}
      {displayState !== "normal" ? (
        <div className="mt-6">
          <DataTable
            columns={[]}
            rows={[]}
            state={displayState}
            forbidden={forbidden}
            errorTitle="No pudimos cargar el análisis"
            errorMessage={
              queryError instanceof ApiError ? queryError.message : "No pudimos cargar los datos."
            }
          />
        </div>
      ) : tab === "Historial" ? (
        <div className="mt-6">
          <DataTable
            rows={saved}
            onRow={setRecord}
            emptyTitle="Aún no hay análisis guardados"
            emptyMessage="Usa «Guardar análisis» para conservar una vista en tu historial."
            columns={[
              { key: "nombre", label: "Análisis" },
              { key: "tipo", label: "Tipo" },
              { key: "fecha", label: "Fecha" },
              { key: "usuario", label: "Creado por" },
            ]}
          />
        </div>
      ) : tab === "Probabilidad y Bayes" ? (
        <div className="bayes-layout">
          <section>
            <h2>Teorema de Bayes</h2>
            <p className="section-description mt-2">
              Probabilidad de confirmar un pedido (A) cuando su revisión es favorable (B).
            </p>
            <div className="formula">
              P(A|B) = <span>P(B|A) · P(A) / P(B)</span>
            </div>
            <form
              className="space-y-5"
              onSubmit={(event) => {
                event.preventDefault();
                const value = bayes(Number(a), Number(ba), Number(b));
                setResult(value);
                setError(value === null);
              }}
            >
              <Field label="P(A) · Probabilidad de confirmar un pedido">
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  required
                  value={a}
                  onChange={(event) => setA(event.target.value)}
                />
              </Field>
              <Field label="P(B|A) · Revisión favorable dado un pedido confirmado">
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  required
                  value={ba}
                  onChange={(event) => setBa(event.target.value)}
                />
              </Field>
              <Field label="P(B) · Probabilidad de revisión favorable">
                <Input
                  type="number"
                  step="0.01"
                  min="0.01"
                  max="1"
                  required
                  value={b}
                  onChange={(event) => setB(event.target.value)}
                />
              </Field>
              {error && (
                <p className="text-danger text-sm">
                  Las probabilidades no son consistentes. P(B) debe ser mayor que cero y no menor
                  que P(B|A) · P(A).
                </p>
              )}
              <Button type="submit">Calcular</Button>
            </form>
          </section>
          <section className="bayes-result">
            {result === null ? (
              <>
                <div className="product-icon">
                  <FileChartColumn />
                </div>
                <h2>Resultado del análisis</h2>
                <p>Completa los valores para visualizar la probabilidad posterior.</p>
              </>
            ) : (
              <>
                <span className="text-primary text-sm font-medium">PROBABILIDAD POSTERIOR</span>
                <strong className="result-number">{(result * 100).toFixed(1)}%</strong>
                <h3>Probabilidad de confirmar el pedido</h3>
                <div className="calculation-steps">
                  <p>
                    <b>1.</b> Multiplicamos P(B|A) por P(A):
                    <br />
                    {ba} · {a} = {(Number(ba) * Number(a)).toFixed(3)}
                  </p>
                  <p>
                    <b>2.</b> Dividimos entre P(B):
                    <br />
                    {(Number(ba) * Number(a)).toFixed(3)} / {b} = {result.toFixed(3)}
                  </p>
                  <p>
                    <b>3.</b> Si la revisión es favorable, la probabilidad de confirmar el pedido es{" "}
                    <b>{(result * 100).toFixed(1)}%</b>.
                  </p>
                </div>
              </>
            )}
          </section>
        </div>
      ) : tab === "Variables" ? (
        <div className="analytics-sections">
          <div className="analytics-chart-grid">
            <section className="chart-block">
              <h2>Variable cuantitativa: ticket de venta</h2>
              <p className="section-description">Importe confirmado en soles por fecha.</p>
              <div className="analysis-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={model.timeline}>
                    <CartesianGrid vertical={false} stroke="var(--border)" />
                    <XAxis dataKey="dia" tick={axis} axisLine={false} tickLine={false} />
                    <YAxis tick={axis} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={tip} formatter={(value) => formatSoles(Number(value))} />
                    <Line
                      isAnimationActive={false}
                      dataKey="valor"
                      name="Importe"
                      stroke="var(--primary)"
                      dot={false}
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>
            <section className="chart-block">
              <h2>Variable aleatoria: combo vendido</h2>
              <p className="section-description">Frecuencia discreta por combo.</p>
              <div className="analysis-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={distribution} layout="vertical" margin={{ left: 35 }}>
                    <CartesianGrid horizontal={false} stroke="var(--border)" />
                    <XAxis type="number" tick={axis} axisLine={false} />
                    <YAxis
                      type="category"
                      dataKey="nombre"
                      tick={axis}
                      width={90}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip contentStyle={tip} />
                    <Bar
                      isAnimationActive={false}
                      dataKey="valor"
                      name="Ventas"
                      fill="var(--chart-cyan)"
                      radius={[0, 3, 3, 0]}
                      barSize={24}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>
          </div>
          <InsightNote title="Variables para entender la demanda">
            El importe de venta es una variable cuantitativa continua; el combo vendido es una
            variable categórica con una distribución de frecuencias.
          </InsightNote>
        </div>
      ) : (
        <div className="analytics-sections">
          <div className="metric-grid analytics-metrics">
            {metrics.map((metric) => (
              <article className="metric-card" key={metric.label}>
                <span className="text-sm text-muted-foreground">{metric.label}</span>
                <strong className="metric-value block">{metric.value}</strong>
                <span className="text-xs text-muted-foreground">{metric.note}</span>
              </article>
            ))}
          </div>
          <section className="chart-block">
            <div className="section-heading">
              <div>
                <h2>Distribución del importe de ventas</h2>
                <p>Comparación de media y mediana · {monthLabel()}</p>
              </div>
              <div className="flex gap-4 text-xs text-muted-foreground">
                <span>
                  Media <b className="text-primary">{formatSoles(model.ticket.average)}</b>
                </span>
                <span>
                  Mediana{" "}
                  <b className="text-accent-foreground">{formatSoles(model.ticket.median)}</b>
                </span>
              </div>
            </div>
            <div className="analysis-chart">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={model.histogram} margin={{ top: 10, right: 30 }}>
                  <CartesianGrid vertical={false} strokeDasharray="3 5" stroke="var(--border)" />
                  <XAxis dataKey="rango" axisLine={false} tickLine={false} tick={axis} />
                  <YAxis tick={axis} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={tip} />
                  <Bar
                    isAnimationActive={false}
                    dataKey="cantidad"
                    name="Cantidad de ventas"
                    fill="var(--primary)"
                    barSize={64}
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>
          <InsightNote title={`La mayoría de ventas se concentra entre ${peakBucket.rango}`}>
            La media es {formatSoles(model.ticket.average)} y la mediana{" "}
            {formatSoles(model.ticket.median)}. Los combos de entrada concentran la mayor cantidad
            de pedidos.
          </InsightNote>
        </div>
      )}
      <RecordPanel title="Análisis guardado" record={record} onClose={() => setRecord(null)} />
    </>
  );
}

export function Insights() {
  const [manualState, setManualState] = useState<VisualState>("normal");
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const { model, forbidden, isLoading, isError, error, refetch } = useAnalytics();

  const displayState = visualState(
    forbidden,
    isLoading,
    isError,
    model.insights.length === 0,
    manualState,
  );

  const refresh = () => {
    void refetch();
    toast.success("Insights actualizados", {
      description: "Se recalcularon con los datos más recientes.",
    });
  };

  return (
    <>
      <PageHeading
        title="Insights"
        description="Lo que tus números dicen, en palabras claras."
        showDemoLabel={false}
        action={
          <Button onClick={refresh}>
            <Sparkles />
            Actualizar insights
          </Button>
        }
      >
        <StateMenu onState={setManualState} />
      </PageHeading>
      {displayState !== "normal" ? (
        <DataTable
          rows={[]}
          columns={[]}
          state={displayState}
          forbidden={forbidden}
          errorTitle="No pudimos cargar los insights"
          errorMessage={error instanceof ApiError ? error.message : "No pudimos cargar los datos."}
        />
      ) : (
        <div className="insights-list">
          {model.insights.map((insight) => (
            <article className="insight-card" key={insight.titulo}>
              <div className="insight-card-main">
                <span className="insight-category">
                  <Sparkles />
                  {insight.tipo}
                </span>
                <h2>{insight.titulo}</h2>
                <p>{insight.observacion}</p>
                <Button
                  variant="link"
                  className="px-0 mt-3"
                  onClick={() =>
                    setDetail({
                      ...insight.evidencia,
                      Observación: insight.observacion,
                      Valor: insight.valor,
                    })
                  }
                >
                  Ver evidencia
                  <ArrowUpRight />
                </Button>
              </div>
              <div className="insight-card-number">
                <strong>{insight.valor}</strong>
                <span>{insight.cambio}</span>
              </div>
            </article>
          ))}
        </div>
      )}
      <RecordPanel title="Evidencia del insight" record={detail} onClose={() => setDetail(null)} />
    </>
  );
}

interface ReportDefinition {
  nombre: string;
  descripcion: string;
  tipo: "Ventas" | "Productos" | "Clientes" | "Estadístico";
}

const REPORTS: ReportDefinition[] = [
  { nombre: "Reporte de ventas", descripcion: "Pedidos confirmados e ingresos", tipo: "Ventas" },
  {
    nombre: "Reporte de productos",
    descripcion: "Planes del catálogo y sus precios",
    tipo: "Productos",
  },
  {
    nombre: "Reporte de clientes",
    descripcion: "Empresas y distribución regional",
    tipo: "Clientes",
  },
  {
    nombre: "Reporte estadístico",
    descripcion: "Media, mediana y dispersión del ticket",
    tipo: "Estadístico",
  },
];

interface ReportData {
  columns: Column[];
  rows: Record<string, unknown>[];
}

function csvCell(value: unknown): string {
  const text = value === null || value === undefined ? "" : String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function toCsv(columns: Column[], rows: Record<string, unknown>[]): string {
  const header = columns.map((column) => csvCell(column.label)).join(",");
  const body = rows.map((row) => columns.map((column) => csvCell(row[column.key])).join(","));
  return [header, ...body].join("\n");
}

export function Reportes() {
  const [preview, setPreview] = useState<ReportDefinition | null>(null);
  const [manualState, setManualState] = useState<VisualState>("normal");
  const [exportOpen, setExportOpen] = useState(false);
  const [exportReport, setExportReport] = useState(REPORTS[0]?.nombre ?? "Reporte de ventas");
  const [exportFormat, setExportFormat] = useState("CSV");

  const { model, forbidden, isLoading, isError, error } = useAnalytics();
  const customersQuery = useCustomers();
  const plansQuery = usePlans();

  const customers = customersQuery.data ?? [];
  const plans = plansQuery.data ?? [];

  const dataFor = (tipo: ReportDefinition["tipo"]): ReportData => {
    if (tipo === "Ventas") {
      return {
        columns: [
          { key: "numero", label: "Pedido" },
          { key: "cliente", label: "Cliente" },
          { key: "fecha", label: "Fecha" },
          {
            key: "total",
            label: "Total",
            render: (row) => formatSoles(Number(row["total"])),
          },
        ],
        rows: model.confirmed.map((order) => ({
          numero: order.code,
          cliente: order.company_name,
          fecha: order.created_at.slice(0, 10),
          total: order.monthly_total + order.setup_total,
        })),
      };
    }
    if (tipo === "Productos") {
      return {
        columns: [
          { key: "nombre", label: "Producto" },
          { key: "codigo", label: "Código" },
          {
            key: "mensual",
            label: "Mensual",
            render: (row) => formatSoles(Number(row["mensual"])),
          },
          {
            key: "instalacion",
            label: "Instalación",
            render: (row) => formatSoles(Number(row["instalacion"])),
          },
        ],
        rows: plans.map((plan: PlanInfo) => ({
          nombre: plan.name,
          codigo: plan.code,
          mensual: plan.monthly_price,
          instalacion: plan.setup_price,
        })),
      };
    }
    if (tipo === "Clientes") {
      return {
        columns: [
          { key: "nombre", label: "Empresa" },
          { key: "region", label: "Región" },
          { key: "correo", label: "Correo" },
        ],
        rows: customers.map((customer) => ({
          nombre: customer.company_name,
          region: customer.region ?? "—",
          correo: customer.email,
        })),
      };
    }
    return {
      columns: [
        { key: "metrica", label: "Métrica" },
        { key: "valor", label: "Valor" },
      ],
      rows: [
        { metrica: "Ventas confirmadas", valor: String(model.ticket.count) },
        { metrica: "Ingresos confirmados", valor: formatSoles(model.ticket.revenue) },
        { metrica: "Media del ticket", valor: formatSoles(model.ticket.average) },
        { metrica: "Mediana del ticket", valor: formatSoles(model.ticket.median) },
        { metrica: "Desviación estándar", valor: formatSoles(model.ticket.stdDev) },
      ],
    };
  };

  const previewData = preview ? dataFor(preview.tipo) : null;
  const summaryValue =
    preview?.tipo === "Clientes"
      ? String(customers.length)
      : preview?.tipo === "Productos"
        ? String(plans.length)
        : formatSoles(model.ticket.revenue);
  const summaryLabel =
    preview?.tipo === "Clientes"
      ? "Clientes"
      : preview?.tipo === "Productos"
        ? "Planes"
        : "Ventas confirmadas";

  const displayState = visualState(
    forbidden,
    isLoading || customersQuery.isLoading || plansQuery.isLoading,
    isError || customersQuery.isError || plansQuery.isError,
    false,
    manualState,
  );

  const runExport = () => {
    const definition = REPORTS.find((report) => report.nombre === exportReport);
    if (!definition) return;
    if (exportFormat !== "CSV") {
      toast.info("Formato disponible próximamente", {
        description: "Por ahora puedes exportar tus reportes en CSV.",
      });
      return;
    }
    const { columns, rows } = dataFor(definition.tipo);
    const blob = new Blob([`\uFEFF${toCsv(columns, rows)}`], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${definition.nombre.toLowerCase().replace(/\s+/g, "-")}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
    setExportOpen(false);
    toast.success("Reporte exportado", { description: `Se descargó ${definition.nombre}.csv` });
  };

  return (
    <>
      <PageHeading
        title="Reportes"
        description="La información de tu negocio, lista para compartir."
        showDemoLabel={false}
        action={
          <Button onClick={() => setExportOpen(true)}>
            <Download />
            Exportar
          </Button>
        }
      >
        <FilterButton />
        <StateMenu onState={setManualState} />
      </PageHeading>
      {displayState !== "normal" ? (
        <DataTable
          state={displayState}
          rows={[]}
          columns={[]}
          forbidden={forbidden}
          errorTitle="No pudimos cargar los reportes"
          errorMessage={error instanceof ApiError ? error.message : "No pudimos cargar los datos."}
        />
      ) : (
        <div className="report-grid">
          {REPORTS.map((report) => (
            <article className="report-card" key={report.nombre}>
              <div className="report-thumb">
                <div className="paper-preview">
                  <div className="paper-header" />
                  <div className="paper-line" />
                  <div className="paper-line short" />
                  <div className="paper-bars">
                    {[35, 60, 45, 75, 55, 85].map((value, index) => (
                      <div
                        className={`paper-bar bar-${index}`}
                        key={index}
                        style={{ height: `${value}%` }}
                      />
                    ))}
                  </div>
                  <div className="paper-line" />
                  <div className="paper-line" />
                </div>
                <span>{monthLabel().toUpperCase()}</span>
              </div>
              <div className="report-info">
                <div className="flex items-center gap-2 mb-2">
                  <FileChartColumn className="size-4 text-primary" />
                  <h3>{report.nombre}</h3>
                </div>
                <p>{report.descripcion}</p>
                <div className="flex justify-between items-center mt-5">
                  <span className="text-xs text-muted-foreground">Actualizado hoy</span>
                  <Button variant="outline" size="sm" onClick={() => setPreview(report)}>
                    <Eye />
                    Vista previa
                  </Button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
      <Dialog
        open={preview !== null}
        onOpenChange={(open) => {
          if (!open) setPreview(null);
        }}
      >
        <DialogContent className="report-dialog max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogTitle>{preview?.nombre}</DialogTitle>
          <DialogDescription>Vista imprimible · {periodLabel()}</DialogDescription>
          {previewData ? (
            <div className="print-report">
              <div className="flex justify-between border-b pb-5">
                <div>
                  <h2>SalesIA</h2>
                  <p>{preview?.nombre}</p>
                </div>
                <span>{monthLabel()}</span>
              </div>
              <div className="summary-band">
                <div>
                  <span>Periodo</span>
                  <strong>{periodLabel()}</strong>
                </div>
                <div>
                  <span>{summaryLabel}</span>
                  <strong>{summaryValue}</strong>
                </div>
              </div>
              <DataTable
                compact
                searchable={false}
                rows={previewData.rows}
                columns={previewData.columns}
              />
              <p className="text-xs text-muted-foreground mt-6">
                Documento interno · SalesIA · Datos del sistema
              </p>
            </div>
          ) : null}
          <div className="flex justify-end gap-2 print-hidden">
            <Button variant="outline" onClick={() => setExportOpen(true)}>
              <Download />
              Exportar
            </Button>
            <Button
              onClick={() =>
                toast.success("Vista lista para imprimir", {
                  description: "Usa la opción de impresión de tu navegador.",
                })
              }
            >
              <Printer />
              Imprimir
            </Button>
          </div>
        </DialogContent>
      </Dialog>
      <Dialog open={exportOpen} onOpenChange={setExportOpen}>
        <DialogContent>
          <DialogTitle>Exportar reporte</DialogTitle>
          <DialogDescription>Descarga los datos actuales de tu negocio en CSV.</DialogDescription>
          <Field label="Reporte">
            <select value={exportReport} onChange={(event) => setExportReport(event.target.value)}>
              {REPORTS.map((report) => (
                <option key={report.nombre}>{report.nombre}</option>
              ))}
            </select>
          </Field>
          <Field label="Formato">
            <select value={exportFormat} onChange={(event) => setExportFormat(event.target.value)}>
              <option>CSV</option>
              <option>PDF</option>
              <option>Excel (.xlsx)</option>
            </select>
          </Field>
          <Button onClick={runExport}>
            <Download />
            Exportar
          </Button>
        </DialogContent>
      </Dialog>
    </>
  );
}
