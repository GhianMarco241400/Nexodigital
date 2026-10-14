import { createFileRoute } from '@tanstack/react-router';
import { Login } from '@/components/salesia/login';
export const Route = createFileRoute('/login')({
 head: () => ({meta: [{title:'Iniciar sesión | SalesIA'},{name:'description',content:'Iniciar sesión de SalesIA. Gestión comercial interna con datos de ejemplo.'},{property:'og:title',content:'Iniciar sesión | SalesIA'},{property:'og:description',content:'Iniciar sesión de SalesIA, el espacio de gestión de tu equipo.'},{property:'og:type',content:'website'},{name:'twitter:card',content:'summary_large_image'}]}),
 component: Page,
});
function Page() { return <Login/>; }
