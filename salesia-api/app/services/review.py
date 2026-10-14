from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from psycopg.types.json import Jsonb
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ai import provider as ai_provider
from app.services.audit import write_audit
from app.services.review_config import (
    get_review_mode,
    get_review_model,
    get_review_provider,
)

_DISPOSABLE_DOMAINS = frozenset(
    {
        "mailinator.com",
        "yopmail.com",
        "guerrillamail.com",
        "sharklasers.com",
        "tempmail.com",
        "10minutemail.com",
        "trashmail.com",
        "getnada.com",
    }
)

_SEVERITY_WEIGHT = {"bajo": 1, "medio": 2, "alto": 3}
_OPEN_STATUSES = ("pendiente", "en_revision")


class ReviewNotFoundError(Exception):
    """El pedido indicado no existe."""


class ReviewStateError(Exception):
    """El pedido no admite la transición solicitada."""


@dataclass(frozen=True)
class Flag:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class ReviewFeatures:
    plan_name: str
    monthly_total: float
    setup_total: float
    catalog_monthly: float
    catalog_setup: float
    infra_estimate: float
    infra_usd: float
    infra_ratio: float
    ruc_valid: bool
    same_ruc_recent: int
    disposable_email: bool
    phone_present: bool
    region_present: bool
    customer_orders: int
    customer_confirmed: int


@dataclass(frozen=True)
class Verdict:
    risk: str
    summary: str
    flags: list[Flag] = field(default_factory=list)
    recommendation: str = "revisar"
    confidence: float = 0.5
    model: str = "heuristic"


def ruc_checksum_valid(ruc: str) -> bool:
    if len(ruc) != 11 or not ruc.isdigit():
        return False
    factors = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    total = sum(int(digit) * factor for digit, factor in zip(ruc[:10], factors))
    remainder = total % 11
    check = 11 - remainder
    if check == 10:
        check = 0
    elif check == 11:
        check = 1
    return check == int(ruc[10])


def _max_risk(flags: list[Flag]) -> str:
    if not flags:
        return "bajo"
    return max((flag.severity for flag in flags), key=lambda s: _SEVERITY_WEIGHT.get(s, 1))


def _recommendation(risk: str) -> str:
    if risk == "alto":
        return "rechazar"
    if risk == "medio":
        return "revisar"
    return "aprobar"


def _confidence(flags: list[Flag]) -> float:
    score = 0.95
    for flag in flags:
        if flag.severity == "alto":
            score -= 0.2
        elif flag.severity == "medio":
            score -= 0.1
        else:
            score -= 0.03
    return round(min(max(score, 0.3), 0.98), 2)


def _summary(risk: str, flags: list[Flag]) -> str:
    if not flags:
        return (
            "Sin señales de riesgo: el pedido es consistente con el catálogo, "
            "la infraestructura y los datos del cliente."
        )
    messages = "; ".join(flag.message for flag in flags)
    return f"Riesgo {risk} ({len(flags)} señales). {messages}"[:1000]


def assess(features: ReviewFeatures) -> Verdict:
    """Calcula el veredicto a partir de las señales. Puro, sin red ni BD."""
    flags: list[Flag] = []

    if features.monthly_total <= 0:
        flags.append(Flag("sin_precio", "alto", "El pedido no tiene precio mensual."))
    elif (
        abs(features.monthly_total - features.catalog_monthly) > 0.01
        or abs(features.setup_total - features.catalog_setup) > 0.01
    ):
        flags.append(
            Flag(
                "precio_inconsistente",
                "alto",
                "El total del pedido no coincide con el catálogo vigente.",
            )
        )

    if features.infra_ratio >= 0.6:
        flags.append(
            Flag(
                "margen_critico",
                "alto",
                f"La infraestructura consume {features.infra_ratio:.0%} del precio mensual.",
            )
        )
    elif features.infra_ratio >= 0.35:
        flags.append(
            Flag(
                "margen_ajustado",
                "medio",
                f"La infraestructura consume {features.infra_ratio:.0%} del precio mensual.",
            )
        )

    if not features.ruc_valid:
        flags.append(
            Flag(
                "ruc_invalido",
                "alto",
                "El RUC no supera la validación de dígito verificador.",
            )
        )

    if features.same_ruc_recent >= 5:
        flags.append(
            Flag(
                "duplicados_altos",
                "alto",
                f"{features.same_ruc_recent} pedidos del mismo RUC en los últimos 7 días.",
            )
        )
    elif features.same_ruc_recent >= 3:
        flags.append(
            Flag(
                "duplicados",
                "medio",
                f"{features.same_ruc_recent} pedidos del mismo RUC en los últimos 7 días.",
            )
        )
    elif features.same_ruc_recent >= 1:
        flags.append(
            Flag(
                "duplicado_reciente",
                "bajo",
                "Ya existe un pedido reciente del mismo RUC.",
            )
        )

    if features.disposable_email:
        flags.append(
            Flag("email_desechable", "medio", "El correo usa un dominio desechable.")
        )

    if not features.phone_present:
        flags.append(Flag("sin_telefono", "bajo", "El cliente no registró teléfono."))

    if not features.region_present:
        flags.append(Flag("sin_region", "bajo", "El cliente no indicó su región."))

    if features.customer_orders <= 1:
        flags.append(Flag("cliente_nuevo", "bajo", "Es el primer pedido del cliente."))
    elif features.customer_confirmed == 0:
        flags.append(
            Flag(
                "cliente_sin_confirmaciones",
                "medio",
                "El cliente no tiene ventas confirmadas previas.",
            )
        )

    risk = _max_risk(flags)
    return Verdict(
        risk=risk,
        summary=_summary(risk, flags),
        flags=flags,
        recommendation=_recommendation(risk),
        confidence=_confidence(flags),
        model="heuristic",
    )


