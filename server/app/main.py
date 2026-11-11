from contextlib import asynccontextmanager
from pathlib import Path
import sys

# Cuando Uvicorn usa `--app-dir server`, añade `server` al import path, pero no
# la raíz del repositorio. La carpeta `shared` vive en esa raíz.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text

from app.config import get_settings
from app.repositories import Repositories
from app.repositories.auth import AuthRepository
from app.repositories.customers import CustomerRepository
from app.repositories.roles import RoleRepository
from app.repositories.workshops import WorkshopRepository
from app.repositories.vehicles import VehicleRepository
from app.routers import auth, workshops
from shared.db.database import Base, SessionLocal, engine

settings = get_settings()
DEFAULT_ROLES = [
    ("admin", "Administrador", "Administra la operación y los registros del taller."),
    ("reception", "Recepcionista", "Registra clientes y gestiona la recepción."),
    ("service_advisor", "Asesor de servicio", "Da seguimiento a servicios y comunicación con clientes."),
    ("technician", "Técnico", "Consulta y actualiza información técnica asignada."),
    ("customer", "Cliente", "Consulta información propia y autorizada."),
    ("system", "Sistema", "Cuenta técnica para procesos internos del sistema."),
]


def seed_roles() -> None:
    with SessionLocal() as db:
        repos = Repositories(
            auth=AuthRepository(db),
            customers=CustomerRepository(db),
            roles=RoleRepository(db),
            workshops=WorkshopRepository(db),
            vehicles=VehicleRepository(db),
        )
        for code, name, description in DEFAULT_ROLES:
            repos.roles.add_if_missing(code, name, description)
        repos.roles.migrate_legacy_codes({
            "owner": "admin",
            "manager": "service_advisor",
            "mechanic": "technician",
        })
        repos.commit()


def ensure_workshop_columns() -> None:
    """Añade ubicación y foto sin borrar talleres existentes en SQLite."""
    workshop_columns = {
        "state": "VARCHAR(120)",
        "municipality": "VARCHAR(120)",
        "locality": "VARCHAR(120)",
        "colony": "VARCHAR(120)",
        "postal_code": "VARCHAR(5)",
        "photo_data": "BYTEA" if engine.dialect.name == "postgresql" else "BLOB",
        "photo_content_type": "VARCHAR(32)",
    }
    existing_columns = {column["name"] for column in inspect(engine).get_columns("workshops")}
    missing_columns = workshop_columns.keys() - existing_columns
    if not missing_columns:
        return
    with engine.begin() as connection:
        for column in missing_columns:
            connection.execute(text(f"ALTER TABLE workshops ADD COLUMN {column} {workshop_columns[column]}"))


def ensure_vehicle_columns() -> None:
    """Añade el VIN del sistema y los datos de foto a vehículos existentes."""
    vehicle_columns = {
        "system_vin": "VARCHAR(19)",
        "photo_data": "BYTEA" if engine.dialect.name == "postgresql" else "BLOB",
        "photo_content_type": "VARCHAR(32)",
    }
    existing_columns = {column["name"] for column in inspect(engine).get_columns("vehicles")}
    missing_columns = vehicle_columns.keys() - existing_columns
    if missing_columns:
        with engine.begin() as connection:
            for column in missing_columns:
                connection.execute(text(f"ALTER TABLE vehicles ADD COLUMN {column} {vehicle_columns[column]}"))
    with engine.begin() as connection:
        connection.execute(text("UPDATE vehicles SET system_vin = 'TM-' || upper(substr(replace(id, '-', ''), 1, 16)) WHERE system_vin IS NULL"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_vehicles_system_vin ON vehicles(system_vin)"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_workshop_columns()
    ensure_vehicle_columns()
    seed_roles()
    yield


app = FastAPI(title="Taller Mecánico API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    first_error = exc.errors()[0]
    message = first_error.get("msg", "Revisa los datos enviados.")
    return JSONResponse(status_code=422, content={"detail": f"Datos no válidos: {message}"})


@app.get("/health", tags=["Estado"])
def health():
    return {"status": "ok", "service": "Taller Mecánico API"}


app.include_router(auth.router, prefix="/api")
app.include_router(workshops.router, prefix="/api")
