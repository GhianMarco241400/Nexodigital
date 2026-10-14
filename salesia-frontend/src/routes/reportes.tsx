import { createFileRoute } from "@tanstack/react-router";
import { Reportes } from "@/components/salesia/analysis";
export const Route = createFileRoute("/reportes")({
  head: () => ({
    meta: [
      { title: "Reportes | SalesIA" },
      { name: "description", content: "Reportes de ventas, productos y clientes de SalesIA." },
      { property: "og:title", content: "Reportes | SalesIA" },
      { property: "og:description", content: "La información de tu negocio lista para compartir." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Page,
});
function Page() {
  return <Reportes />;
}
