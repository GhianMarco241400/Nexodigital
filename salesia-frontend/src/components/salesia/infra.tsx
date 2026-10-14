import { Server } from "lucide-react";

import type { OrderDetail } from "@/types/api";
import { formatSoles, formatUsd, serviceCodeLabel } from "@/modules/orders/format";

export function InfraSection({ detail }: { detail: OrderDetail }) {
  const components = detail.infra_components;
  const infraUsd = detail.infra_usd;
  const infraEstimate = detail.infra_estimate;
  const fxRate = detail.fx_rate;
  const regionCode = detail.region_code;
  const hasInfra = components.length > 0 || infraUsd > 0;

  return (
    <section>
      <h3>
        <Server />
        Infraestructura AWS
      </h3>
      {hasInfra ? (
        <>
          <p className="text-xs text-muted-foreground mb-4">
            Región {regionCode}
            {fxRate > 0 ? ` · Tipo de cambio S/ ${fxRate.toFixed(2)} por US$1` : ""}
          </p>
          {components.map((component) => (
            <div className="mb-3" key={component.service_code}>
              <div className="price-line">
                <span>{serviceCodeLabel(component.service_code)}</span>
                <span>{formatUsd(component.usd_monthly)}</span>
              </div>
              {component.breakdown.map((line, index) => (
                <div className="price-line text-xs text-muted-foreground" key={index}>
                  <span>{line.label}</span>
                  <span>{formatUsd(line.amount)}</span>
                </div>
              ))}
            </div>
          ))}
          <div className="price-line border-t pt-4 mt-4 text-base font-semibold">
            <span>Infraestructura mensual</span>
            <span>{formatUsd(infraUsd)}</span>
          </div>
          {infraEstimate > 0 && (
            <div className="price-line text-muted-foreground">
              <span>Equivalente en soles</span>
              <span>{formatSoles(infraEstimate)}</span>
            </div>
          )}
        </>
      ) : (
        <p className="text-sm text-muted-foreground">
          Sin infraestructura calculada para este pedido.
        </p>
      )}
    </section>
  );
}
