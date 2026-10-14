import { describe, it, expect } from 'vitest';
import { visibleModules, modulePaths, bayes } from '../data/access';
describe('SalesIA demo roles',()=>{
 it('Administrador sees every module',()=>expect(visibleModules('Administrador')).toEqual(modulePaths));
 it('Gerente sees Dashboard, Ventas, Analytics, Reportes only',()=>expect(visibleModules('Gerente')).toEqual(['/','/ventas','/analytics','/reportes']));
 it('Vendedor sees Pedidos, Ventas, Clientes only',()=>expect(visibleModules('Vendedor')).toEqual(['/pedidos','/ventas','/clientes']));
 it('Almacén sees Inventario, Productos, Proveedores only',()=>expect(visibleModules('Almacén')).toEqual(['/inventario','/productos','/proveedores']));
 it('Analista sees Analytics, Insights, Reportes only',()=>expect(visibleModules('Analista')).toEqual(['/analytics','/insights','/reportes']));
});
describe('Bayes preview',()=>{
 it('uses P(B|A)·P(A) / P(B)',()=>expect(bayes(0.4,0.75,0.5)).toBeCloseTo(0.6));
 it('rejects a zero denominator',()=>expect(bayes(0.4,0.75,0)).toBeNull());
 it('rejects inconsistent probabilities',()=>expect(bayes(0.8,0.9,0.2)).toBeNull());
});
