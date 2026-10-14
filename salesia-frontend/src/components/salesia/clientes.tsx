import { useState } from "react";

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useCustomers } from "@/modules/customers/queries";
import { ApiError } from "@/services/api";
import type { Customer } from "@/types/api";
import { DataTable, PageHeading, type Column, type VisualState } from "./ui";

function customerColumns(): Column[] {
  return [
    {
      key: "company_name",
      label: "Empresa",
      render: (row) => (
        <span className="font-medium text-foreground">{String(row["company_name"])}</span>
      ),
    },
    {
      key: "ruc",
      label: "RUC",
      render: (row) => <span className="table-code">{String(row["ruc"])}</span>,
    },
    { key: "contact_name", label: "Contacto" },
    { key: "email", label: "Correo electrónico" },
    { key: "region", label: "Región" },
  ];
}

function CustomerDetail({ record, onClose }: { record: Customer | null; onClose: () => void }) {
  return (
    <Sheet
      open={record !== null}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <SheetContent className="detail-sheet sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{record ? record.company_name : ""}</SheetTitle>
          <SheetDescription>Cliente</SheetDescription>
        </SheetHeader>
        {record ? (
          <dl className="record-detail mt-7">
            <div>
              <dt>RUC</dt>
              <dd>{record.ruc}</dd>
            </div>
            <div>
              <dt>Contacto</dt>
              <dd>{record.contact_name}</dd>
            </div>
            <div>
              <dt>Correo electrónico</dt>
              <dd>{record.email}</dd>
            </div>
            <div>
              <dt>Teléfono</dt>
              <dd>{record.phone ?? "—"}</dd>
            </div>
            <div>
              <dt>Región</dt>
              <dd>{record.region ?? "—"}</dd>
            </div>
          </dl>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}

export function Clientes() {
  const [selected, setSelected] = useState<Customer | null>(null);
  const customers = useCustomers();

  const rows = customers.data ?? [];
  const forbidden = customers.error instanceof ApiError && customers.error.status === 403;
  const state: VisualState = forbidden
    ? "normal"
    : customers.isLoading
      ? "loading"
      : customers.isError
        ? "error"
        : rows.length === 0
          ? "empty"
          : "normal";

  return (
    <>
      <PageHeading
        title="Clientes"
        description="Toda la información de las empresas con las que trabajas."
        showDemoLabel={false}
      />
      <DataTable
        rows={rows}
        columns={customerColumns()}
        state={state}
        forbidden={forbidden}
        placeholder="Buscar cliente, RUC o contacto..."
        onRow={(row) => setSelected(row as unknown as Customer)}
        errorTitle="No pudimos cargar los clientes"
        errorMessage={
          customers.error instanceof ApiError
            ? customers.error.message
            : "No pudimos cargar los clientes."
        }
        onRetry={() => {
          void customers.refetch();
        }}
      />
      <CustomerDetail record={selected} onClose={() => setSelected(null)} />
    </>
  );
}
