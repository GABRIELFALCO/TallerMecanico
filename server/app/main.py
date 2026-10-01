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

from app.config import get_settings
from app.routers import auth, workshops
from shared.db.database import Base, SessionLocal, engine
from shared.db.models import Role

settings = get_settings()
DEFAULT_ROLES = [
    ("owner", "Propietario", "Control total del taller y sus usuarios."),
    ("manager", "Gerente", "Opera el taller y administra clientes."),
    ("reception", "Recepción", "Registra clientes y gestiona la recepción."),
    ("mechanic", "Mecánico", "Consulta información operativa asignada."),
]


def seed_roles() -> None:
    with SessionLocal() as db:
        for code, name, description in DEFAULT_ROLES:
            if not db.query(Role).filter(Role.code == code).first():
                db.add(Role(code=code, name=name, description=description))
        db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
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
