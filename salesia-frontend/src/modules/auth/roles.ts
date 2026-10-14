import type { Rol } from "@/data/salesia";

const API_ROLE_TO_ROL: Record<string, Rol> = {
  administrador: "Administrador",
  gerente: "Gerente",
  vendedor: "Vendedor",
  analista: "Analista",
  almacen: "Almacén",
};

export function rolFromApi(role: string): Rol {
  return API_ROLE_TO_ROL[role.toLowerCase()] ?? "Vendedor";
}

export function isAdminRole(role: string): boolean {
  return role.toLowerCase() === "administrador";
}

const ORDERS_MANAGE_ROLES = new Set(["administrador", "vendedor"]);
const ORDERS_REVIEW_ROLES = new Set(["administrador", "vendedor", "analista"]);

export function canManageOrders(role: string | null | undefined): boolean {
  return role !== null && role !== undefined && ORDERS_MANAGE_ROLES.has(role.toLowerCase());
}

export function canReviewOrders(role: string | null | undefined): boolean {
  return role !== null && role !== undefined && ORDERS_REVIEW_ROLES.has(role.toLowerCase());
}
