from datetime import datetime, timezone

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.security import csrf_matches, decode_session_token
from shared.db.database import get_db
from shared.db.models import Membership, User, UserSession, Workshop


def require_csrf(request: Request, csrf_token: str | None = Cookie(default=None)) -> None:
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        if not csrf_matches(csrf_token, request.headers.get("X-CSRF-Token")):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solicitud de seguridad inválida. Recarga la página e inténtalo de nuevo.")


def current_user(
    session_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not session_token:
        raise HTTPException(status_code=401, detail="Tu sesión no está disponible. Inicia sesión nuevamente.")
    try:
        claims = decode_session_token(session_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Tu sesión expiró. Inicia sesión nuevamente.")
    db_session = db.get(UserSession, claims.get("sid"))
    user = db.get(User, claims.get("sub"))
    expires_at = db_session.expires_at if db_session else None
    # SQLite devuelve fechas sin zona horaria aunque la columna se declare timezone=True.
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not db_session or not user or db_session.revoked_at or not expires_at or expires_at <= datetime.now(timezone.utc) or not user.is_active:
        raise HTTPException(status_code=401, detail="Tu sesión ya no es válida. Inicia sesión nuevamente.")
    return user


def active_membership(
    workshop_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> Membership:
    membership = (
        db.query(Membership)
        .options(joinedload(Membership.role), joinedload(Membership.workshop))
        .filter(Membership.user_id == user.id, Membership.workshop_id == workshop_id, Membership.is_active.is_(True))
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No tienes autorización para este taller.")
    if not membership.workshop.is_active:
        raise HTTPException(status_code=403, detail="Este taller está inactivo. Contacta al administrador.")
    return membership


def require_roles(*roles: str):
    def dependency(membership: Membership = Depends(active_membership)) -> Membership:
        if membership.role.code not in roles:
            raise HTTPException(status_code=403, detail="Tu rol no tiene permiso para realizar esta acción.")
        return membership
    return dependency
