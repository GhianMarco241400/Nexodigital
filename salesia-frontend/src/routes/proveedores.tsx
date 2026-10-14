import { createFileRoute } from '@tanstack/react-router';
import { Maintenance } from '@/components/salesia/operations';
export const Route = createFileRoute('/proveedores')({
 head: () => ({meta: [{title:'Proveedores | SalesIA'},{name:'description',content:'Proveedores de SalesIA. Gestión comercial interna con datos de ejemplo.'},{property:'og:title',content:'Proveedores | SalesIA'},{property:'og:description',content:'Proveedores de SalesIA, el espacio de gestión de tu equipo.'},{property:'og:type',content:'website'},{name:'twitter:card',content:'summary_large_image'}]}),
 component: Page,
});
function Page() { return <Maintenance module="Proveedores"/>; }
