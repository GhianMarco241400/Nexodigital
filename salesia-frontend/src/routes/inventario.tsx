import { createFileRoute } from '@tanstack/react-router';
import { Inventario } from '@/components/salesia/operations';
export const Route = createFileRoute('/inventario')({
 head: () => ({meta: [{title:'Inventario | SalesIA'},{name:'description',content:'Inventario de SalesIA. Gestión comercial interna con datos de ejemplo.'},{property:'og:title',content:'Inventario | SalesIA'},{property:'og:description',content:'Inventario de SalesIA, el espacio de gestión de tu equipo.'},{property:'og:type',content:'website'},{name:'twitter:card',content:'summary_large_image'}]}),
 component: Page,
});
function Page() { return <Inventario/>; }
