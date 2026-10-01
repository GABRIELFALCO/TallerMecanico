# Taller Mecánico

Base de un sistema multinegocio para talleres mecánicos.

## Estructura

- `client/`: SPA en Vue 3, TypeScript y Vite.
- `server/`: API REST en FastAPI.
- `shared/`: modelos y acceso a base de datos compartidos por el backend.

## Inicio rápido

En una terminal, con Python 3.11+ y Node 20+:

```powershell
cd C:\ProyectoTaller
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r server\requirements.txt
Copy-Item server\.env.example server\.env
uvicorn app.main:app --app-dir server --reload --port 8000
```

En otra terminal:

```powershell
cd client
npm install
npm run dev
```

Abra `http://localhost:5173`. La API queda disponible en `http://localhost:8000/docs`.

> Antes de producción, configure una clave `JWT_SECRET` aleatoria y `COOKIE_SECURE=true`; use PostgreSQL mediante `DATABASE_URL`.

## Seguridad y primer alcance

- Las contraseñas se validan (12 caracteres, mayúscula, minúscula y número) y se almacenan exclusivamente con **Argon2id**.
- La sesión está en una cookie `HttpOnly`, expira, puede revocarse y se contrasta contra la base de datos en cada solicitud.
- Los cambios de estado exigen token CSRF y la API restringe CORS al origen configurado.
- Cada dato de cliente pertenece a un taller. La creación comprueba que el taller esté activo y que el rol sea `owner`, `manager` o `reception`.
- Al iniciar, se crean los roles: propietario, gerente, recepción y mecánico. El propietario puede asignar uno a cuentas existentes con `POST /api/workshops/{workshop_id}/members`.
