from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.dependencies import current_user, require_admin_user, require_csrf, require_roles
from app.repositories import Repositories, get_repositories
from app.schemas import CustomerInput, CustomerStatusInput, CustomerUpdateInput, MembershipInput, MembershipStatusInput, RoleUpdateInput, VehicleInput, VehicleUpdateInput, WorkshopInput, WorkshopStatusInput, WorkshopUpdateInput, decode_photo_data_url
from shared.db.models import Customer, Membership, User, Vehicle, Workshop

router = APIRouter(tags=["Talleres y clientes"])


@router.get("/workshops")
def list_workshops(user: User = Depends(current_user), repos: Repositories = Depends(get_repositories)):
    items = repos.workshops.list_user_memberships(user.id)
    return [
        {"id": item.workshop.id, "name": item.workshop.name, "tax_id": item.workshop.tax_id, "state": item.workshop.state, "municipality": item.workshop.municipality, "locality": item.workshop.locality, "colony": item.workshop.colony, "postal_code": item.workshop.postal_code, "is_active": item.workshop.is_active, "role": item.role.code}
        for item in items
    ]


@router.post("/workshops", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_workshop(payload: WorkshopInput, user: User = Depends(require_admin_user), repos: Repositories = Depends(get_repositories)):
    admin_role = repos.roles.get_by_code("admin")
    duplicate_name = repos.workshops.find_by_name(payload.name)
    duplicate_tax_id = repos.workshops.find_by_tax_id(payload.tax_id)
    if duplicate_name and duplicate_tax_id:
        raise HTTPException(status_code=409, detail="Ya existen un taller con ese nombre y RFC.")
    if duplicate_name:
        raise HTTPException(status_code=409, detail="Ya existe un taller con ese nombre.")
    if duplicate_tax_id:
        raise HTTPException(status_code=409, detail="Ya existe un taller con ese RFC.")
    photo_data, photo_content_type = decode_photo_data_url(payload.photo_data_url)
    workshop = Workshop(name=payload.name.strip(), tax_id=payload.tax_id, state=payload.state, municipality=payload.municipality, locality=payload.locality, colony=payload.colony, postal_code=payload.postal_code, photo_data=photo_data, photo_content_type=photo_content_type)
    repos.workshops.add(workshop)
    repos.workshops.add_membership(Membership(user_id=user.id, workshop_id=workshop.id, role_id=admin_role.id))
    repos.commit()
    return {"id": workshop.id, "name": workshop.name, "tax_id": workshop.tax_id, "state": workshop.state, "municipality": workshop.municipality, "locality": workshop.locality, "colony": workshop.colony, "postal_code": workshop.postal_code, "photo_url": f"/api/admin/workshops/{workshop.id}/photo" if workshop.photo_content_type else None, "is_active": workshop.is_active, "role": "admin", "message": "Taller creado y asociado a tu cuenta."}


@router.get("/admin/workshops")
def list_admin_workshops(user: User = Depends(require_admin_user), repos: Repositories = Depends(get_repositories)):
    return [
        {"id": item.workshop.id, "name": item.workshop.name, "tax_id": item.workshop.tax_id, "state": item.workshop.state, "municipality": item.workshop.municipality, "locality": item.workshop.locality, "colony": item.workshop.colony, "postal_code": item.workshop.postal_code, "photo_url": f"/api/admin/workshops/{item.workshop.id}/photo" if item.workshop.photo_content_type else None, "is_active": item.workshop.is_active, "role": item.role.code}
        for item in repos.workshops.list_admin_workshops(user.id)
    ]


@router.get("/admin/workshops/{workshop_id}/photo")
def get_admin_workshop_photo(
    workshop_id: str,
    user: User = Depends(require_admin_user),
    repos: Repositories = Depends(get_repositories),
):
    membership = repos.workshops.get_any_membership(user.id, workshop_id)
    if not membership or membership.role.code != "admin":
        raise HTTPException(status_code=404, detail="No encontramos la foto de este taller.")
    photo = repos.workshops.get_photo(workshop_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Este taller no tiene una foto registrada.")
    image_data, content_type = photo
    return Response(
        content=image_data,
        media_type=content_type,
        headers={
            "Cache-Control": "private, no-store",
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; sandbox",
        },
    )


@router.patch("/admin/workshops/{workshop_id}", dependencies=[Depends(require_csrf)])
def update_workshop(
    workshop_id: str,
    payload: WorkshopUpdateInput,
    user: User = Depends(require_admin_user),
    repos: Repositories = Depends(get_repositories),
):
    membership = repos.workshops.get_any_membership(user.id, workshop_id)
    if not membership or membership.role.code != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos para administrar este taller.")
    duplicate_name = repos.workshops.find_by_name(payload.name, exclude_id=workshop_id)
    duplicate_tax_id = repos.workshops.find_by_tax_id(payload.tax_id, exclude_id=workshop_id)
    if duplicate_name or duplicate_tax_id:
        raise HTTPException(status_code=409, detail="Ya existe otro taller con ese nombre o RFC.")
    repos.workshops.update_workshop(membership.workshop, payload.name, payload.tax_id, payload.state, payload.municipality, payload.locality, payload.colony, payload.postal_code)
    repos.commit()
    return {"id": membership.workshop.id, "name": membership.workshop.name, "tax_id": membership.workshop.tax_id, "state": membership.workshop.state, "municipality": membership.workshop.municipality, "locality": membership.workshop.locality, "colony": membership.workshop.colony, "postal_code": membership.workshop.postal_code, "photo_url": f"/api/admin/workshops/{membership.workshop.id}/photo" if membership.workshop.photo_content_type else None, "is_active": membership.workshop.is_active, "role": "admin", "message": "Taller actualizado correctamente."}


@router.patch("/admin/workshops/{workshop_id}/status", dependencies=[Depends(require_csrf)])
def update_workshop_status(
    workshop_id: str,
    payload: WorkshopStatusInput,
    user: User = Depends(require_admin_user),
    repos: Repositories = Depends(get_repositories),
):
    membership = repos.workshops.get_any_membership(user.id, workshop_id)
    if not membership or membership.role.code != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos para administrar este taller.")
    repos.workshops.set_workshop_active(membership.workshop, payload.is_active)
    repos.commit()
    return {"id": membership.workshop.id, "is_active": membership.workshop.is_active, "message": "Taller activado correctamente." if payload.is_active else "Taller deshabilitado correctamente."}


@router.get("/roles")
def list_roles(user: User = Depends(current_user), repos: Repositories = Depends(get_repositories)):
    return [{"code": role.code, "name": role.name, "description": role.description} for role in repos.roles.list()]


@router.post("/workshops/{workshop_id}/members", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def assign_member(
    workshop_id: str,
    payload: MembershipInput,
    membership: Membership = Depends(require_roles("admin")),
    repos: Repositories = Depends(get_repositories),
):
    """Asigna un rol a una cuenta existente. Solo el administrador del taller puede hacerlo."""
    if membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    user = repos.auth.find_user_by_email(str(payload.email).lower())
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="No encontramos una cuenta activa con ese correo. Pide a la persona que cree su cuenta primero.")
    role = repos.roles.get_by_code(payload.role)
    existing = repos.workshops.find_membership(user.id, workshop_id)
    if existing:
        existing.role_id = role.id
        existing.is_active = True
        message = "Rol actualizado correctamente."
    else:
        repos.workshops.add_membership(Membership(user_id=user.id, workshop_id=workshop_id, role_id=role.id, is_active=True))
        message = "Usuario autorizado y rol asignado correctamente."
    repos.commit()
    return {"message": message, "email": user.email, "role": role.code}


@router.get("/workshops/{workshop_id}/role-assignments")
def list_role_assignments(
    workshop_id: str,
    membership: Membership = Depends(require_roles("admin")),
    repos: Repositories = Depends(get_repositories),
):
    """Devuelve el estado de cada asignación del taller para la pantalla administrativa."""
    if membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    assignments = repos.workshops.list_workshop_memberships(workshop_id)
    return [
        {
            "membership_id": item.id,
            "user_id": item.user.id,
            "full_name": item.user.full_name,
            "email": item.user.email,
            "role": item.role.code,
            "role_name": item.role.name,
            "is_active": item.is_active,
            "user_active": item.user.is_active,
        }
        for item in assignments
    ]


@router.patch("/workshops/{workshop_id}/members/{membership_id}/role", dependencies=[Depends(require_csrf)])
def update_member_role(
    workshop_id: str,
    membership_id: str,
    payload: RoleUpdateInput,
    current_membership: Membership = Depends(require_roles("admin")),
    repos: Repositories = Depends(get_repositories),
):
    if current_membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    target = repos.workshops.get_membership_by_id(workshop_id, membership_id)
    role = repos.roles.get_by_code(payload.role)
    if not target or not role:
        raise HTTPException(status_code=404, detail="No encontramos la asignación o el rol solicitado.")
    if target.role.code == "admin" and role.code != "admin" and target.is_active:
        admin_role = repos.roles.get_by_code("admin")
        if admin_role and repos.workshops.count_active_memberships_by_role(workshop_id, admin_role.id) <= 1:
            raise HTTPException(status_code=409, detail="No puedes retirar el último administrador activo del taller.")
    repos.workshops.set_role(target, role)
    repos.commit()
    return {"message": "Rol actualizado correctamente.", "membership_id": target.id, "role": role.code}


@router.patch("/workshops/{workshop_id}/members/{membership_id}/status", dependencies=[Depends(require_csrf)])
def update_member_status(
    workshop_id: str,
    membership_id: str,
    payload: MembershipStatusInput,
    current_user: User = Depends(current_user),
    current_membership: Membership = Depends(require_roles("admin")),
    repos: Repositories = Depends(get_repositories),
):
    if current_membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    target = repos.workshops.get_membership_by_id(workshop_id, membership_id)
    if not target:
        raise HTTPException(status_code=404, detail="No encontramos la asignación solicitada.")
    if target.user_id == current_user.id and not payload.is_active:
        raise HTTPException(status_code=409, detail="No puedes deshabilitar tu propia membresía administrativa.")
    if target.role.code == "admin" and not payload.is_active:
        admin_role = repos.roles.get_by_code("admin")
        if admin_role and repos.workshops.count_active_memberships_by_role(workshop_id, admin_role.id) <= 1:
            raise HTTPException(status_code=409, detail="No puedes deshabilitar el último administrador activo del taller.")
    if payload.is_active and not target.user.is_active:
        raise HTTPException(status_code=409, detail="La cuenta del usuario está desactivada y no puede reactivarse desde esta pantalla.")
    repos.workshops.set_active(target, payload.is_active)
    repos.commit()
    return {"message": "Membresía reactivada correctamente." if payload.is_active else "Membresía deshabilitada correctamente.", "membership_id": target.id, "is_active": target.is_active}


@router.post("/workshops/{workshop_id}/customers", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_customer(
    workshop_id: str,
    payload: CustomerInput,
    membership: Membership = Depends(require_roles("admin", "reception")),
    repos: Repositories = Depends(get_repositories),
):
    # require_roles verifica pertenencia autorizada y que el taller esté activo.
    if membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    phone = payload.phone.strip()
    normalized_email = str(payload.email).lower()
    duplicate_phone = repos.customers.find_by_phone(workshop_id, phone)
    duplicate_email = repos.customers.find_by_email(workshop_id, normalized_email)
    if duplicate_phone and duplicate_email:
        raise HTTPException(status_code=409, detail="Ya existe un cliente con ese teléfono y correo en este taller.")
    if duplicate_phone:
        raise HTTPException(status_code=409, detail="Ya existe un cliente con ese teléfono en este taller.")
    if duplicate_email:
        raise HTTPException(status_code=409, detail="Ya existe un cliente con ese correo en este taller.")
    customer = Customer(workshop_id=workshop_id, name=payload.full_name, phone=phone, email=normalized_email)
    repos.customers.add(customer)
    repos.commit()
    return {"id": customer.id, "full_name": customer.name, "phone": customer.phone, "email": customer.email, "contacts": 2, "message": "Cliente registrado correctamente."}


@router.get("/workshops/{workshop_id}/customers")
def list_customers(
    workshop_id: str,
    membership: Membership = Depends(require_roles("admin", "reception")),
    repos: Repositories = Depends(get_repositories),
):
    """Lista clientes únicamente del taller activo autorizado."""
    if membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    return [
        {
            "id": item.id,
            "full_name": item.name,
            "phone": item.phone,
            "email": item.email,
            "is_active": item.is_active,
            "workshop": {
                "id": item.workshop.id,
                "name": item.workshop.name,
                "tax_id": item.workshop.tax_id,
                "state": item.workshop.state,
                "municipality": item.workshop.municipality,
                "locality": item.workshop.locality,
                "colony": item.workshop.colony,
                "postal_code": item.workshop.postal_code,
            },
        }
        for item in repos.customers.list_by_workshop(workshop_id)
    ]


@router.patch("/workshops/{workshop_id}/customers/{customer_id}", dependencies=[Depends(require_csrf)])
def update_customer(
    workshop_id: str,
    customer_id: str,
    payload: CustomerUpdateInput,
    membership: Membership = Depends(require_roles("admin", "reception")),
    repos: Repositories = Depends(get_repositories),
):
    if membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    customer = repos.customers.get_by_id(workshop_id, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="No encontramos el cliente en este taller.")
    duplicate_phone = repos.customers.find_by_phone_excluding(workshop_id, payload.phone, customer_id)
    duplicate_email = repos.customers.find_by_email_excluding(workshop_id, str(payload.email).lower(), customer_id)
    if duplicate_phone and duplicate_email:
        raise HTTPException(status_code=409, detail="El teléfono y el correo ya pertenecen a otro cliente de este taller.")
    if duplicate_phone:
        raise HTTPException(status_code=409, detail="El teléfono ya pertenece a otro cliente de este taller.")
    if duplicate_email:
        raise HTTPException(status_code=409, detail="El correo ya pertenece a otro cliente de este taller.")
    repos.customers.update(customer, payload.full_name, payload.phone, str(payload.email).lower())
    repos.commit()
    return {"id": customer.id, "full_name": customer.name, "phone": customer.phone, "email": customer.email, "is_active": customer.is_active, "message": "Cliente actualizado correctamente."}


@router.patch("/workshops/{workshop_id}/customers/{customer_id}/status", dependencies=[Depends(require_csrf)])
def update_customer_status(
    workshop_id: str,
    customer_id: str,
    payload: CustomerStatusInput,
    membership: Membership = Depends(require_roles("admin", "reception")),
    repos: Repositories = Depends(get_repositories),
):
    if membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    customer = repos.customers.get_by_id(workshop_id, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="No encontramos el cliente en este taller.")
    repos.customers.set_active(customer, payload.is_active)
    repos.commit()
    return {"id": customer.id, "is_active": customer.is_active, "message": "Cliente reactivado correctamente." if payload.is_active else "Cliente deshabilitado correctamente."}


def vehicle_view(vehicle: Vehicle) -> dict:
    return {
        "id": vehicle.id,
        "system_vin": vehicle.system_vin,
        "workshop_id": vehicle.workshop_id,
        "customer_id": vehicle.customer_id,
        "vin": vehicle.vin,
        "plate": vehicle.plate,
        "brand": vehicle.brand,
        "model": vehicle.model,
        "year": vehicle.year,
        "version": vehicle.version,
        "color": vehicle.color,
        "mileage": vehicle.mileage,
        "technician_id": vehicle.technician_id,
        "is_active": vehicle.is_active,
        "customer_name": vehicle.customer.name if vehicle.customer else None,
        "customer_email": vehicle.customer.email if vehicle.customer else None,
        "customer_phone": vehicle.customer.phone if vehicle.customer else None,
        "customer_is_active": vehicle.customer.is_active if vehicle.customer else False,
        "photo_url": f"/api/workshops/{vehicle.workshop_id}/vehicles/{vehicle.id}/photo" if vehicle.photo_content_type else None,
    }


@router.get("/workshops/{workshop_id}/vehicles")
def list_workshop_vehicles(
    workshop_id: str,
    membership: Membership = Depends(require_roles("admin", "reception")),
    repos: Repositories = Depends(get_repositories),
):
    if membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    return [vehicle_view(vehicle) for vehicle in repos.vehicles.list_by_workshop(workshop_id)]


@router.get("/workshops/{workshop_id}/vehicles/{vehicle_id}/photo")
def get_vehicle_photo(
    workshop_id: str,
    vehicle_id: str,
    user: User = Depends(current_user),
    membership: Membership = Depends(require_roles("admin", "reception", "customer")),
    repos: Repositories = Depends(get_repositories),
):
    if membership.workshop_id != workshop_id:
        raise HTTPException(status_code=404, detail="No encontramos la foto de este vehículo.")
    vehicle = repos.vehicles.get_by_id(workshop_id, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="No encontramos la foto de este vehículo.")
    if membership.role.code == "customer" and (
        not vehicle.customer
        or not vehicle.customer.email
        or vehicle.customer.email.lower() != user.email.lower()
    ):
        raise HTTPException(status_code=404, detail="No encontramos la foto de este vehículo.")
    photo = repos.vehicles.get_photo(vehicle.id)
    if not photo:
        raise HTTPException(status_code=404, detail="Este vehículo no tiene una foto registrada.")
    image_data, content_type = photo
    return Response(
        content=image_data,
        media_type=content_type,
        headers={
            "Cache-Control": "private, max-age=3600",
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; sandbox",
        },
    )


@router.patch("/workshops/{workshop_id}/vehicles/{vehicle_id}/status", dependencies=[Depends(require_csrf)])
def update_vehicle_status(
    workshop_id: str,
    vehicle_id: str,
    payload: CustomerStatusInput,
    membership: Membership = Depends(require_roles("admin", "reception")),
    repos: Repositories = Depends(get_repositories),
):
    if membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    vehicle = repos.vehicles.get_by_id(workshop_id, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="No encontramos el vehículo en este taller.")
    repos.vehicles.set_active(vehicle, payload.is_active)
    repos.commit()
    return {"id": vehicle.id, "is_active": vehicle.is_active, "message": "Vehículo activado correctamente." if payload.is_active else "Vehículo deshabilitado correctamente."}


@router.patch("/workshops/{workshop_id}/vehicles/{vehicle_id}", dependencies=[Depends(require_csrf)])
def update_vehicle(
    workshop_id: str,
    vehicle_id: str,
    payload: VehicleUpdateInput,
    membership: Membership = Depends(require_roles("admin", "reception")),
    repos: Repositories = Depends(get_repositories),
):
    if membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    vehicle = repos.vehicles.get_by_id(workshop_id, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="No encontramos el vehículo en este taller.")
    duplicate_plate = repos.vehicles.find_by_plate(workshop_id, payload.plate, exclude_vehicle_id=vehicle_id)
    if duplicate_plate:
        raise HTTPException(status_code=409, detail="La placa ya está registrada en otro vehículo de este taller.")
    repos.vehicles.update_details(
        vehicle,
        plate=payload.plate,
        brand=payload.brand,
        model=payload.model,
        year=payload.year,
        version=payload.version,
        color=payload.color,
        mileage=payload.mileage,
    )
    repos.commit()
    return {**vehicle_view(vehicle), "message": "Vehículo actualizado correctamente."}


@router.get("/workshops/{workshop_id}/my-vehicles")
def list_my_vehicles(
    workshop_id: str,
    user: User = Depends(current_user),
    membership: Membership = Depends(require_roles("customer")),
    repos: Repositories = Depends(get_repositories),
):
    if membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    return [vehicle_view(vehicle) for vehicle in repos.vehicles.list_by_customer_email(workshop_id, user.email.lower())]


@router.get("/workshops/{workshop_id}/customers/{customer_id}/vehicles")
def list_customer_vehicles(
    workshop_id: str,
    customer_id: str,
    membership: Membership = Depends(require_roles("admin", "reception")),
    repos: Repositories = Depends(get_repositories),
):
    if membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    customer = repos.customers.get_by_id(workshop_id, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="No encontramos el cliente en este taller.")
    return [vehicle_view(vehicle) for vehicle in repos.vehicles.list_by_customer(workshop_id, customer_id)]


@router.post("/workshops/{workshop_id}/customers/{customer_id}/vehicles", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_vehicle(
    workshop_id: str,
    customer_id: str,
    payload: VehicleInput,
    membership: Membership = Depends(require_roles("admin", "reception")),
    repos: Repositories = Depends(get_repositories),
):
    if membership.workshop_id != workshop_id:
        raise HTTPException(status_code=403, detail="El taller indicado no corresponde a tu sesión autorizada.")
    customer = repos.customers.get_by_id(workshop_id, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="No encontramos el cliente en este taller.")
    if not customer.is_active:
        raise HTTPException(status_code=409, detail="Solo un cliente activo puede recibir un vehículo.")
    duplicate_vin = repos.vehicles.find_by_vin(payload.vin)
    duplicate_plate = repos.vehicles.find_by_plate(workshop_id, payload.plate)
    if duplicate_vin:
        raise HTTPException(status_code=409, detail="El VIN ya está registrado en el sistema.")
    if duplicate_plate:
        raise HTTPException(status_code=409, detail="La placa ya está registrada en este taller.")
    photo_data, photo_content_type = decode_photo_data_url(payload.photo_data_url)
    vehicle = Vehicle(
        workshop_id=workshop_id,
        customer_id=customer_id,
        vin=payload.vin,
        plate=payload.plate,
        brand=payload.brand,
        model=payload.model,
        year=payload.year,
        version=payload.version,
        color=payload.color,
        mileage=payload.mileage,
        photo_data=photo_data,
        photo_content_type=photo_content_type,
        technician_id=None,
        is_active=True,
    )
    repos.vehicles.add(vehicle)
    repos.commit()
    return {**vehicle_view(vehicle), "message": "Vehículo registrado y asociado al cliente correctamente."}
