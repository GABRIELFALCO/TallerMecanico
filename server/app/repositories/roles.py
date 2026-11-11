from sqlalchemy.orm import Session

from shared.db.models import Membership, Role


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, code: str) -> Role | None:
        return self.db.query(Role).filter(Role.code == code).first()

    def list(self) -> list[Role]:
        return self.db.query(Role).order_by(Role.name).all()

    def add_if_missing(self, code: str, name: str, description: str) -> Role:
        role = self.get_by_code(code)
        if role:
            return role
        role = Role(code=code, name=name, description=description)
        self.db.add(role)
        self.db.flush()
        return role

    def migrate_legacy_codes(self, mapping: dict[str, str]) -> None:
        """Mueve membresías de roles retirados antes de eliminar esos roles."""
        for legacy_code, current_code in mapping.items():
            legacy = self.get_by_code(legacy_code)
            current = self.get_by_code(current_code)
            if not legacy or not current:
                continue
            self.db.query(Membership).filter(Membership.role_id == legacy.id).update(
                {Membership.role_id: current.id}, synchronize_session=False
            )
            self.db.delete(legacy)
        self.db.flush()
