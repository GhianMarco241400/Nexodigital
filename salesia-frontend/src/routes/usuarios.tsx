import { createFileRoute } from '@tanstack/react-router';
import { Maintenance } from '@/components/salesia/operations';
export const Route = createFileRoute('/usuarios')({
 head: () => ({meta: [{title:'Usuarios y roles | SalesIA'},{name:'description',content:'Usuarios y roles de SalesIA. Gestión comercial interna con datos de ejemplo.'},{property:'og:title',content:'Usuarios y roles | SalesIA'},{property:'og:description',content:'Usuarios y roles de SalesIA, el espacio de gestión de tu equipo.'},{property:'og:type',content:'website'},{name:'twitter:card',content:'summary_large_image'}]}),
 component: Page,
});
function Page() { return <Maintenance module="Usuarios y roles"/>; }
