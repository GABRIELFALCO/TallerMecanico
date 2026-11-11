from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.dependencies import current_user, require_csrf
from app.repositories import Repositories, get_repositories
from app.schemas import CustomerAccountRegisterInput, LoginInput, MeView, MembershipView, RegisterInput
from app.security import create_session_token, hash_password, needs_rehash, new_csrf_token, new_session_id, verify_password
from shared.db.models import User, UserSession, Workshop, Membership

router = APIRouter(prefix="/auth", tags=["Autenticación"])
settings = get_settings()


def me_view(user: User, repos: Repositories) -> MeView:
    memberships = repos.auth.list_memberships(user.id)
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


def set_session_cookies(response: Response, user: User, repos: Repositories, user_agent: str | None) -> None:
    session_id = new_session_id()
    token, expires_at = create_session_token(user.id, session_id)
    repos.auth.add_session(UserSession(id=session_id, user_id=user.id, expires_at=expires_at, user_agent=(user_agent or "")[:255]))
    repos.commit()
    max_age = settings.session_hours * 60 * 60
    response.set_cookie("session_token", token, max_age=max_age, httponly=True, secure=settings.cookie_secure, samesite="lax")
    response.set_cookie("csrf_token", new_csrf_token(), max_age=max_age, httponly=False, secure=settings.cookie_secure, samesite="lax")


@router.get("/csrf")
def csrf(response: Response):
    """Entrega un token antifalsificación antes de operaciones que modifican datos."""
    response.set_cookie("csrf_token", new_csrf_token(), max_age=3600, httponly=False, secure=settings.cookie_secure, samesite="lax")
    return {"message": "Protección de solicitud preparada."}


@router.post("/register", response_model=MeView, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def register(payload: RegisterInput, response: Response, request: Request, repos: Repositories = Depends(get_repositories)):
    email = str(payload.email).lower()
    if repos.auth.find_user_by_email(email):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con este correo. Inicia sesión o usa otro correo.")
    workshop_name = " ".join(payload.workshop_name.split())
    duplicate_name = repos.workshops.find_by_name(workshop_name)
    duplicate_tax_id = repos.workshops.find_by_tax_id(payload.workshop_tax_id)
    if duplicate_name and duplicate_tax_id:
        raise HTTPException(status_code=409, detail="Ya existe un taller con ese nombre y RFC. Usa datos fiscales diferentes.")
    if duplicate_name:
        raise HTTPException(status_code=409, detail="Ya existe un taller con ese nombre. Elige otro nombre comercial.")
    if duplicate_tax_id:
        raise HTTPException(status_code=409, detail="Ya existe un taller con ese RFC. Verifica el RFC o inicia sesión con la cuenta existente.")
    admin_role = repos.roles.get_by_code("admin")
    if not admin_role:
        raise HTTPException(status_code=500, detail="No se configuraron los roles iniciales del sistema.")
    user = User(full_name=payload.full_name.strip(), email=email, password_hash=hash_password(payload.password), is_verified=True)
    workshop = Workshop(
        name=workshop_name,
        tax_id=payload.workshop_tax_id,
        state=payload.workshop_state,
        municipality=payload.workshop_municipality,
        locality=payload.workshop_locality,
        colony=payload.workshop_colony,
        postal_code=payload.workshop_postal_code,
        is_active=True,
    )
    try:
        repos.auth.add_user(user)
        repos.workshops.add(workshop)
        repos.workshops.add_membership(Membership(user_id=user.id, workshop_id=workshop.id, role_id=admin_role.id, is_active=True))
        repos.commit()
    except IntegrityError:
        repos.rollback()
        raise HTTPException(status_code=409, detail="No se pudo crear la cuenta porque el correo o los datos del taller ya están registrados.")
    set_session_cookies(response, user, repos, request.headers.get("user-agent"))
    return me_view(user, repos)


@router.post("/register-customer", response_model=MeView, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def register_customer_account(
    payload: CustomerAccountRegisterInput,
    response: Response,
    request: Request,
    repos: Repositories = Depends(get_repositories),
):
    """Crea acceso de cliente para un registro activo ya existente en un taller."""
    email = str(payload.email).lower()
    if repos.auth.find_user_by_email(email):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con este correo. Inicia sesión o usa otro correo.")

    workshop = repos.workshops.find_by_tax_id(payload.workshop_tax_id)
    if not workshop:
        raise HTTPException(status_code=404, detail="No encontramos un taller activo con ese RFC.")
    if not workshop.is_active:
        raise HTTPException(status_code=403, detail="El taller está inactivo. Solicita ayuda al administrador.")

    customer = repos.customers.find_by_email(workshop.id, email)
    if not customer:
        raise HTTPException(
            status_code=404,
            detail="No encontramos una ficha de cliente con ese correo en el taller identificado por el RFC. Verifica ambos datos con recepción.",
        )
    if not customer.is_active:
        raise HTTPException(status_code=403, detail="Tu registro de cliente está deshabilitado. Contacta al taller.")
    if customer.name.casefold() != payload.full_name.casefold():
        raise HTTPException(status_code=409, detail="El nombre no coincide con el registro de cliente del taller.")

    customer_role = repos.roles.get_by_code("customer")
    if not customer_role:
        raise HTTPException(status_code=500, detail="No se configuró el rol Cliente del sistema.")

    user = User(full_name=customer.name, email=email, password_hash=hash_password(payload.password), is_verified=True)
    try:
        repos.auth.add_user(user)
        repos.workshops.add_membership(Membership(user_id=user.id, workshop_id=workshop.id, role_id=customer_role.id, is_active=True))
        repos.commit()
    except IntegrityError:
        repos.rollback()
        raise HTTPException(status_code=409, detail="No se pudo crear la cuenta porque el correo ya está registrado.")

    set_session_cookies(response, user, repos, request.headers.get("user-agent"))
    return me_view(user, repos)


@router.post("/login", response_model=MeView, dependencies=[Depends(require_csrf)])
def login(payload: LoginInput, response: Response, request: Request, repos: Repositories = Depends(get_repositories)):
    user = repos.auth.find_user_by_email(str(payload.email).lower())
    # Se responde el mismo mensaje tanto si el correo como la contraseña fallan.
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Tu cuenta está desactivada. Contacta al administrador.")
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(payload.password)
        repos.commit()
    set_session_cookies(response, user, repos, request.headers.get("user-agent"))
    return me_view(user, repos)


@router.post("/logout", dependencies=[Depends(require_csrf)])
def logout(response: Response, user: User = Depends(current_user), repos: Repositories = Depends(get_repositories), request: Request = None):
    token = request.cookies.get("session_token") if request else None
    if token:
        try:
            from app.security import decode_session_token
            session = repos.auth.get_session(decode_session_token(token).get("sid"))
            if session and session.user_id == user.id:
                repos.auth.revoke_session(session, datetime.now(timezone.utc))
                repos.commit()
        except Exception:
            pass
    response.delete_cookie("session_token")
    response.delete_cookie("csrf_token")
    return {"message": "Sesión cerrada correctamente."}


@router.get("/me", response_model=MeView)
def me(user: User = Depends(current_user), repos: Repositories = Depends(get_repositories)):
    return me_view(user, repos)
