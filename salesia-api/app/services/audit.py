from typing import Any, Mapping

from psycopg.types.json import Jsonb
from sqlalchemy import text
from sqlalchemy.orm import Session


def write_audit(
    db: Session,
    *,
    action: str,
    actor_id: int | None = None,
    entity: str | None = None,
    entity_id: str | None = None,
    detail: Mapping[str, Any] | None = None,
    ip: str | None = None,
) -> None:
    db.execute(
        text(
            "insert into audit_log "
            "(actor_id, action, entity, entity_id, detail, ip) "
            "values (:actor_id, :action, :entity, :entity_id, :detail, :ip)"
        ),
        {
            "actor_id": actor_id,
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "detail": Jsonb(detail if detail is not None else {}),
            "ip": ip,
        },
    )
