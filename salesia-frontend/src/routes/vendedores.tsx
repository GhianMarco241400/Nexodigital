import { createFileRoute } from '@tanstack/react-router';
import { Maintenance } from '@/components/salesia/operations';
export const Route = createFileRoute('/vendedores')({
 head: () => ({meta: [{title:'Vendedores | SalesIA'},{name:'description',content:'Vendedores de SalesIA. Gestión comercial interna con datos de ejemplo.'},{property:'og:title',content:'Vendedores | SalesIA'},{property:'og:description',content:'Vendedores de SalesIA, el espacio de gestión de tu equipo.'},{property:'og:type',content:'website'},{name:'twitter:card',content:'summary_large_image'}]}),
 component: Page,
});
function Page() { return <Maintenance module="Vendedores"/>; }
