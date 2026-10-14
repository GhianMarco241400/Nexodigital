import type { Rol } from './salesia';
export const modulePaths = ['/', '/pedidos', '/ventas', '/inventario', '/clientes', '/productos', '/proveedores', '/vendedores', '/analytics', '/insights', '/reportes', '/usuarios', '/auditoria', '/seguridad'] as const;
export type ModulePath = typeof modulePaths[number];
const permissions: Record<Rol, readonly ModulePath[]> = {
 Administrador: modulePaths,
 Gerente: ['/', '/ventas', '/analytics', '/reportes'],
 Vendedor: ['/pedidos', '/ventas', '/clientes'],
 Analista: ['/analytics', '/insights', '/reportes'],
 Almacén: ['/inventario', '/productos', '/proveedores'],
};
export const visibleModules = (rol: Rol) => permissions[rol];
export const canView = (rol: Rol, path: string) => permissions[rol].some(p=>p===path);
export function bayes(a: number, ba: number, b: number): number | null {
 if (![a,ba,b].every(Number.isFinite) || a<0 || a>1 || ba<0 || ba>1 || b<=0 || b>1 || ba*a>b) return null;
 return ba*a/b;
}
