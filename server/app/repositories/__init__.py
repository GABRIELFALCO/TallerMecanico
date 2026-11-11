"""Punto único de composición de repositorios de persistencia."""

from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from shared.db.database import get_db

from .auth import AuthRepository
from .customers import CustomerRepository
from .roles import RoleRepository
from .workshops import WorkshopRepository
from .vehicles import VehicleRepository


@dataclass
class Repositories:
    auth: AuthRepository
    customers: CustomerRepository
    roles: RoleRepository
    workshops: WorkshopRepository
    vehicles: VehicleRepository

    def commit(self) -> None:
        self.auth.db.commit()

    def rollback(self) -> None:
        self.auth.db.rollback()


def get_repositories(db: Session = Depends(get_db)):
    """Composición para FastAPI; los endpoints reciben repositorios, nunca SQLAlchemy."""
    return Repositories(
        auth=AuthRepository(db),
        customers=CustomerRepository(db),
        roles=RoleRepository(db),
        workshops=WorkshopRepository(db),
        vehicles=VehicleRepository(db),
    )
