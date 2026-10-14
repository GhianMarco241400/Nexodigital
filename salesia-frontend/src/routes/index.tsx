import { createFileRoute } from "@tanstack/react-router";
import { Dashboard } from '@/components/salesia/dashboard';
export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: 'Dashboard | SalesIA' },
    { name: 'description', content: 'Resumen comercial de SalesIA: ventas, pedidos y clientes de tu equipo. Datos de ejemplo.' },
    { property: 'og:title', content: 'Dashboard | SalesIA' },
    { property: 'og:description', content: 'El espacio interno de gestión comercial de tu equipo.' },
    { property: 'og:type', content: 'website' },
    { name: 'twitter:card', content: 'summary_large_image' },
  ] }),
  component: Index,
});
function Index() {
  return <Dashboard/>;
}
