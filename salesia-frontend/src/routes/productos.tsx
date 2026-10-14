import { createFileRoute } from "@tanstack/react-router";
import { Productos } from "@/components/salesia/productos";
export const Route = createFileRoute("/productos")({
  head: () => ({
    meta: [
      { title: "Productos | SalesIA" },
      { name: "description", content: "Catálogo de combos y servicios adicionales de SalesIA." },
      { property: "og:title", content: "Productos | SalesIA" },
      {
        property: "og:description",
        content: "El catálogo de combos y extras que ofreces a tus clientes.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Page,
});
function Page() {
  return <Productos />;
}
