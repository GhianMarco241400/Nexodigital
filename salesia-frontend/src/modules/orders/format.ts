import type { OrderCounts, OrderStatus } from "@/types/api";

const currencyFormatter = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  minimumFractionDigits: 2,
});

const dateTimeFormatter = new Intl.DateTimeFormat("es-PE", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function formatSoles(value: number): string {
  return currencyFormatter.format(Number.isFinite(value) ? value : 0);
}

const usdFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
});

export function formatUsd(value: number): string {
  return usdFormatter.format(Number.isFinite(value) ? value : 0);
}

const SERVICE_LABELS: Record<string, string> = {
  ec2: "Amazon EC2",
  rds: "Amazon RDS",
  s3: "Amazon S3",
  cloudfront: "Amazon CloudFront",
  route53: "Amazon Route 53",
  lambda: "AWS Lambda",
  dynamodb: "Amazon DynamoDB",
  sns: "Amazon SNS",
};

export function serviceCodeLabel(code: string): string {
  return SERVICE_LABELS[code] ?? code.toUpperCase();
}

export function formatDateTime(value: string | Date): string {
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return "—";
  return dateTimeFormatter.format(date);
}

const STATUS_LABELS: Record<string, string> = {
  pendiente: "Pendiente de revisión",
  en_revision: "En revisión",
  confirmado: "Confirmado",
  rechazado: "Rechazado",
};

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

const RISK_LABELS: Record<string, string> = {
  bajo: "Bajo",
  medio: "Medio",
  alto: "Alto",
};

export function riskLabel(risk: string): string {
  return RISK_LABELS[risk] ?? risk;
}

export interface OrderTab {
  label: string;
  status: OrderStatus | null;
  countKey: keyof OrderCounts;
}

export const ORDER_TABS: OrderTab[] = [
  { label: "Todos", status: null, countKey: "total" },
  { label: "Pendiente de revisión", status: "pendiente", countKey: "pendiente" },
  { label: "En revisión", status: "en_revision", countKey: "en_revision" },
  { label: "Confirmado", status: "confirmado", countKey: "confirmado" },
  { label: "Rechazado", status: "rechazado", countKey: "rechazado" },
];
