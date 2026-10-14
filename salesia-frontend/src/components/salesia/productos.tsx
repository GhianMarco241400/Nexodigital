import { useState } from "react";

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { ApiError } from "@/services/api";
import { formatSoles } from "@/modules/orders/format";
import { useExtras, usePlans } from "@/modules/catalog/queries";
import { DataTable, PageHeading, TabBar, type Column, type VisualState } from "./ui";

const PRODUCT_TABS = ["Combos", "Extras"] as const;

type ProductTab = (typeof PRODUCT_TABS)[number];

function catalogColumns(tab: ProductTab): Column[] {
  return [
    {
      key: "nombre",
      label: tab === "Combos" ? "Combo" : "Extra",
      render: (row) => <span className="font-medium text-foreground">{String(row["nombre"])}</span>,
    },
    {
      key: "codigo",
      label: "Código",
      render: (row) => <span className="table-code">{String(row["codigo"])}</span>,
    },
    { key: "descripcion", label: "Descripción" },
    {
      key: "mensual",
      label: "Precio mensual",
      render: (row) => <span className="table-amount">{formatSoles(Number(row["mensual"]))}</span>,
    },
    {
      key: "implementacion",
      label: "Implementación",
      render: (row) => (
        <span className="table-amount">{formatSoles(Number(row["implementacion"]))}</span>
      ),
    },
  ];
}

function ProductDetail({
  record,
  label,
  onClose,
}: {
  record: Record<string, unknown> | null;
  label: string;
  onClose: () => void;
}) {
  return (
    <Sheet
      open={record !== null}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <SheetContent className="detail-sheet sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{record ? String(record["nombre"]) : ""}</SheetTitle>
          <SheetDescription>{label}</SheetDescription>
        </SheetHeader>
        {record ? (
          <dl className="record-detail mt-7">
            <div>
              <dt>Código</dt>
              <dd>{String(record["codigo"])}</dd>
            </div>
            <div>
              <dt>Descripción</dt>
              <dd>{String(record["descripcion"])}</dd>
            </div>
            <div>
              <dt>Precio mensual</dt>
              <dd>{formatSoles(Number(record["mensual"]))}</dd>
            </div>
            <div>
              <dt>Implementación</dt>
              <dd>{formatSoles(Number(record["implementacion"]))}</dd>
            </div>
          </dl>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}

export function Productos() {
  const [tab, setTab] = useState<ProductTab>("Combos");
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);

  const plans = usePlans();
  const extras = useExtras();
  const active = tab === "Combos" ? plans : extras;

  const rows = (active.data ?? []).map((item) => ({
    codigo: item.code,
    nombre: item.name,
    descripcion: item.description ?? "—",
    mensual: item.monthly_price,
    implementacion: item.setup_price,
  }));

  const forbidden = active.error instanceof ApiError && active.error.status === 403;
  const state: VisualState = forbidden
    ? "normal"
    : active.isLoading
      ? "loading"
      : active.isError
        ? "error"
        : rows.length === 0
          ? "empty"
          : "normal";

  return (
    <>
      <PageHeading
        title="Productos"
        description="El catálogo de combos y servicios adicionales que ofreces."
        showDemoLabel={false}
      />
      <div className="mb-6">
        <TabBar
          items={[...PRODUCT_TABS]}
          value={tab}
          onChange={(value) => setTab(value as ProductTab)}
        />
      </div>
      <DataTable
        rows={rows}
        columns={catalogColumns(tab)}
        state={state}
        forbidden={forbidden}
        placeholder={`Buscar ${tab.toLowerCase()}...`}
        onRow={setSelected}
        errorTitle="No pudimos cargar el catálogo"
        errorMessage={
          active.error instanceof ApiError ? active.error.message : "No pudimos cargar el catálogo."
        }
        onRetry={() => {
          void active.refetch();
        }}
      />
      <ProductDetail
        label={tab === "Combos" ? "Combo" : "Extra"}
        record={selected}
        onClose={() => setSelected(null)}
      />
    </>
  );
}
