import { createFileRoute } from '@tanstack/react-router';
import { Ventas } from '@/components/salesia/operations';
export const Route = createFileRoute('/ventas')({
 head: () => ({meta: [{title:'Ventas | SalesIA'},{name:'description',content:'Ventas de SalesIA. Gestión comercial interna con datos de ejemplo.'},{property:'og:title',content:'Ventas | SalesIA'},{property:'og:description',content:'Ventas de SalesIA, el espacio de gestión de tu equipo.'},{property:'og:type',content:'website'},{name:'twitter:card',content:'summary_large_image'}]}),
 component: Page,
});
function Page() { return <Ventas/>; }
