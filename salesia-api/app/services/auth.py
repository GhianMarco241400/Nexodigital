import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.config import settings
from app.schemas.auth import UserOut
from app.services.audit import write_audit

_ph = PasswordHasher()
_DUMMY_HASH = _ph.hash("salesia-dummy-password-for-timing")

_RATE_LIMIT_WINDOW_SECONDS = 15 * 60
_RATE_LIMIT_MAX_FAILURES = 5
# NOTA: el bloqueo por fuerza bruta vive en memoria del proceso. En producción
# con varios workers/procesos esto debe moverse a un almacén compartido
# (Redis o una tabla en la base de datos) para ser consistente entre procesos.
_RATE_LIMIT_LOCK = threading.Lock()
_failed_logins: dict[tuple[str, str], list[float]] = {}


class AuthError(Exception):
    """Base para errores de autenticación."""


class InvalidCredentialsError(AuthError):
    """Credenciales inválidas (usuario inexistente, inactivo o contraseña errónea)."""


class RateLimitedError(AuthError):
    """Demasiados intentos fallidos recientes."""


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        options={"require": ["exp", "iat", "sub"]},
    )


def authenticate(db: Session, email: str, password: str) -> RowMapping | None:
    user = (
        db.execute(
            text(
                "select id, full_name, email, role, active, password_hash "
                "from staff_users where email = :email"
            ),
            {"email": email},
        )
        .mappings()
        .first()
    )

    if user is None:
        # Verificamos contra un hash falso para no revelar por tiempo
        # si el correo existe.
        verify_password(_DUMMY_HASH, password)
        return None

    if not user["active"] or not user["password_hash"]:
        verify_password(_DUMMY_HASH, password)
        return None

    if not verify_password(user["password_hash"], password):
        return None

    return user


def get_user_by_id(db: Session, user_id: int) -> RowMapping | None:
    return (
        db.execute(
            text(
                "select id, full_name, email, role, active "
                "from staff_users where id = :user_id"
            ),
            {"user_id": user_id},
        )
        .mappings()
        .first()
    )


def _purge_expired_locked(now: float) -> None:
    expired = [
        key
        for key, timestamps in _failed_logins.items()
        if not timestamps or now - timestamps[-1] >= _RATE_LIMIT_WINDOW_SECONDS
    ]
    for key in expired:
        del _failed_logins[key]


def is_rate_limited(email: str, ip: str) -> bool:
    key = (email, ip)
    now = time.monotonic()
    with _RATE_LIMIT_LOCK:
        timestamps = _failed_logins.get(key)
        if not timestamps:
            return False
        if now - timestamps[-1] >= _RATE_LIMIT_WINDOW_SECONDS:
            del _failed_logins[key]
            return False
        return len(timestamps) >= _RATE_LIMIT_MAX_FAILURES


def register_failure(email: str, ip: str) -> None:
    key = (email, ip)
    now = time.monotonic()
    with _RATE_LIMIT_LOCK:
        # Limpiamos entradas vencidas para que el diccionario no crezca sin límite.
        _purge_expired_locked(now)
        timestamps = _failed_logins.get(key)
        if timestamps is None or now - timestamps[-1] >= _RATE_LIMIT_WINDOW_SECONDS:
            timestamps = []
            _failed_logins[key] = timestamps
        timestamps.append(now)
        timestamps[:] = [
            moment for moment in timestamps if now - moment < _RATE_LIMIT_WINDOW_SECONDS
        ]


def reset_failures(email: str, ip: str) -> None:
    with _RATE_LIMIT_LOCK:
        _failed_logins.pop((email, ip), None)


def _user_out(user: RowMapping) -> UserOut:
    return UserOut(
        id=user["id"],
        full_name=user["full_name"],
        email=user["email"],
        role=user["role"],
    )


def login(
    db: Session, email: str, password: str, ip: str | None
) -> tuple[str, UserOut, int]:
    client_ip = ip or ""

    if is_rate_limited(email, client_ip):
        raise RateLimitedError("Demasiados intentos, intenta más tarde")

    user = authenticate(db, email, password)

    if user is None:
        register_failure(email, client_ip)
        write_audit(
            db,
            action="login_failed",
            actor_id=None,
            entity="staff_users",
            entity_id=None,
            detail={"email": email},
            ip=ip,
        )
        # El fallo debe persistir aunque el login no haya sido exitoso.
        db.commit()
        raise InvalidCredentialsError("Correo o contraseña incorrectos")

    reset_failures(email, client_ip)
    db.execute(
        text("update staff_users set last_login_at = now() where id = :user_id"),
        {"user_id": user["id"]},
    )
    write_audit(
        db,
        action="login_ok",
        actor_id=user["id"],
        entity="staff_users",
        entity_id=str(user["id"]),
        detail=None,
        ip=ip,
    )
    db.commit()

    token = create_token(user["id"], user["role"])
    return token, _user_out(user), settings.jwt_expire_minutes * 60
