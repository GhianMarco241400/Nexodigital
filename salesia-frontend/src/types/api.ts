export interface ApiUser {
  id: number;
  full_name: string;
  email: string;
  role: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: ApiUser;
}

export type OrderStatus = "pendiente" | "en_revision" | "confirmado" | "rechazado";

export interface OrderListItem {
  code: string;
  company_name: string;
  plan_name: string;
  monthly_total: number;
  setup_total: number;
  status: string;
  risk: string;
  created_at: string;
}

export interface OrderCounts {
  total: number;
  pendiente: number;
  en_revision: number;
  confirmado: number;
  rechazado: number;
  ingresos_confirmado: number;
}

export interface OrderListResponse {
  items: OrderListItem[];
  total: number;
  page: number;
  page_size: number;
  counts: OrderCounts;
}

export interface CustomerInfo {
  company_name: string;
  ruc: string;
  contact_name: string;
  email: string;
  phone: string | null;
  region: string | null;
}

export interface PlanInfo {
  code: string;
  name: string;
  description: string | null;
  monthly_price: number;
  setup_price: number;
}

export interface ExtraInfo {
  code: string;
  name: string;
  description: string | null;
  monthly_price: number;
  setup_price: number;
}

export interface Customer {
  company_name: string;
  ruc: string;
  contact_name: string;
  email: string;
  phone: string | null;
  region: string | null;
}

export interface OrderItemInfo {
  extra_name: string;
  monthly_price: number;
  setup_price: number;
  quantity: number;
}

export interface ComponentLine {
  label: string;
  amount: number;
}

export interface InfraComponentInfo {
  service_code: string;
  usd_monthly: number;
  breakdown: ComponentLine[];
}

export interface StaffRef {
  id: number;
  full_name: string;
}

export interface ReviewFlag {
  code: string;
  severity: string;
  message: string;
}

export interface ReviewInfo {
  summary: string;
  flags: ReviewFlag[] | null;
  risk: string;
  recommendation: string | null;
  confidence: number | null;
  model: string | null;
  created_at: string;
}

export type ReviewMode = "heuristic" | "llm" | "hybrid";

export type ReviewProvider = "gemini" | "groq" | "openrouter" | "ollama" | "openai";

export interface ReviewConfig {
  mode: ReviewMode;
  provider: ReviewProvider;
  model: string;
  ai_enabled: boolean;
  has_api_key: boolean;
  updated_by: string | null;
  updated_at: string | null;
}

export interface ReviewTestResult {
  ok: boolean;
  provider: ReviewProvider | null;
  model: string | null;
  latency_ms: number | null;
  error: string | null;
}

export interface OrderEventInfo {
  event_type: string;
  description: string | null;
  actor_name: string | null;
  created_at: string;
}

export interface OrderDetail {
  code: string;
  status: string;
  risk: string;
  region_code: string;
  created_at: string;
  monthly_total: number;
  setup_total: number;
  infra_usd: number;
  infra_estimate: number;
  fx_rate: number;
  customer: CustomerInfo;
  plan: PlanInfo;
  items: OrderItemInfo[];
  infra_components: InfraComponentInfo[];
  assigned_to: StaffRef | null;
  reviewed_by: StaffRef | null;
  reviewed_at: string | null;
  reject_reason: string | null;
  review: ReviewInfo | null;
  events: OrderEventInfo[];
}
