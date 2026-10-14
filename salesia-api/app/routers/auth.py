from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import AuthenticatedUser, get_current_user
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.services.auth import InvalidCredentialsError, RateLimitedError, login

router = APIRouter(prefix="/auth", tags=["auth"])

_WWW_AUTHENTICATE = {"WWW-Authenticate": "Bearer"}


@router.post("/login", response_model=TokenResponse)
def login_endpoint(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    ip = request.client.host if request.client else None

    try:
        token, user, expires_in = login(
            db, str(payload.email), payload.password, ip
        )
    except RateLimitedError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers=_WWW_AUTHENTICATE,
        ) from exc

    return TokenResponse(access_token=token, expires_in=expires_in, user=user)


@router.get("/me", response_model=UserOut)
def me_endpoint(
    user: AuthenticatedUser = Depends(get_current_user),
) -> UserOut:
    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
    )
