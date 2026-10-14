export type Rol = "Administrador" | "Gerente" | "Vendedor" | "Analista" | "Almacén";
export interface Cliente {
  id: string;
  nombre: string;
  ruc: string;
  contacto: string;
  email: string;
  region: string;
  estado: string;
}
export interface Combo {
  id: string;
  nombre: string;
  categoria: string;
  descripcion: string;
  precio: number;
  cupos: number;
  region: string;
}
export interface Proveedor {
  id: string;
  nombre: string;
  servicio: string;
  contacto: string;
  email: string;
  estado: string;
}
export interface Vendedor {
  id: string;
  nombre: string;
  email: string;
  region: string;
  ventas: number;
  total: number;
  estado: string;
}
export interface Usuario {
  id: string;
  nombre: string;
  email: string;
  rol: Rol;
  estado: string;
}
export interface Alerta {
  id: string;
  titulo: string;
  descripcion: string;
  severidad: "Bajo" | "Medio" | "Alto";
  fecha: string;
  evidencia: string;
}
export interface Extra {
  id: string;
  nombre: string;
  precio: number;
  categoria: string;
}
export interface Movimiento {
  codigo: string;
  combo: string;
  region: string;
  tipo: string;
  cantidad: number;
  fecha: string;
}
export interface RegistroAuditoria {
  fecha: string;
  usuario: string;
  accion: string;
  modulo: string;
}
export const roles: Rol[] = ["Administrador", "Gerente", "Vendedor", "Analista", "Almacén"];
export const clientes: Cliente[] = [
  {
    id: "CLI-001",
    nombre: "Andes Café S.A.C.",
    ruc: "20601234561",
    contacto: "Valeria Rojas",
    email: "valeria@andescafe.example",
    region: "Lima",
    estado: "Activo",
  },
  {
    id: "CLI-002",
    nombre: "Textiles Inti S.A.C.",
    ruc: "20602345672",
    contacto: "José Huamán",
    email: "jose@inti.example",
    region: "Arequipa",
    estado: "Activo",
  },
  {
    id: "CLI-003",
    nombre: "Bodega Don Lucho",
    ruc: "20603456783",
    contacto: "Luis Quispe",
    email: "luis@donlucho.example",
    region: "Lima",
    estado: "Activo",
  },
  {
    id: "CLI-004",
    nombre: "Clínica Vida Norte",
    ruc: "20604567894",
    contacto: "Ana Torres",
    email: "ana@vidanorte.example",
    region: "Trujillo",
    estado: "Activo",
  },
  {
    id: "CLI-005",
    nombre: "Maki Sushi Perú",
    ruc: "20605678905",
    contacto: "Diego Mendoza",
    email: "diego@maki.example",
    region: "Lima",
    estado: "Activo",
  },
  {
    id: "CLI-006",
    nombre: "EcoMarket Cusco",
    ruc: "20606789016",
    contacto: "Camila Flores",
    email: "camila@ecomarket.example",
    region: "Cusco",
    estado: "Inactivo",
  },
  {
    id: "CLI-007",
    nombre: "Ferretería El Progreso",
    ruc: "20607890127",
    contacto: "Pedro Salas",
    email: "pedro@progreso.example",
    region: "Piura",
    estado: "Activo",
  },
  {
    id: "CLI-008",
    nombre: "Estudio Forma",
    ruc: "20608901238",
    contacto: "Lucía Vargas",
    email: "lucia@forma.example",
    region: "Lima",
    estado: "Activo",
  },
];
export const combos: Combo[] = [
  {
    id: "COM-001",
    nombre: "Web Emprende",
    categoria: "Página web",
    descripcion: "Web corporativa de 5 secciones, dominio y hosting.",
    precio: 1490,
    cupos: 18,
    region: "Lima",
  },
  {
    id: "COM-002",
    nombre: "Web Negocio",
    categoria: "Página web",
    descripcion: "Web de 10 secciones con catálogo y gestión de contenidos.",
    precio: 2490,
    cupos: 12,
    region: "Arequipa",
  },
  {
    id: "COM-003",
    nombre: "Tienda Online",
    categoria: "E-commerce",
    descripcion: "Tienda virtual con catálogo, carrito y pagos.",
    precio: 3990,
    cupos: 4,
    region: "Lima",
  },
  {
    id: "COM-004",
    nombre: "App Business",
    categoria: "App móvil",
    descripcion: "Aplicación Android e iOS para tu negocio.",
    precio: 5990,
    cupos: 3,
    region: "Trujillo",
  },
];
export const extras: Extra[] = [
  { id: "EXT-001", nombre: "WhatsApp integrado", precio: 150, categoria: "Integraciones" },
  { id: "EXT-002", nombre: "SEO inicial", precio: 350, categoria: "Marketing" },
  { id: "EXT-003", nombre: "Sección adicional", precio: 200, categoria: "Contenido" },
];
export const categorias = [
  {
    id: "CAT-001",
    nombre: "Página web",
    descripcion: "Sitios corporativos y catálogos",
    cantidad: 2,
  },
  { id: "CAT-002", nombre: "E-commerce", descripcion: "Tiendas y pagos digitales", cantidad: 1 },
  { id: "CAT-003", nombre: "App móvil", descripcion: "Aplicaciones Android e iOS", cantidad: 1 },
];
export const proveedores: Proveedor[] = [
  {
    id: "PRO-001",
    nombre: "Nube Andina S.A.C.",
    servicio: "Hosting y dominios",
    contacto: "Miguel Vega",
    email: "miguel@nubeandina.example",
    estado: "Activo",
  },
  {
    id: "PRO-002",
    nombre: "Pixel Sur Studio",
    servicio: "Diseño UI/UX",
    contacto: "Mariana Soto",
    email: "mariana@pixelsur.example",
    estado: "Activo",
  },
  {
    id: "PRO-003",
    nombre: "Código Norte",
    servicio: "Desarrollo móvil",
    contacto: "Javier Paredes",
    email: "javier@codigonorte.example",
    estado: "Activo",
  },
];
export const vendedores: Vendedor[] = [
  {
    id: "VDR-001",
    nombre: "Lucía Torres",
    email: "lucia@salesia.example",
    region: "Lima",
    ventas: 28,
    total: 62420,
    estado: "Activo",
  },
  {
    id: "VDR-002",
    nombre: "Carlos Mendoza",
    email: "carlos@salesia.example",
    region: "Arequipa",
    ventas: 24,
    total: 58960,
    estado: "Activo",
  },
  {
    id: "VDR-003",
    nombre: "Diego Ramos",
    email: "diego@salesia.example",
    region: "Trujillo",
    ventas: 20,
    total: 44240,
    estado: "Activo",
  },
];
export const usuarios: Usuario[] = [
  {
    id: "USR-001",
    nombre: "Marco Salazar",
    email: "marco@salesia.example",
    rol: "Administrador",
    estado: "Activo",
  },
  {
    id: "USR-002",
    nombre: "Lucía Torres",
    email: "lucia@salesia.example",
    rol: "Vendedor",
    estado: "Activo",
  },
  {
    id: "USR-003",
    nombre: "Andrea Ponce",
    email: "andrea@salesia.example",
    rol: "Gerente",
    estado: "Activo",
  },
  {
    id: "USR-004",
    nombre: "Sofía Herrera",
    email: "sofia@salesia.example",
    rol: "Analista",
    estado: "Activo",
  },
  {
    id: "USR-005",
    nombre: "Luis Medina",
    email: "luis@salesia.example",
    rol: "Almacén",
    estado: "Inactivo",
  },
];
export const alertas: Alerta[] = [
  {
    id: "ALT-001",
    titulo: "Descuento fuera de lo habitual",
    descripcion: "Un pedido registra un descuento del 35%, superior al promedio del 8%.",
    severidad: "Alto",
    fecha: "13 oct, 09:18",
    evidencia: "PED-0245 · Tienda Online · Carlos Mendoza · Descuento: S/ 1,396.50",
  },
  {
    id: "ALT-002",
    titulo: "Intentos de ingreso fallidos",
    descripcion: "Se detectaron 5 intentos fallidos en un intervalo de 3 minutos.",
    severidad: "Medio",
    fecha: "12 oct, 22:45",
    evidencia: "Usuario: luis@salesia.example · IP de ejemplo: 192.0.2.15 · 5 intentos",
  },
  {
    id: "ALT-003",
    titulo: "Venta fuera de horario",
    descripcion: "Una venta fue registrada a las 23:42, fuera del horario habitual.",
    severidad: "Bajo",
    fecha: "12 oct, 23:42",
    evidencia: "VEN-0180 · Lucía Torres · Importe: S/ 1,490.00",
  },
];
export const movimientos: Movimiento[] = [
  {
    codigo: "MOV-0081",
    combo: "Web Emprende",
    region: "Lima",
    tipo: "Asignación",
    cantidad: -1,
    fecha: "13 oct, 09:42",
  },
  {
    codigo: "MOV-0080",
    combo: "Tienda Online",
    region: "Lima",
    tipo: "Reposición",
    cantidad: 5,
    fecha: "12 oct, 16:20",
  },
  {
    codigo: "MOV-0079",
    combo: "App Business",
    region: "Trujillo",
    tipo: "Asignación",
    cantidad: -1,
    fecha: "12 oct, 14:30",
  },
];
export const auditoria: RegistroAuditoria[] = [
  {
    fecha: "13 oct 2026, 09:42",
    usuario: "Lucía Torres",
    accion: "Creó el pedido PED-0249",
    modulo: "Pedidos",
  },
  {
    fecha: "13 oct 2026, 09:18",
    usuario: "Marco Salazar",
    accion: "Inició revisión de PED-0248",
    modulo: "Pedidos",
  },
  {
    fecha: "12 oct 2026, 17:35",
    usuario: "Lucía Torres",
    accion: "Confirmó la venta VEN-0183",
    modulo: "Ventas",
  },
  {
    fecha: "12 oct 2026, 16:20",
    usuario: "Andrea Ponce",
    accion: "Consultó reporte mensual",
    modulo: "Reportes",
  },
];
export const soles = (valor: number) =>
  new Intl.NumberFormat("es-PE", {
    style: "currency",
    currency: "PEN",
    minimumFractionDigits: 2,
  }).format(valor);
