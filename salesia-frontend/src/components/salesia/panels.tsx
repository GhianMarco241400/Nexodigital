import { useEffect, useState } from "react";
import {
  Building2,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Check,
  X,
  FileText,
  ShieldCheck,
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { clientes, combos, roles, soles } from "@/data/salesia";
import { Field, Status, StateMenu, TabBar, type VisualState } from "./ui";
import { useConfirmOrder, useOrder, useRejectOrder, useRunReview } from "@/modules/orders/queries";
import { formatDateTime, formatSoles, riskLabel, statusLabel } from "@/modules/orders/format";
import { canManageOrders, canReviewOrders, isAdminRole } from "@/modules/auth/roles";
import { useAuth } from "@/modules/auth/AuthProvider";
import { useReviewConfig, useTestReview, useUpdateReviewConfig } from "@/modules/settings/queries";
import { ApiError } from "@/services/api";
import type { ReviewProvider } from "@/types/api";
import { InfraSection } from "./infra";

const recommendationLabel: Record<string, string> = {
  aprobar: "Aprobar",
  revisar: "Revisar",
  rechazar: "Rechazar",
};

const providerLabel: Record<ReviewProvider, string> = {
  gemini: "Google Gemini",
  groq: "Groq",
  openrouter: "OpenRouter",
  ollama: "Ollama (local)",
  openai: "OpenAI",
};
const providerOrder: ReviewProvider[] = ["gemini", "groq", "openrouter", "ollama", "openai"];
export function PedidoPanel({ code, onClose }: { code: string | null; onClose: () => void }) {
  const [tab, setTab] = useState("Detalle");
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");
  const detailQuery = useOrder(code);
  const detail = detailQuery.data ?? null;
  const { user } = useAuth();
  const canManage = canManageOrders(user?.role);
  const canReview = canReviewOrders(user?.role);
  const isAdmin = isAdminRole(user?.role ?? "");
  const reviewConfig = useReviewConfig(isAdmin);
  const updateReviewConfig = useUpdateReviewConfig();
  const testReview = useTestReview();
  const [modelDraft, setModelDraft] = useState("");
  useEffect(() => {
    if (reviewConfig.data?.model) setModelDraft(reviewConfig.data.model);
  }, [reviewConfig.data?.model]);
  const orderCode = detail?.code ?? "";
  const reviewMutation = useRunReview(orderCode);
  const confirmMutation = useConfirmOrder(orderCode);
  const rejectMutation = useRejectOrder(orderCode);
  const error = detailQuery.error;
  const forbidden = error instanceof ApiError && error.status === 403;
  const notFound = error instanceof ApiError && error.status === 404;
  const isOpen = detail?.status === "pendiente" || detail?.status === "en_revision";
  const flags = detail?.review?.flags ?? [];
  const mutationError = (e: unknown, fallback: string) =>
    toast.error(e instanceof ApiError ? e.message : fallback);
  const close = () => {
    onClose();
    setTab("Detalle");
    setRejecting(false);
    setReason("");
  };
  return (
    <Sheet
      open={code !== null}
      onOpenChange={(o) => {
        if (!o) close();
      }}
    >
      <SheetContent className="detail-sheet w-full sm:max-w-xl overflow-y-auto">
        <SheetHeader>
          <div className="flex items-center gap-2 text-primary text-xs font-medium mb-2">
            <ClipboardIcon />
            PEDIDO
          </div>
          <SheetTitle>{code}</SheetTitle>
          <SheetDescription>
            {detail
              ? `${formatDateTime(detail.created_at)} · ${detail.assigned_to?.full_name ?? "Sin asignar"}`
              : ""}
          </SheetDescription>
        </SheetHeader>
        {detailQuery.isLoading ? (
          <div aria-label="Cargando pedido" className="space-y-6 py-8">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-14 animate-pulse rounded bg-muted" />
            ))}
          </div>
        ) : forbidden ? (
          <div className="empty-state">
            <ShieldCheck />
            <h3>Sin acceso</h3>
            <p>No tienes permiso para ver este pedido.</p>
          </div>
        ) : notFound ? (
          <div className="empty-state">
            <FileText />
            <h3>Pedido no encontrado</h3>
            <p>El pedido {code} no existe o fue eliminado.</p>
          </div>
        ) : error ? (
          <div className="empty-state">
            <AlertTriangle className="text-danger" />
            <h3>No pudimos cargar el pedido</h3>
            <p>{error instanceof ApiError ? error.message : "Intenta de nuevo."}</p>
            <Button
              variant="outline"
              onClick={() => {
                void detailQuery.refetch();
              }}
            >
              Reintentar
            </Button>
          </div>
        ) : detail ? (
          <>
            <div className="flex items-center gap-3 my-5">
              <Status>{statusLabel(detail.status)}</Status>
              <Status>{riskLabel(detail.risk)}</Status>
            </div>
            <TabBar items={["Detalle", "Historial"]} value={tab} onChange={setTab} />
            {tab === "Historial" ? (
              <div className="timeline">
                {detail.events.length ? (
                  detail.events.map((e, i) => (
                    <div className="timeline-item" key={i}>
                      <span>
                        <Clock />
                      </span>
                      <div>
                        <strong>{e.event_type}</strong>
                        <p>
                          {e.description ?? "—"}
                          {e.actor_name ? ` · ${e.actor_name}` : ""}
                          <span className="block text-xs text-muted-foreground mt-1">
                            {formatDateTime(e.created_at)}
                          </span>
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground mt-4">
                    Aún no hay eventos registrados.
                  </p>
                )}
              </div>
            ) : (
              <div className="panel-sections">
                <section>
                  <h3>
                    <Building2 />
                    Datos de la empresa
                  </h3>
                  <dl>
                    <div>
                      <dt>Razón social</dt>
                      <dd>{detail.customer.company_name}</dd>
                    </div>
                    <div>
                      <dt>RUC</dt>
                      <dd>{detail.customer.ruc}</dd>
                    </div>
                    <div>
                      <dt>Contacto</dt>
                      <dd>{detail.customer.contact_name}</dd>
                    </div>
                    <div>
                      <dt>Correo</dt>
                      <dd>{detail.customer.email}</dd>
                    </div>
                    <div>
                      <dt>Región</dt>
                      <dd>{detail.customer.region ?? "—"}</dd>
                    </div>
                  </dl>
                </section>
                <section>
                  <h3>Plan y extras</h3>
                  <div className="price-line">
                    <strong>{detail.plan.name}</strong>
                    <span>{formatSoles(detail.monthly_total)}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mb-4">
                    {detail.plan.description ?? "—"}
                  </p>
                  {detail.items.map((item, i) => (
                    <div className="price-line text-muted-foreground" key={i}>
                      <span>
                        {item.extra_name}
                        {item.quantity > 1 ? ` ×${item.quantity}` : ""}
                      </span>
                      <span>{formatSoles(item.monthly_price + item.setup_price)}</span>
                    </div>
                  ))}
                  {detail.setup_total > 0 && (
                    <div className="price-line text-muted-foreground">
                      <span>Instalación</span>
                      <span>{formatSoles(detail.setup_total)}</span>
                    </div>
                  )}
                  <div className="price-line border-t pt-4 mt-4 text-base font-semibold">
                    <span>Total del pedido</span>
                    <span>{formatSoles(detail.monthly_total + detail.setup_total)}</span>
                  </div>
                </section>
                <InfraSection detail={detail} />
                <section className="ai-review">
                  <div className="flex items-center justify-between gap-3">
                    <h3>
                      <Sparkles />
                      Revisión con IA
                    </h3>
                    {isOpen && canReview && (
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={reviewMutation.isPending}
                        onClick={() =>
                          reviewMutation.mutate(undefined, {
                            onSuccess: () => toast.success("Revisión de IA completada"),
                            onError: (e) => mutationError(e, "No se pudo ejecutar la revisión"),
                          })
                        }
                      >
                        <Sparkles />
                        {detail.review ? "Volver a revisar" : "Ejecutar revisión"}
                      </Button>
                    )}
                  </div>
                  {detail.review ? (
                    <>
                      <p>{detail.review.summary}</p>
                      <div
                        className={`ai-evidence ${detail.review.risk.toLowerCase() === "alto" ? "evidence-warning" : "evidence-success"}`}
                      >
                        {detail.review.risk.toLowerCase() === "alto" ? (
                          <AlertTriangle />
                        ) : (
                          <CheckCircle2 />
                        )}
                        <span>Nivel de riesgo: {riskLabel(detail.review.risk)}</span>
                      </div>
                      {detail.review.recommendation && (
                        <p className="text-sm mt-3">
                          Recomendación:{" "}
                          <strong>
                            {recommendationLabel[detail.review.recommendation] ??
                              detail.review.recommendation}
                          </strong>
                          {detail.review.confidence !== null
                            ? ` · Confianza ${Math.round(detail.review.confidence * 100)}%`
                            : ""}
                          {detail.review.model && detail.review.model !== "heuristic"
                            ? ` · ${detail.review.model}`
                            : ""}
                        </p>
                      )}
                      {flags.length > 0 && (
                        <ul className="mt-3 space-y-1 text-sm text-muted-foreground">
                          {flags.map((flag) => (
                            <li key={flag.code}>
                              <strong>{riskLabel(flag.severity)}:</strong> {flag.message}
                            </li>
                          ))}
                        </ul>
                      )}
                      <span className="block text-xs text-muted-foreground mt-3">
                        {formatDateTime(detail.review.created_at)}
                      </span>
                    </>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Aún no hay una revisión de IA para este pedido.
                    </p>
                  )}
                  {isAdmin && (
                    <div className="mt-4 space-y-3 border-t pt-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-medium">Usar IA en la revisión</p>
                          <p className="text-xs text-muted-foreground">
                            {reviewConfig.data
                              ? `${reviewConfig.data.ai_enabled ? "Activada" : "Desactivada (solo reglas)"} · ${providerLabel[reviewConfig.data.provider]} · ${reviewConfig.data.model}`
                              : "Cargando…"}
                          </p>
                        </div>
                        <Switch
                          checked={reviewConfig.data?.ai_enabled ?? false}
                          disabled={reviewConfig.isLoading || updateReviewConfig.isPending}
                          onCheckedChange={(value) =>
                            updateReviewConfig.mutate(
                              { mode: value ? "hybrid" : "heuristic" },
                              {
                                onSuccess: (config) =>
                                  toast.success(
                                    config.ai_enabled
                                      ? "IA activada"
                                      : "IA desactivada (solo reglas)",
                                  ),
                                onError: (e) =>
                                  toast.error(
                                    e instanceof ApiError
                                      ? e.message
                                      : "No se pudo cambiar el modo",
                                  ),
                              },
                            )
                          }
                        />
                      </div>
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm">Proveedor</p>
                        <Select
                          value={reviewConfig.data?.provider ?? ""}
                          disabled={reviewConfig.isLoading || updateReviewConfig.isPending}
                          onValueChange={(value) =>
                            updateReviewConfig.mutate(
                              { provider: value as ReviewProvider },
                              {
                                onSuccess: (config) => {
                                  setModelDraft(config.model);
                                  toast.success(`Proveedor: ${providerLabel[config.provider]}`);
                                },
                                onError: (e) =>
                                  toast.error(
                                    e instanceof ApiError
                                      ? e.message
                                      : "No se pudo cambiar el proveedor",
                                  ),
                              },
                            )
                          }
                        >
                          <SelectTrigger className="w-48">
                            <SelectValue placeholder="Proveedor" />
                          </SelectTrigger>
                          <SelectContent>
                            {providerOrder.map((name) => (
                              <SelectItem key={name} value={name}>
                                {providerLabel[name]}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm">Modelo</p>
                        <Input
                          className="w-48"
                          value={modelDraft}
                          disabled={reviewConfig.isLoading || updateReviewConfig.isPending}
                          placeholder={reviewConfig.data?.model ?? "Modelo"}
                          onChange={(e) => setModelDraft(e.target.value)}
                          onBlur={() => {
                            const next = modelDraft.trim();
                            if (
                              next &&
                              next !== reviewConfig.data?.model &&
                              !updateReviewConfig.isPending
                            ) {
                              updateReviewConfig.mutate({ model: next });
                            }
                          }}
                        />
                      </div>
                      <div className="flex items-center gap-3">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={testReview.isPending}
                          onClick={() =>
                            testReview.mutate(undefined, {
                              onError: (e) =>
                                toast.error(e instanceof ApiError ? e.message : "Falló la prueba"),
                            })
                          }
                        >
                          <Sparkles />
                          Probar conexión
                        </Button>
                        {testReview.data && (
                          <span className="text-xs text-muted-foreground">
                            {testReview.data.ok
                              ? `OK · ${testReview.data.latency_ms} ms`
                              : `Fallo: ${testReview.data.error}`}
                          </span>
                        )}
                      </div>
                      {reviewConfig.data && !reviewConfig.data.has_api_key && (
                        <p className="text-xs text-muted-foreground">
                          {reviewConfig.data.provider === "ollama"
                            ? "Ollama (local) no requiere clave."
                            : `Falta la clave de ${providerLabel[reviewConfig.data.provider]} en el servidor (.env).`}
                        </p>
                      )}
                    </div>
                  )}
                </section>
                {isOpen ? (
                  <div className="space-y-3">
                    <div className="flex gap-3">
                      <Button
                        className="flex-1"
                        disabled={!canManage || confirmMutation.isPending}
                        onClick={() =>
                          confirmMutation.mutate(undefined, {
                            onSuccess: () => toast.success("Venta confirmada"),
                            onError: (e) => mutationError(e, "No se pudo confirmar la venta"),
                          })
                        }
                      >
                        <Check />
                        Confirmar venta
                      </Button>
                      <Button
                        variant="outline"
                        disabled={!canManage}
                        onClick={() => setRejecting((v) => !v)}
                      >
                        <X />
                        Rechazar
                      </Button>
                    </div>
                    {rejecting && (
                      <div className="space-y-2">
                        <Input
                          value={reason}
                          maxLength={300}
                          placeholder="Motivo del rechazo"
                          onChange={(e) => setReason(e.target.value)}
                        />
                        <div className="flex gap-3">
                          <Button
                            variant="outline"
                            className="flex-1"
                            onClick={() => {
                              setRejecting(false);
                              setReason("");
                            }}
                          >
                            Cancelar
                          </Button>
                          <Button
                            className="flex-1"
                            disabled={reason.trim().length < 3 || rejectMutation.isPending}
                            onClick={() =>
                              rejectMutation.mutate(reason.trim(), {
                                onSuccess: () => {
                                  toast.success("Pedido rechazado");
                                  setRejecting(false);
                                  setReason("");
                                },
                                onError: (e) => mutationError(e, "No se pudo rechazar el pedido"),
                              })
                            }
                          >
                            Confirmar rechazo
                          </Button>
                        </div>
                      </div>
                    )}
                    {!canManage && (
                      <p className="text-xs text-muted-foreground">
                        Solo un vendedor o administrador puede confirmar o rechazar.
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Este pedido está {statusLabel(detail.status).toLowerCase()}
                    {detail.reviewed_at ? ` · ${formatDateTime(detail.reviewed_at)}` : ""}.
                  </p>
                )}
              </div>
            )}
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
function ClipboardIcon() {
  return <FileText className="size-4" />;
}
const fields: Record<string, string[]> = {
  Inventario: ["Combo", "Región", "Tipo de movimiento", "Cupos disponibles", "Observaciones"],
  Ventas: ["Cliente", "Combo", "Vendedor", "Método de pago", "Total (S/)"],
  Clientes: ["Razón social", "RUC", "Contacto", "Correo electrónico", "Región"],
  Productos: ["Nombre del combo", "Categoría", "Precio (S/)", "Cupos disponibles", "Descripción"],
  Extras: ["Nombre del extra", "Categoría", "Precio (S/)"],
  Categorías: ["Nombre", "Descripción"],
  Proveedores: ["Razón social", "Servicio", "Contacto", "Correo electrónico"],
  Vendedores: ["Nombre completo", "Correo electrónico", "Región"],
  Usuarios: ["Nombre completo", "Correo electrónico", "Rol"],
  Pedidos: ["Cliente", "Combo", "Vendedor", "Observaciones"],
};
export function FormPanel({
  module,
  open,
  onClose,
}: {
  module: string;
  open: boolean;
  onClose: () => void;
}) {
  const [state, setState] = useState<VisualState>("normal");
  const [errors, setErrors] = useState(false);
  return (
    <Sheet
      open={open}
      onOpenChange={(o) => {
        if (!o) {
          onClose();
          setState("normal");
          setErrors(false);
        }
      }}
    >
      <SheetContent className="detail-sheet w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Nuevo registro · {module}</SheetTitle>
          <SheetDescription>Datos de ejemplo · Los cambios no se guardan.</SheetDescription>
        </SheetHeader>
        <div className="flex justify-end mt-3">
          <StateMenu onState={setState} />
        </div>
        {state === "loading" ? (
          <div aria-label="Cargando formulario" className="space-y-7 py-6">
            {[1, 2, 3, 4].map((i) => (
              <div className="animate-pulse h-14 bg-muted rounded" key={i} />
            ))}
          </div>
        ) : state === "error" ? (
          <div className="empty-state">
            <AlertTriangle />
            <h3>El formulario no está disponible</h3>
            <p>Error de ejemplo al cargar las opciones.</p>
            <Button variant="outline" onClick={() => setState("normal")}>
              Reintentar
            </Button>
          </div>
        ) : state === "empty" ? (
          <div className="empty-state">
            <FileText />
            <h3>No hay opciones disponibles</h3>
            <p>Agrega registros de referencia para continuar.</p>
            <Button variant="outline" onClick={() => setState("normal")}>
              Volver al formulario
            </Button>
          </div>
        ) : (
          <form
            className="space-y-5 mt-6"
            onSubmit={(e) => {
              e.preventDefault();
              toast.success("Formulario validado correctamente", {
                description: "Vista de ejemplo. No se guardaron cambios.",
              });
              onClose();
            }}
          >
            {(fields[module] ?? ["Nombre", "Descripción"]).map((label) => (
              <Field key={label} label={label}>
                {label === "Rol" ? (
                  <select required defaultValue="Vendedor">
                    {roles.map((r) => (
                      <option key={r}>{r}</option>
                    ))}
                  </select>
                ) : label === "Combo" ? (
                  <select required>
                    <option value="">Seleccionar combo</option>
                    {combos.map((c) => (
                      <option key={c.id}>{c.nombre}</option>
                    ))}
                  </select>
                ) : label === "Cliente" ? (
                  <select required>
                    <option value="">Seleccionar cliente</option>
                    {clientes.map((c) => (
                      <option key={c.id}>{c.nombre}</option>
                    ))}
                  </select>
                ) : (
                  <Input
                    required={label !== "Observaciones" && label !== "Descripción"}
                    type={
                      label.includes("Correo")
                        ? "email"
                        : label.includes("Precio") || label.includes("Cupos")
                          ? "number"
                          : "text"
                    }
                    min={label.includes("Precio") || label.includes("Cupos") ? 0 : undefined}
                    placeholder={
                      label === "Región"
                        ? "Lima"
                        : label === "RUC"
                          ? "20601234561"
                          : label.includes("Correo")
                            ? "nombre@empresa.example"
                            : label
                    }
                    onInvalid={() => setErrors(true)}
                  />
                )}
              </Field>
            ))}
            {errors && (
              <p className="text-sm text-danger">
                Completa los campos obligatorios con datos válidos.
              </p>
            )}
            <div className="flex justify-end gap-2 pt-4 border-t">
              <Button variant="outline" type="button" onClick={onClose}>
                Cancelar
              </Button>
              <Button type="submit">Guardar</Button>
            </div>
          </form>
        )}
      </SheetContent>
    </Sheet>
  );
}
export function RecordPanel({
  record,
  title,
  onClose,
}: {
  record: Record<string, unknown> | null;
  title: string;
  onClose: () => void;
}) {
  return (
    <Sheet
      open={!!record}
      onOpenChange={(o) => {
        if (!o) onClose();
      }}
    >
      <SheetContent className="detail-sheet sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>
            {String(record?.["nombre"] ?? record?.["cliente"] ?? record?.["numero"] ?? title)}
          </SheetTitle>
          <SheetDescription>{title} · Datos de ejemplo</SheetDescription>
        </SheetHeader>
        <dl className="record-detail mt-7">
          {Object.entries(record ?? {}).map(([key, value]) => (
            <div key={key}>
              <dt>{key.replace(/([A-Z])/g, " $1")}</dt>
              <dd>{key === "precio" || key === "total" ? soles(Number(value)) : String(value)}</dd>
            </div>
          ))}
        </dl>
      </SheetContent>
    </Sheet>
  );
}
