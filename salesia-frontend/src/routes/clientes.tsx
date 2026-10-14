import { createFileRoute } from "@tanstack/react-router";
import { Clientes } from "@/components/salesia/clientes";
export const Route = createFileRoute("/clientes")({
  head: () => ({
    meta: [
      { title: "Clientes | SalesIA" },
      { name: "description", content: "Clientes y empresas registradas en SalesIA." },
      { property: "og:title", content: "Clientes | SalesIA" },
      {
        property: "og:description",
        content: "La información de las empresas con las que trabajas.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Page,
});
function Page() {
  return <Clientes />;
}
