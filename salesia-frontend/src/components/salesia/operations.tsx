import { useEffect, useState } from "react";
import { AlertTriangle, Package, Plus, ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  combos,
  movimientos,
  clientes,
  proveedores,
  vendedores,
  usuarios,
  extras,
  categorias,
  soles,
} from "@/data/salesia";
import {
  PageHeading,
  DataTable,
  FilterButton,
  StateMenu,
  Status,
  TabBar,
  NewButton,
  type VisualState,
  type Column,
} from "./ui";
import { PedidoPanel, RecordPanel, FormPanel } from "./panels";
import { ORDER_PAGE_SIZE, useOrders } from "@/modules/orders/queries";
import {
  ORDER_TABS,
  formatSoles,
  formatDateTime,
  riskLabel,
  statusLabel,
} from "@/modules/orders/format";
import { ApiError } from "@/services/api";
const money = (r: Record<string, unknown>, key = "total") => (
  <span className="table-amount">{soles(Number(r[key]))}</span>
);
const status = (r: Record<string, unknown>) => <Status>{String(r["estado"])}</Status>;
const company = (r: Record<string, unknown>) => (
  <span className="font-medium text-foreground">{String(r["nombre"] ?? r["cliente"])}</span>
);
export function Pedidos() {
  const [tab, setTab] = useState("Todos");
  const [detailCode, setDetailCode] = useState<string | null>(null);
  const [form, setForm] = useState(false);
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  useEffect(() => {
    const id = setTimeout(() => {
      setSearch(query);
      setPage(1);
    }, 300);
    return () => clearTimeout(id);
  }, [query]);
  const tabs = ORDER_TABS.filter((t) => t.status !== "confirmado");
  const activeTab = tabs.find((t) => t.label === tab) ?? tabs[0]!;
  const listQuery = useOrders({
    status: activeTab.status,
    excludeStatus: activeTab.status === null ? "confirmado" : null,
    q: search,
    page,
    pageSize: ORDER_PAGE_SIZE,
  });
  const data = listQuery.data;
  const rows = (data?.items ?? []).map((item) => ({
    codigo: item.code,
    cliente: item.company_name,
    combo: item.plan_name,
    total: item.monthly_total + item.setup_total,
    estado: statusLabel(item.status),
    riesgo: riskLabel(item.risk),
  }));
  const total = data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / ORDER_PAGE_SIZE));
  const forbidden = listQuery.error instanceof ApiError && listQuery.error.status === 403;
  const state: VisualState = forbidden
    ? "normal"
    : listQuery.isLoading
      ? "loading"
      : listQuery.isError
        ? "error"
        : rows.length === 0
          ? "empty"
          : "normal";
  return (
    <>
      <PageHeading
        title="Pedidos"
        description="Revisa, valida y da seguimiento a las solicitudes de tus clientes."
        showDemoLabel={false}
        action={<NewButton label="Nuevo pedido" onClick={() => setForm(true)} />}
      />
      <div className="module-tabs">
        <TabBar
          items={tabs.map((t) => t.label)}
          value={tab}
          onChange={(v) => {
            setTab(v);
            setPage(1);
          }}
        />
        <span className="text-sm text-muted-foreground">{total} pedidos</span>
      </div>
      <DataTable
        serverSide
        rows={rows}
        state={state}
        forbidden={forbidden}
        searchValue={query}
        onSearchChange={setQuery}
        page={page}
        pageCount={pageCount}
        pageSize={ORDER_PAGE_SIZE}
        onPageChange={setPage}
        total={total}
        placeholder="Buscar pedido o cliente..."
        errorTitle="No pudimos cargar los pedidos"
        errorMessage={
          listQuery.error instanceof ApiError
            ? listQuery.error.message
            : "No pudimos cargar los pedidos."
        }
        onRetry={() => {
          void listQuery.refetch();
        }}
        onRow={(r) => setDetailCode(String(r["codigo"]))}
        columns={[
          {
            key: "codigo",
            label: "Código",
            render: (r) => <span className="table-code">{String(r["codigo"])}</span>,
          },
          { key: "cliente", label: "Cliente", render: company },
          { key: "combo", label: "Combo" },
          {
            key: "total",
            label: "Total",
            render: (r) => <span className="table-amount">{formatSoles(Number(r["total"]))}</span>,
          },
          { key: "estado", label: "Estado", render: status },
          { key: "riesgo", label: "Riesgo", render: (r) => <Status>{String(r["riesgo"])}</Status> },
        ]}
      />
      <PedidoPanel code={detailCode} onClose={() => setDetailCode(null)} />
      <FormPanel module="Pedidos" open={form} onClose={() => setForm(false)} />
    </>
  );
}
export function Ventas() {
  const [detailCode, setDetailCode] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  useEffect(() => {
    const id = setTimeout(() => {
      setSearch(query);
      setPage(1);
    }, 300);
    return () => clearTimeout(id);
  }, [query]);
  const listQuery = useOrders({ status: "confirmado", q: search, page, pageSize: ORDER_PAGE_SIZE });
  const data = listQuery.data;
  const rows = (data?.items ?? []).map((item) => ({
    codigo: item.code,
    cliente: item.company_name,
    combo: item.plan_name,
    total: item.monthly_total + item.setup_total,
    fecha: formatDateTime(item.created_at),
    estado: statusLabel(item.status),
  }));
  const total = data?.total ?? 0;
  const counts = data?.counts;
  const pageCount = Math.max(1, Math.ceil(total / ORDER_PAGE_SIZE));
  const vendido = counts?.ingresos_confirmado ?? 0;
  const cantidad = counts?.confirmado ?? 0;
  const ticket = cantidad > 0 ? vendido / cantidad : 0;
  const forbidden = listQuery.error instanceof ApiError && listQuery.error.status === 403;
  const state: VisualState = forbidden
    ? "normal"
    : listQuery.isLoading
      ? "loading"
      : listQuery.isError
        ? "error"
        : rows.length === 0
          ? "empty"
          : "normal";
  return (
    <>
      <PageHeading
        title="Ventas"
        description="Ventas generadas al confirmar los pedidos revisados y aprobados."
        showDemoLabel={false}
      />
      <div className="summary-band">
        <div>
          <span>Total vendido</span>
          <strong>{formatSoles(vendido)}</strong>
        </div>
        <div>
          <span>Ventas confirmadas</span>
          <strong>{cantidad}</strong>
        </div>
        <div>
          <span>Ticket promedio</span>
          <strong>{formatSoles(ticket)}</strong>
        </div>
      </div>
      <DataTable
        serverSide
        rows={rows}
        state={state}
        forbidden={forbidden}
        searchValue={query}
        onSearchChange={setQuery}
        page={page}
        pageCount={pageCount}
        pageSize={ORDER_PAGE_SIZE}
        onPageChange={setPage}
        total={total}
        placeholder="Buscar venta o cliente..."
        errorTitle="No pudimos cargar las ventas"
        errorMessage={
          listQuery.error instanceof ApiError
            ? listQuery.error.message
            : "No pudimos cargar las ventas."
        }
        onRetry={() => {
          void listQuery.refetch();
        }}
        onRow={(r) => setDetailCode(String(r["codigo"]))}
        columns={[
          {
            key: "codigo",
            label: "Pedido",
            render: (r) => <span className="table-code">{String(r["codigo"])}</span>,
          },
          { key: "cliente", label: "Cliente", render: company },
          { key: "combo", label: "Combo" },
          {
            key: "total",
            label: "Total",
            render: (r) => <span className="table-amount">{formatSoles(Number(r["total"]))}</span>,
          },
          {
            key: "fecha",
            label: "Fecha",
            render: (r) => <span className="text-muted-foreground">{String(r["fecha"])}</span>,
          },
          { key: "estado", label: "Estado", render: status },
        ]}
      />
      <PedidoPanel code={detailCode} onClose={() => setDetailCode(null)} />
    </>
  );
}
export function Inventario() {
  const [tab, setTab] = useState("Cupos disponibles");
  const [state, setState] = useState<VisualState>("normal");
  const [filter, setFilter] = useState("");
  const [form, setForm] = useState(false);
  const [record, setRecord] = useState<Record<string, unknown> | null>(null);
  return (
    <>
      <PageHeading
        title="Inventario"
        description="Controla la capacidad disponible de tus combos por región."
        action={<NewButton label="Registrar movimiento" onClick={() => setForm(true)} />}
      />
      <div className="module-tabs">
        <TabBar items={["Cupos disponibles", "Movimientos"]} value={tab} onChange={setTab} />
        <div className="flex gap-2">
          <FilterButton onApply={setFilter} />
          <StateMenu onState={setState} />
        </div>
      </div>
      {tab === "Movimientos" ? (
        <DataTable
          state={state}
          rows={movimientos.filter((m) => !filter || Object.values(m).join(" ").includes(filter))}
          onRow={setRecord}
          columns={[
            { key: "codigo", label: "Movimiento" },
            { key: "combo", label: "Combo" },
            { key: "region", label: "Región" },
            { key: "tipo", label: "Tipo", render: (r) => <Status>{String(r["tipo"])}</Status> },
            { key: "cantidad", label: "Cupos" },
            { key: "fecha", label: "Fecha" },
          ]}
        />
      ) : state !== "normal" ? (
        <DataTable rows={[]} columns={[]} state={state} />
      ) : (
        <>
          <div className="inventory-alert">
            <AlertTriangle />
            <div>
              <strong>2 combos con pocos cupos</strong>
              <p>Tienda Online y App Business tienen menos de 5 cupos disponibles.</p>
            </div>
          </div>
          <div className="inventory-grid">
            {combos
              .filter((c) => !filter || Object.values(c).join(" ").includes(filter))
              .map((c) => (
                <article className="inventory-item" key={c.id}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="product-icon">
                        <Package />
                      </div>
                      <div>
                        <h3>{c.nombre}</h3>
                        <span className="text-xs text-muted-foreground">
                          {c.region} · {c.categoria}
                        </span>
                      </div>
                    </div>
                    {c.cupos < 5 && <Status>Medio</Status>}
                  </div>
                  <div className="cupos">
                    <strong>{c.cupos}</strong>
                    <span>de 25 cupos disponibles</span>
                  </div>
                  <progress
                    className={c.cupos < 5 ? "low-progress" : ""}
                    value={c.cupos}
                    max={25}
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-3">
                    <span>{25 - c.cupos} cupos asignados</span>
                    <span>{Math.round((c.cupos / 25) * 100)}% disponible</span>
                  </div>
                </article>
              ))}
          </div>
        </>
      )}
      <FormPanel module="Inventario" open={form} onClose={() => setForm(false)} />
      <RecordPanel title="Movimiento" record={record} onClose={() => setRecord(null)} />
    </>
  );
}
const catalog: Record<string, { description: string; rows: object[]; columns: Column[] }> = {
  Clientes: {
    description: "Toda la información de las empresas con las que trabajas.",
    rows: clientes,
    columns: [
      { key: "nombre", label: "Empresa", render: company },
      { key: "ruc", label: "RUC" },
      { key: "contacto", label: "Contacto" },
      { key: "region", label: "Región" },
      { key: "estado", label: "Estado", render: status },
    ],
  },
  Productos: {
    description: "Gestiona tus combos, servicios adicionales y categorías.",
    rows: combos,
    columns: [
      { key: "nombre", label: "Combo", render: company },
      { key: "categoria", label: "Categoría" },
      { key: "precio", label: "Precio fijo", render: (r) => money(r, "precio") },
      { key: "cupos", label: "Cupos disponibles" },
    ],
  },
  Proveedores: {
    description: "Tus aliados para entregar mejores productos digitales.",
    rows: proveedores,
    columns: [
      { key: "nombre", label: "Proveedor", render: company },
      { key: "servicio", label: "Servicio" },
      { key: "contacto", label: "Contacto" },
      { key: "estado", label: "Estado", render: status },
    ],
  },
  Vendedores: {
    description: "El equipo comercial y su rendimiento de ventas.",
    rows: vendedores,
    columns: [
      { key: "nombre", label: "Vendedor", render: company },
      { key: "region", label: "Región" },
      { key: "ventas", label: "Ventas" },
      { key: "total", label: "Total vendido", render: (r) => money(r) },
      { key: "estado", label: "Estado", render: status },
    ],
  },
  "Usuarios y roles": {
    description: "Gestiona los accesos de tu equipo a SalesIA.",
    rows: usuarios,
    columns: [
      { key: "nombre", label: "Usuario", render: company },
      { key: "email", label: "Correo electrónico" },
      { key: "rol", label: "Rol" },
      { key: "estado", label: "Estado", render: status },
    ],
  },
};
export function Maintenance({ module }: { module: string }) {
  const data = catalog[module];
  const [tab, setTab] = useState("Combos");
  const [state, setState] = useState<VisualState>("normal");
  const [form, setForm] = useState(false);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [filter, setFilter] = useState("");
  if (!data) return null;
  const rows =
    module === "Productos" && tab === "Extras"
      ? extras
      : module === "Productos" && tab === "Categorías"
        ? categorias
        : data.rows;
  const columns =
    module === "Productos" && tab === "Extras"
      ? [
          { key: "nombre", label: "Extra", render: company },
          { key: "categoria", label: "Categoría" },
          {
            key: "precio",
            label: "Precio",
            render: (r: Record<string, unknown>) => money(r, "precio"),
          },
        ]
      : module === "Productos" && tab === "Categorías"
        ? [
            { key: "nombre", label: "Categoría", render: company },
            { key: "descripcion", label: "Descripción" },
            { key: "cantidad", label: "Productos" },
          ]
        : data.columns;
  return (
    <>
      <PageHeading
        title={module}
        description={data.description}
        action={<NewButton onClick={() => setForm(true)} />}
      />
      {module === "Productos" && (
        <div className="mb-6">
          <TabBar items={["Combos", "Extras", "Categorías"]} value={tab} onChange={setTab} />
        </div>
      )}
      <DataTable
        rows={rows.filter((r) => !filter || Object.values(r).join(" ").includes(filter))}
        columns={columns}
        onRow={setDetail}
        state={state}
        placeholder={`Buscar ${module.toLowerCase()}...`}
        toolbar={
          <>
            <FilterButton onApply={setFilter} />
            <StateMenu onState={setState} />
          </>
        }
      />
      <FormPanel
        module={
          module === "Usuarios y roles"
            ? "Usuarios"
            : module === "Productos" && tab !== "Combos"
              ? tab
              : module
        }
        open={form}
        onClose={() => setForm(false)}
      />
      <RecordPanel record={detail} title={module} onClose={() => setDetail(null)} />
    </>
  );
}
