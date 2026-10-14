import { createFileRoute } from '@tanstack/react-router';
import { Auditoria } from '@/components/salesia/admin';
export const Route = createFileRoute('/auditoria')({
 head: () => ({meta: [{title:'Auditoría | SalesIA'},{name:'description',content:'Auditoría de SalesIA. Gestión comercial interna con datos de ejemplo.'},{property:'og:title',content:'Auditoría | SalesIA'},{property:'og:description',content:'Auditoría de SalesIA, el espacio de gestión de tu equipo.'},{property:'og:type',content:'website'},{name:'twitter:card',content:'summary_large_image'}]}),
 component: Page,
});
function Page() { return <Auditoria/>; }
