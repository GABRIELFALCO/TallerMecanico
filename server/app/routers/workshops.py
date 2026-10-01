from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.dependencies import current_user, require_csrf, require_roles
from app.schemas import CustomerInput, MembershipInput, WorkshopInput
from shared.db.database import get_db
from shared.db.models import Customer, Membership, Role, User, Workshop

router = APIRouter(tags=["Talleres y clientes"])


@router.get("/workshops")
def list_workshops(user: User = Depends(current_user), db: Session = Depends(get_db)):
    items = (
        db.query(Membership)
        .options(joinedload(Membership.role), joinedload(Membership.workshop))
        .filter(Membership.user_id == user.id, Membership.is_active.is_(True))
        .all()
    )
    return [
        {"id": item.workshop.id, "name": item.workshop.name, "is_active": item.workshop.is_active, "role": item.role.code}
        for item in items
    ]


@router.post("/workshops", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_workshop(payload: WorkshopInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    owner_role = db.query(Role).filter(Role.code == "owner").first()
    workshop = Workshop(name=payload.name.strip(), tax_id=payload.tax_id.strip() if payload.tax_id else None)
    db.add(workshop)
    db.flush()
    db.add(Membership(user_id=user.id, workshop_id=workshop.id, role_id=owner_role.id))
    db.commit()
    return {"id": workshop.id, "name": workshop.name, "is_active": workshop.is_active, "message": "Taller creado y asociado a tu cuenta."}


@router.get("/roles")
def list_roles(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [{"code": role.code, "name": role.name, "description": role.description} for role in db.query(Role).order_by(Role.name).all()]


@router.post("/workshops/{workshop_id}/members", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def assign_member(
    workshop_id: str,
    payload: MembershipInput,
    membership: Membership = Depends(require_roles("owner")),
    db: Session = Depends(get_db),
):
    """Asigna un rol a una cuenta existente. Solo el propietario del taller puede hacerlo."""
    if membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    user = db.query(User).filter(User.email == str(payload.email).lower()).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="No encontramos una cuenta activa con ese correo. Pide a la persona que cree su cuenta primero.")
    role = db.query(Role).filter(Role.code == payload.role).first()
    existing = db.query(Membership).filter(Membership.user_id == user.id, Membership.workshop_id == workshop_id).first()
    if existing:
        existing.role_id = role.id
        existing.is_active = True
        message = "Rol actualizado correctamente."
    else:
        db.add(Membership(user_id=user.id, workshop_id=workshop_id, role_id=role.id, is_active=True))
        message = "Usuario autorizado y rol asignado correctamente."
    db.commit()
    return {"message": message, "email": user.email, "role": role.code}


@router.post("/workshops/{workshop_id}/customers", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_customer(
    workshop_id: str,
    payload: CustomerInput,
    membership: Membership = Depends(require_roles("owner", "manager", "reception")),
    db: Session = Depends(get_db),
):
    # require_roles verifica pertenencia autorizada y que el taller esté activo.
    if membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    phone = payload.phone.strip()
    if db.query(Customer).filter(Customer.workshop_id == workshop_id, Customer.phone == phone).first():
        raise HTTPException(status_code=409, detail="Ya existe un cliente con este teléfono en el taller.")
    customer = Customer(workshop_id=workshop_id, name=payload.name.strip(), phone=phone, email=str(payload.email).lower() if payload.email else None)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return {"id": customer.id, "name": customer.name, "phone": customer.phone, "email": customer.email, "message": "Cliente registrado correctamente."}
