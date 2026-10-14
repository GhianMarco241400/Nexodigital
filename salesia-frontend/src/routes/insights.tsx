import { createFileRoute } from "@tanstack/react-router";
import { Insights } from "@/components/salesia/analysis";
export const Route = createFileRoute("/insights")({
  head: () => ({
    meta: [
      { title: "Insights | SalesIA" },
      { name: "description", content: "Observaciones automáticas de tus ventas en SalesIA." },
      { property: "og:title", content: "Insights | SalesIA" },
      { property: "og:description", content: "Lo que tus números dicen, en palabras claras." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Page,
});
function Page() {
  return <Insights />;
}
