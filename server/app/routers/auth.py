from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.dependencies import current_user, require_csrf
from app.schemas import LoginInput, MeView, MembershipView, RegisterInput
from app.security import create_session_token, hash_password, needs_rehash, new_csrf_token, new_session_id, verify_password
from shared.db.database import get_db
from shared.db.models import Membership, Role, User, UserSession, Workshop

router = APIRouter(prefix="/auth", tags=["Autenticación"])
settings = get_settings()


def me_view(user: User, db: Session) -> MeView:
    memberships = (
        db.query(Membership)
        .options(joinedload(Membership.role), joinedload(Membership.workshop))
        .filter(Membership.user_id == user.id, Membership.is_active.is_(True))
        .all()
    )
    return MeView(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        is_verified=user.is_verified,
        memberships=[
            MembershipView(
                workshop_id=item.workshop.id,
                workshop_name=item.workshop.name,
                workshop_active=item.workshop.is_active,
                role=item.role.code,
            )
            for item in memberships
        ],
    )


def set_session_cookies(response: Response, user: User, db: Session, user_agent: str | None) -> None:
    session_id = new_session_id()
    token, expires_at = create_session_token(user.id, session_id)
    db.add(UserSession(id=session_id, user_id=user.id, expires_at=expires_at, user_agent=(user_agent or "")[:255]))
    db.commit()
    max_age = settings.session_hours * 60 * 60
    response.set_cookie("session_token", token, max_age=max_age, httponly=True, secure=settings.cookie_secure, samesite="lax")
    response.set_cookie("csrf_token", new_csrf_token(), max_age=max_age, httponly=False, secure=settings.cookie_secure, samesite="lax")


@router.get("/csrf")
def csrf(response: Response):
    """Entrega un token antifalsificación antes de operaciones que modifican datos."""
    response.set_cookie("csrf_token", new_csrf_token(), max_age=3600, httponly=False, secure=settings.cookie_secure, samesite="lax")
    return {"message": "Protección de solicitud preparada."}


@router.post("/register", response_model=MeView, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def register(payload: RegisterInput, response: Response, request: Request, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con este correo. Inicia sesión o usa otro correo.")
    owner_role = db.query(Role).filter(Role.code == "owner").first()
    if not owner_role:
        raise HTTPException(status_code=500, detail="No se configuraron los roles iniciales del sistema.")
    user = User(full_name=payload.full_name.strip(), email=email, password_hash=hash_password(payload.password), is_verified=True)
    workshop = Workshop(name=payload.workshop_name.strip(), is_active=True)
    db.add_all([user, workshop])
    db.flush()
    db.add(Membership(user_id=user.id, workshop_id=workshop.id, role_id=owner_role.id, is_active=True))
    db.commit()
    db.refresh(user)
    set_session_cookies(response, user, db, request.headers.get("user-agent"))
    return me_view(user, db)


@router.post("/login", response_model=MeView, dependencies=[Depends(require_csrf)])
def login(payload: LoginInput, response: Response, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(payload.email).lower()).first()
    # Se responde el mismo mensaje tanto si el correo como la contraseña fallan.
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Tu cuenta está desactivada. Contacta al administrador.")
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(payload.password)
        db.commit()
    set_session_cookies(response, user, db, request.headers.get("user-agent"))
    return me_view(user, db)


@router.post("/logout", dependencies=[Depends(require_csrf)])
def logout(response: Response, user: User = Depends(current_user), db: Session = Depends(get_db), request: Request = None):
    token = request.cookies.get("session_token") if request else None
    if token:
        try:
            from app.security import decode_session_token
            session = db.get(UserSession, decode_session_token(token).get("sid"))
            if session and session.user_id == user.id:
                session.revoked_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass
    response.delete_cookie("session_token")
    response.delete_cookie("csrf_token")
    return {"message": "Sesión cerrada correctamente."}


@router.get("/me", response_model=MeView)
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return me_view(user, db)