def _load_features(db: Session, code: str) -> tuple[int, ReviewFeatures] | None:
    row = (
        db.execute(
            text(
                "select o.id, o.monthly_total, o.setup_total, o.infra_estimate, "
                "o.infra_usd, c.id as customer_id, c.ruc, c.email, c.phone, "
                "c.region, p.name as plan_name, "
                "p.monthly_price as plan_monthly, p.setup_price as plan_setup "
                "from orders o "
                "join customers c on c.id = o.customer_id "
                "join plans p on p.id = o.plan_id "
                "where o.code = :code"
            ),
            {"code": code},
        )
        .mappings()
        .first()
    )
    if row is None:
        return None

    order_id = row["id"]

    extras = (
        db.execute(
            text(
                "select coalesce(sum(monthly_price), 0) as monthly, "
                "coalesce(sum(setup_price), 0) as setup "
                "from order_items where order_id = :order_id"
            ),
            {"order_id": order_id},
        )
        .mappings()
        .one()
    )

    recent = db.execute(
        text(
            "select count(*) from orders "
            "where customer_id = :customer_id and id <> :order_id "
            "and created_at >= now() - interval '7 days'"
        ),
        {"customer_id": row["customer_id"], "order_id": order_id},
    ).scalar_one()

    history = (
        db.execute(
            text(
                "select count(*) as total, "
                "count(*) filter (where status = 'confirmado') as confirmed "
                "from orders where customer_id = :customer_id"
            ),
            {"customer_id": row["customer_id"]},
        )
        .mappings()
        .one()
    )

    monthly_total = float(row["monthly_total"])
    infra_estimate = float(row["infra_estimate"] or 0)
    email = (row["email"] or "").strip().lower()
    domain = email.rsplit("@", 1)[-1] if "@" in email else ""

    catalog_monthly = float(row["plan_monthly"]) + float(extras["monthly"])
    catalog_setup = float(row["plan_setup"]) + float(extras["setup"])

    features = ReviewFeatures(
        plan_name=row["plan_name"],
        monthly_total=monthly_total,
        setup_total=float(row["setup_total"]),
        catalog_monthly=catalog_monthly,
        catalog_setup=catalog_setup,
        infra_estimate=infra_estimate,
        infra_usd=float(row["infra_usd"] or 0),
        infra_ratio=(infra_estimate / monthly_total) if monthly_total > 0 else 0.0,
        ruc_valid=ruc_checksum_valid((row["ruc"] or "").strip()),
        same_ruc_recent=int(recent),
        disposable_email=domain in _DISPOSABLE_DOMAINS,
        phone_present=bool((row["phone"] or "").strip()),
        region_present=bool((row["region"] or "").strip()),
        customer_orders=int(history["total"]),
        customer_confirmed=int(history["confirmed"]),
    )
    return order_id, features


def _llm_merge(
    features: ReviewFeatures,
    verdict: Verdict,
    *,
    provider: str,
    model: str,
) -> Verdict:
    payload = {
        "pedido": features.plan_name,
        "precio_mensual": features.monthly_total,
        "infraestructura": features.infra_estimate,
        "senales_regla": [asdict(flag) for flag in verdict.flags],
    }
    result = ai_provider.complete_json(
        provider=provider,
        system=(
            "Eres un analista de ventas B2B. Recibes señales ya calculadas de un "
            "pedido y devuelves un JSON con 'summary' (resumen en español, máx. 60 "
            "palabras) y 'flags' (array de {code, severity, message}) solo si "
            "detectas algo relevante no cubierto. No inventes datos."
        ),
        user=json.dumps(payload, ensure_ascii=False, default=str),
        model=model,
    )
    if result is None:
        return verdict

    flags = list(verdict.flags)
    existing = {flag.code for flag in flags}
    extra = result.get("flags")
    if isinstance(extra, list):
        for item in extra:
            if not isinstance(item, dict):
                continue
            code = item.get("code")
            severity = item.get("severity")
            message = item.get("message")
            if (
                isinstance(code, str)
                and code
                and code not in existing
                and severity in _SEVERITY_WEIGHT
                and isinstance(message, str)
                and message
            ):
                flags.append(Flag(code=code, severity=severity, message=message))
                existing.add(code)

    summary = result.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        summary = verdict.summary

    risk = _max_risk(flags)
    return Verdict(
        risk=risk,
        summary=summary.strip()[:1000],
        flags=flags,
        recommendation=_recommendation(risk),
        confidence=_confidence(flags),
        model=model,
    )


