from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from shared.db.models import Customer


class CustomerRepository:
    """Todas las consultas de clientes quedan aisladas de los routers."""

    def __init__(self, db: Session):
        self.db = db

    def find_by_phone(self, workshop_id: str, phone: str) -> Customer | None:
        return self.db.query(Customer).filter(Customer.workshop_id == workshop_id, Customer.phone == phone).first()

    def find_by_email(self, workshop_id: str, email: str) -> Customer | None:
        normalized_email = email.strip().lower()
        return (
            self.db.query(Customer)
            .filter(
                Customer.workshop_id == workshop_id,
                func.lower(func.trim(Customer.email)) == normalized_email,
            )
            .first()
        )

    def list_by_workshop(self, workshop_id: str) -> list[Customer]:
        return (
            self.db.query(Customer)
            .options(joinedload(Customer.workshop))
            .filter(Customer.workshop_id == workshop_id)
            .order_by(Customer.is_active.desc(), Customer.name)
            .all()
        )

    def get_by_id(self, workshop_id: str, customer_id: str) -> Customer | None:
        return (
            self.db.query(Customer)
            .options(joinedload(Customer.workshop))
            .filter(Customer.workshop_id == workshop_id, Customer.id == customer_id)
            .first()
        )

    def find_by_phone_excluding(self, workshop_id: str, phone: str, customer_id: str) -> Customer | None:
        return (
            self.db.query(Customer)
            .filter(Customer.workshop_id == workshop_id, Customer.phone == phone, Customer.id != customer_id)
            .first()
        )

    def find_by_email_excluding(self, workshop_id: str, email: str, customer_id: str) -> Customer | None:
        normalized_email = email.strip().lower()
        return (
            self.db.query(Customer)
            .filter(
                Customer.workshop_id == workshop_id,
                func.lower(func.trim(Customer.email)) == normalized_email,
                Customer.id != customer_id,
            )
            .first()
        )

    def update(self, customer: Customer, full_name: str, phone: str, email: str) -> None:
        customer.name = full_name
        customer.phone = phone
        customer.email = email

    def set_active(self, customer: Customer, is_active: bool) -> None:
        customer.is_active = is_active

    def add(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.flush()
        return customer
