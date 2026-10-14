from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.orders_read import (
    ComponentLine,
    CustomerInfo,
    InfraComponentInfo,
    OrderCounts,
    OrderDetail,
    OrderEventInfo,
    OrderItemInfo,
    OrderListItem,
    OrderListResponse,
    PlanInfo,
    ReviewInfo,
    StaffRef,
)

_DETAIL_SQL = (
    "select o.id, o.code, o.status, o.risk, o.region_code, o.created_at, "
    "o.monthly_total, o.setup_total, o.reviewed_at, o.reject_reason, "
    "o.infra_usd, o.infra_estimate, o.fx_rate, "
    "c.company_name, c.ruc, c.contact_name, c.email, c.phone, c.region, "
    "p.code as plan_code, p.name as plan_name, "
    "p.description as plan_description, "
    "p.monthly_price as plan_monthly_price, "
    "p.setup_price as plan_setup_price, "
    "a.id as assigned_id, a.full_name as assigned_name, "
    "r.id as reviewed_id, r.full_name as reviewed_name "
    "from orders o "
    "join customers c on c.id = o.customer_id "
    "join plans p on p.id = o.plan_id "
    "left join staff_users a on a.id = o.assigned_to "
    "left join staff_users r on r.id = o.reviewed_by "
    "where o.code = :code"
)


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _build_filters(
    status: str | None, q: str | None, exclude_status: str | None = None
) -> tuple[str, dict]:
    conditions: list[str] = []
    params: dict = {}

    if status is not None:
        conditions.append("o.status = :status")
        params["status"] = status

    if exclude_status is not None:
        conditions.append("o.status <> :exclude_status")
        params["exclude_status"] = exclude_status

    if q is not None and q.strip():
        params["pattern"] = f"%{_escape_like(q)}%"
        conditions.append(
            "(o.code ilike :pattern escape '\\' "
            "or c.company_name ilike :pattern escape '\\')"
        )

    where_sql = (" where " + " and ".join(conditions)) if conditions else ""
    return where_sql, params


def list_orders(
    db: Session,
    *,
    status: str | None,
    q: str | None,
    page: int,
    page_size: int,
    exclude_status: str | None = None,
) -> OrderListResponse:
    where_sql, params = _build_filters(status, q, exclude_status)

    item_rows = (
        db.execute(
            text(
                "select o.code, c.company_name, p.name as plan_name, "
                "o.monthly_total, o.setup_total, o.status, o.risk, o.created_at "
                "from orders o "
                "join customers c on c.id = o.customer_id "
                "join plans p on p.id = o.plan_id"
                + where_sql
                + " order by o.created_at desc, o.id desc "
                "limit :limit offset :offset"
            ),
            {**params, "limit": page_size, "offset": (page - 1) * page_size},
        )
        .mappings()
        .all()
    )

    total = db.execute(
        text(
            "select count(*) "
            "from orders o "
            "join customers c on c.id = o.customer_id"
            + where_sql
        ),
        params,
    ).scalar_one()

    count_rows = (
        db.execute(
            text("select status, count(*) as amount from orders group by status")
        )
        .mappings()
        .all()
    )
    counts = {"pendiente": 0, "en_revision": 0, "confirmado": 0, "rechazado": 0}
    for row in count_rows:
        if row["status"] in counts:
            counts[row["status"]] = row["amount"]

    ingresos_confirmado = db.execute(
        text(
            "select coalesce(sum(monthly_total + setup_total), 0) "
            "from orders where status = 'confirmado'"
        )
    ).scalar_one()

    items = [
        OrderListItem(
            code=row["code"],
            company_name=row["company_name"],
            plan_name=row["plan_name"],
            monthly_total=row["monthly_total"],
            setup_total=row["setup_total"],
            status=row["status"],
            risk=row["risk"],
            created_at=row["created_at"],
        )
        for row in item_rows
    ]

    return OrderListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        counts=OrderCounts(
            total=sum(counts.values()),
            **counts,
            ingresos_confirmado=float(ingresos_confirmado),
        ),
    )


