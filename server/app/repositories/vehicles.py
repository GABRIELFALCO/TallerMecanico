from sqlalchemy.orm import Session, joinedload

from shared.db.models import Customer, Vehicle


class VehicleRepository:
    """Persistencia de vehículos aislada de los routers."""

    def __init__(self, db: Session):
        self.db = db

    def list_by_customer(self, workshop_id: str, customer_id: str) -> list[Vehicle]:
        return (
            self.db.query(Vehicle)
            .options(joinedload(Vehicle.customer))
            .filter(Vehicle.workshop_id == workshop_id, Vehicle.customer_id == customer_id)
            .order_by(Vehicle.is_active.desc(), Vehicle.created_at.desc())
            .all()
        )

    def list_by_workshop(self, workshop_id: str) -> list[Vehicle]:
        return (
            self.db.query(Vehicle)
            .options(joinedload(Vehicle.customer))
            .filter(Vehicle.workshop_id == workshop_id)
            .order_by(Vehicle.is_active.desc(), Vehicle.created_at.desc())
            .all()
        )

    def list_by_customer_email(self, workshop_id: str, email: str) -> list[Vehicle]:
        return (
            self.db.query(Vehicle)
            .join(Vehicle.customer)
            .options(joinedload(Vehicle.customer))
            .filter(Vehicle.workshop_id == workshop_id, Customer.email == email)
            .order_by(Vehicle.is_active.desc(), Vehicle.created_at.desc())
            .all()
        )

    def find_by_vin(self, vin: str, exclude_vehicle_id: str | None = None) -> Vehicle | None:
        query = self.db.query(Vehicle).filter(Vehicle.vin == vin)
        if exclude_vehicle_id:
            query = query.filter(Vehicle.id != exclude_vehicle_id)
        return query.first()

    def find_by_plate(self, workshop_id: str, plate: str, exclude_vehicle_id: str | None = None) -> Vehicle | None:
        query = self.db.query(Vehicle).filter(Vehicle.workshop_id == workshop_id, Vehicle.plate == plate)
        if exclude_vehicle_id:
            query = query.filter(Vehicle.id != exclude_vehicle_id)
        return query.first()

    def add(self, vehicle: Vehicle) -> Vehicle:
        self.db.add(vehicle)
        self.db.flush()
        return vehicle

    def get_by_id(self, workshop_id: str, vehicle_id: str) -> Vehicle | None:
        return (
            self.db.query(Vehicle)
            .options(joinedload(Vehicle.customer))
            .filter(Vehicle.workshop_id == workshop_id, Vehicle.id == vehicle_id)
            .first()
        )

    def get_photo(self, vehicle_id: str) -> tuple[bytes, str] | None:
        photo = (
            self.db.query(Vehicle.photo_data, Vehicle.photo_content_type)
            .filter(Vehicle.id == vehicle_id)
            .first()
        )
        if not photo or not photo.photo_data or not photo.photo_content_type:
            return None
        return photo.photo_data, photo.photo_content_type

    def set_active(self, vehicle: Vehicle, is_active: bool) -> None:
        vehicle.is_active = is_active

    def update_details(self, vehicle: Vehicle, *, plate: str, brand: str, model: str, year: int, version: str, color: str, mileage: int | None) -> Vehicle:
        vehicle.plate = plate
        vehicle.brand = brand
        vehicle.model = model
        vehicle.year = year
        vehicle.version = version
        vehicle.color = color
        vehicle.mileage = mileage
        self.db.flush()
        return vehicle
