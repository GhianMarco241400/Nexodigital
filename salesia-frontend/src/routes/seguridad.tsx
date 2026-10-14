import { createFileRoute } from '@tanstack/react-router';
import { Seguridad } from '@/components/salesia/admin';
export const Route = createFileRoute('/seguridad')({
 head: () => ({meta: [{title:'Seguridad | SalesIA'},{name:'description',content:'Seguridad de SalesIA. Gestión comercial interna con datos de ejemplo.'},{property:'og:title',content:'Seguridad | SalesIA'},{property:'og:description',content:'Seguridad de SalesIA, el espacio de gestión de tu equipo.'},{property:'og:type',content:'website'},{name:'twitter:card',content:'summary_large_image'}]}),
 component: Page,
});
function Page() { return <Seguridad/>; }