def run_review(db: Session, *, code: str, actor_id: int | None = None) -> Verdict:
    row = (
        db.execute(
            text("select id, status from orders where code = :code"),
            {"code": code},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise ReviewNotFoundError(code)
    if row["status"] not in _OPEN_STATUSES:
        raise ReviewStateError("El pedido ya fue confirmado o rechazado.")

    loaded = _load_features(db, code)
    if loaded is None:
        raise ReviewNotFoundError(code)
    order_id, features = loaded

    verdict = assess(features)
    provider = get_review_provider(db)
    model = get_review_model(db, provider)
    if get_review_mode(db) in ("llm", "hybrid") and ai_provider.has_key(provider):
        verdict = _llm_merge(features, verdict, provider=provider, model=model)

    payload = {
        "items": [asdict(flag) for flag in verdict.flags],
        "recommendation": verdict.recommendation,
        "confidence": verdict.confidence,
        "model": verdict.model,
        "features": asdict(features),
    }

    db.execute(
        text(
            "insert into order_reviews (order_id, summary, flags, risk) "
            "values (:order_id, :summary, :flags, :risk)"
        ),
        {
            "order_id": order_id,
            "summary": verdict.summary,
            "flags": Jsonb(payload),
            "risk": verdict.risk,
        },
    )
    db.execute(
        text(
            "update orders set risk = :risk, "
            "status = case when status = 'pendiente' then 'en_revision' else status end, "
            "updated_at = now() where id = :order_id"
        ),
        {"risk": verdict.risk, "order_id": order_id},
    )
    db.execute(
        text(
            "insert into order_events (order_id, event_type, description, actor_id) "
            "values (:order_id, 'revision_ia', :description, :actor_id)"
        ),
        {
            "order_id": order_id,
            "description": verdict.summary[:500],
            "actor_id": actor_id,
        },
    )
    write_audit(
        db,
        action="orders.review",
        actor_id=actor_id,
        entity="order",
        entity_id=code,
        detail={
            "risk": verdict.risk,
            "recommendation": verdict.recommendation,
            "confidence": verdict.confidence,
            "model": verdict.model,
        },
    )
    db.commit()
    return verdict


def confirm_order(db: Session, *, code: str, actor_id: int) -> None:
    row = (
        db.execute(
            text("select id, status from orders where code = :code"),
            {"code": code},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise ReviewNotFoundError(code)
    if row["status"] not in _OPEN_STATUSES:
        raise ReviewStateError("El pedido ya fue confirmado o rechazado.")

    db.execute(
        text(
            "update orders set status = 'confirmado', reviewed_by = :actor_id, "
            "reviewed_at = now(), reject_reason = null, updated_at = now() "
            "where id = :order_id"
        ),
        {"actor_id": actor_id, "order_id": row["id"]},
    )
    db.execute(
        text(
            "insert into order_events (order_id, event_type, description, actor_id) "
            "values (:order_id, 'confirmado', 'Venta confirmada', :actor_id)"
        ),
        {"order_id": row["id"], "actor_id": actor_id},
    )
    write_audit(
        db,
        action="orders.confirm",
        actor_id=actor_id,
        entity="order",
        entity_id=code,
        detail={"status": "confirmado"},
    )
    db.commit()


def reject_order(db: Session, *, code: str, actor_id: int, reason: str) -> None:
    row = (
        db.execute(
            text("select id, status from orders where code = :code"),
            {"code": code},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise ReviewNotFoundError(code)
    if row["status"] not in _OPEN_STATUSES:
        raise ReviewStateError("El pedido ya fue confirmado o rechazado.")

    db.execute(
        text(
            "update orders set status = 'rechazado', reviewed_by = :actor_id, "
            "reviewed_at = now(), reject_reason = :reason, updated_at = now() "
            "where id = :order_id"
        ),
        {"actor_id": actor_id, "reason": reason, "order_id": row["id"]},
    )
    db.execute(
        text(
            "insert into order_events (order_id, event_type, description, actor_id) "
            "values (:order_id, 'rechazado', :description, :actor_id)"
        ),
        {
            "order_id": row["id"],
            "description": f"Pedido rechazado: {reason}"[:500],
            "actor_id": actor_id,
        },
    )
    write_audit(
        db,
        action="orders.reject",
        actor_id=actor_id,
        entity="order",
        entity_id=code,
        detail={"status": "rechazado", "reason": reason},
    )
    db.commit()
