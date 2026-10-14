import { createFileRoute } from "@tanstack/react-router";
import { Analytics } from "@/components/salesia/analysis";
export const Route = createFileRoute("/analytics")({
  head: () => ({
    meta: [
      { title: "Analytics | SalesIA" },
      { name: "description", content: "Analítica de ventas de SalesIA con datos reales." },
      { property: "og:title", content: "Analytics | SalesIA" },
      { property: "og:description", content: "Analiza el rendimiento comercial de tu negocio." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Page,
});
function Page() {
  return <Analytics />;
}
