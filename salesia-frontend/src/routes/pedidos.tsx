import { createFileRoute } from '@tanstack/react-router';
import { Pedidos } from '@/components/salesia/operations';
export const Route = createFileRoute('/pedidos')({
 head: () => ({meta: [{title:'Pedidos | SalesIA'},{name:'description',content:'Pedidos de SalesIA. Gestión comercial interna con datos de ejemplo.'},{property:'og:title',content:'Pedidos | SalesIA'},{property:'og:description',content:'Pedidos de SalesIA, el espacio de gestión de tu equipo.'},{property:'og:type',content:'website'},{name:'twitter:card',content:'summary_large_image'}]}),
 component: Page,
});
function Page() { return <Pedidos/>; }