def get_order_detail(db: Session, code: str) -> OrderDetail | None:
    row = db.execute(text(_DETAIL_SQL), {"code": code}).mappings().first()
    if row is None:
        return None

    order_id = row["id"]

    item_rows = (
        db.execute(
            text(
                "select extra_name, monthly_price, setup_price, quantity "
                "from order_items where order_id = :order_id order by id"
            ),
            {"order_id": order_id},
        )
        .mappings()
        .all()
    )

    review_row = (
        db.execute(
            text(
                "select summary, flags, risk, created_at "
                "from order_reviews where order_id = :order_id "
                "order by created_at desc, id desc limit 1"
            ),
            {"order_id": order_id},
        )
        .mappings()
        .first()
    )

    component_rows = (
        db.execute(
            text(
                "select service_code, usd_monthly, breakdown "
                "from order_components where order_id = :order_id "
                "order by service_code"
            ),
            {"order_id": order_id},
        )
        .mappings()
        .all()
    )

    event_rows = (
        db.execute(
            text(
                "select e.event_type, e.description, e.created_at, "
                "s.full_name as actor_name "
                "from order_events e "
                "left join staff_users s on s.id = e.actor_id "
                "where e.order_id = :order_id "
                "order by e.created_at asc, e.id asc"
            ),
            {"order_id": order_id},
        )
        .mappings()
        .all()
    )

    assigned_to = None
    if row["assigned_id"] is not None:
        assigned_to = StaffRef(
            id=row["assigned_id"], full_name=row["assigned_name"]
        )

    reviewed_by = None
    if row["reviewed_id"] is not None:
        reviewed_by = StaffRef(
            id=row["reviewed_id"], full_name=row["reviewed_name"]
        )

    review = None
    if review_row is not None:
        raw_flags = review_row["flags"]
        recommendation = None
        confidence = None
        model = None
        flags = raw_flags
        if isinstance(raw_flags, dict):
            flags = raw_flags.get("items")
            recommendation = raw_flags.get("recommendation")
            confidence = raw_flags.get("confidence")
            model = raw_flags.get("model")
        review = ReviewInfo(
            summary=review_row["summary"],
            flags=flags,
            risk=review_row["risk"],
            recommendation=recommendation,
            confidence=confidence,
            model=model,
            created_at=review_row["created_at"],
        )

    return OrderDetail(
        code=row["code"],
        status=row["status"],
        risk=row["risk"],
        region_code=row["region_code"],
        created_at=row["created_at"],
        monthly_total=row["monthly_total"],
        setup_total=row["setup_total"],
        infra_usd=row["infra_usd"],
        infra_estimate=row["infra_estimate"],
        fx_rate=row["fx_rate"],
        customer=CustomerInfo(
            company_name=row["company_name"],
            ruc=row["ruc"],
            contact_name=row["contact_name"],
            email=row["email"],
            phone=row["phone"],
            region=row["region"],
        ),
        plan=PlanInfo(
            code=row["plan_code"],
            name=row["plan_name"],
            description=row["plan_description"],
            monthly_price=row["plan_monthly_price"],
            setup_price=row["plan_setup_price"],
        ),
        items=[
            OrderItemInfo(
                extra_name=item["extra_name"],
                monthly_price=item["monthly_price"],
                setup_price=item["setup_price"],
                quantity=item["quantity"],
            )
            for item in item_rows
        ],
        infra_components=[
            InfraComponentInfo(
                service_code=component["service_code"],
                usd_monthly=component["usd_monthly"],
                breakdown=[
                    ComponentLine(label=line["label"], amount=line["amount"])
                    for line in (component["breakdown"] or [])
                ],
            )
            for component in component_rows
        ],
        assigned_to=assigned_to,
        reviewed_by=reviewed_by,
        reviewed_at=row["reviewed_at"],
        reject_reason=row["reject_reason"],
        review=review,
        events=[
            OrderEventInfo(
                event_type=event["event_type"],
                description=event["description"],
                actor_name=event["actor_name"],
                created_at=event["created_at"],
            )
            for event in event_rows
        ],
    )
