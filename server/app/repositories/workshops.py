from sqlalchemy.orm import Session, joinedload

from shared.db.models import Membership, Role, Workshop


class WorkshopRepository:
    """Persistencia de talleres y pertenencias, sin decisiones de negocio."""

    def __init__(self, db: Session):
        self.db = db

    def list_user_memberships(self, user_id: str) -> list[Membership]:
        return (
            self.db.query(Membership)
            .options(joinedload(Membership.role), joinedload(Membership.workshop))
            .filter(Membership.user_id == user_id, Membership.is_active.is_(True))
            .all()
        )

    def get_membership(self, user_id: str, workshop_id: str) -> Membership | None:
        return (
            self.db.query(Membership)
            .options(joinedload(Membership.role), joinedload(Membership.workshop))
            .filter(Membership.user_id == user_id, Membership.workshop_id == workshop_id, Membership.is_active.is_(True))
            .first()
        )

    def get_any_membership(self, user_id: str, workshop_id: str) -> Membership | None:
        return (
            self.db.query(Membership)
            .options(joinedload(Membership.role), joinedload(Membership.workshop))
            .filter(Membership.user_id == user_id, Membership.workshop_id == workshop_id, Membership.is_active.is_(True))
            .first()
        )

    def list_admin_workshops(self, user_id: str) -> list[Membership]:
        return (
            self.db.query(Membership)
            .options(joinedload(Membership.role), joinedload(Membership.workshop))
            # El JOIN explícito permite ordenar por Workshop.name. Sin él,
            # joinedload crea un alias y SQLite no encuentra `workshops.name`
            # en la cláusula ORDER BY.
            .join(Membership.workshop)
            .filter(Membership.user_id == user_id, Membership.is_active.is_(True), Membership.role.has(code="admin"))
            .order_by(Workshop.name)
            .all()
        )

    def find_by_name(self, name: str, exclude_id: str | None = None) -> Workshop | None:
        query = self.db.query(Workshop).filter(Workshop.name.ilike(name))
        if exclude_id:
            query = query.filter(Workshop.id != exclude_id)
        return query.first()

    def find_by_tax_id(self, tax_id: str, exclude_id: str | None = None) -> Workshop | None:
        query = self.db.query(Workshop).filter(Workshop.tax_id == tax_id)
        if exclude_id:
            query = query.filter(Workshop.id != exclude_id)
        return query.first()

    def get_photo(self, workshop_id: str) -> tuple[bytes, str] | None:
        photo = (
            self.db.query(Workshop.photo_data, Workshop.photo_content_type)
            .filter(Workshop.id == workshop_id)
            .first()
        )
        if not photo or not photo.photo_data or not photo.photo_content_type:
            return None
        return photo.photo_data, photo.photo_content_type

    def add(self, workshop: Workshop) -> Workshop:
        self.db.add(workshop)
        self.db.flush()
        return workshop

    def add_membership(self, membership: Membership) -> Membership:
        self.db.add(membership)
        self.db.flush()
        return membership

    def find_membership(self, user_id: str, workshop_id: str) -> Membership | None:
        return self.db.query(Membership).filter(Membership.user_id == user_id, Membership.workshop_id == workshop_id).first()

    def list_workshop_memberships(self, workshop_id: str) -> list[Membership]:
        return (
            self.db.query(Membership)
            .options(joinedload(Membership.user), joinedload(Membership.role))
            .filter(Membership.workshop_id == workshop_id)
            .order_by(Membership.is_active.desc())
            .all()
        )

    def get_membership_by_id(self, workshop_id: str, membership_id: str) -> Membership | None:
        return (
            self.db.query(Membership)
            .options(joinedload(Membership.user), joinedload(Membership.role))
            .filter(Membership.id == membership_id, Membership.workshop_id == workshop_id)
            .first()
        )

    def count_active_memberships_by_role(self, workshop_id: str, role_id: str) -> int:
        return (
            self.db.query(Membership)
            .filter(Membership.workshop_id == workshop_id, Membership.role_id == role_id, Membership.is_active.is_(True))
            .count()
        )

    def set_role(self, membership: Membership, role: Role) -> None:
        membership.role_id = role.id

    def set_active(self, membership: Membership, is_active: bool) -> None:
        membership.is_active = is_active

    def update_workshop(self, workshop: Workshop, name: str, tax_id: str, state: str, municipality: str, locality: str, colony: str, postal_code: str) -> None:
        workshop.name = name
        workshop.tax_id = tax_id
        workshop.state = state
        workshop.municipality = municipality
        workshop.locality = locality
        workshop.colony = colony
        workshop.postal_code = postal_code

    def set_workshop_active(self, workshop: Workshop, is_active: bool) -> None:
        workshop.is_active = is_active
