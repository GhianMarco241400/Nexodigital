from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import auth as auth_service

bearer_scheme = HTTPBearer(auto_error=False)

_WWW_AUTHENTICATE = {"WWW-Authenticate": "Bearer"}


@dataclass(frozen=True)
class AuthenticatedUser:
    id: int
    full_name: str
    email: str
    role: str


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers=_WWW_AUTHENTICATE,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    if credentials is None or not credentials.credentials:
        raise _unauthorized("No autenticado")

    try:
        payload = auth_service.decode_token(credentials.credentials)
    except jwt.InvalidTokenError as exc:
        raise _unauthorized("Token inválido o vencido") from exc

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise _unauthorized("Token inválido o vencido") from exc

    user = auth_service.get_user_by_id(db, user_id)
    if user is None or not user["active"]:
        raise _unauthorized("Usuario no autorizado")

    return AuthenticatedUser(
        id=user["id"],
        full_name=user["full_name"],
        email=user["email"],
        role=user["role"],
    )


def require_roles(*roles: str):
    allowed = set(roles)

    def dependency(
        user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para esta acción",
            )
        return user

    return dependency
