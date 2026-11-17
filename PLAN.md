# Plan de desarrollo — Taller Mecánico

> Actualizado: 6 de noviembre de 2026  
> Convención: ✅ completado · 🟡 en curso / pendiente de validación · ⬜ pendiente

## Estado actual

| Área | Proceso / tarea | Estado | Resultado actual | Siguiente acción |
|---|---|:---:|---|---|
| Base | Estructura `client` / `server` / `shared` | ✅ | Proyecto separado por responsabilidades. | Mantener esta organización al agregar módulos. |
| Base | SPA con Vue 3, TypeScript y Vite | ✅ | Interfaz de acceso y panel inicial disponibles. | Agregar rutas y vistas por módulo. |
| Arquitectura | Facade estricto en frontend | ✅ | Los componentes consumen `TallerMecanicoFacade`; el acceso HTTP queda encapsulado. | Crear fachadas refinadas por módulo cuando crezca el subsistema. |
| Arquitectura | Repository estricto en backend | ✅ | Routers y dependencias consumen repositorios; las consultas SQLAlchemy están aisladas. | Añadir interfaces/protocolos y pruebas de repositorios. |
| Documentación | Skill de documentación del backend relacionada con el orquestador | ✅ | Skill creada y enlazada desde `sourse/spec/skills/orquestador.md`; define fuentes, reglas, validaciones y formato de entrega. | Aplicarla en cada cambio documental del backend. |
| Documentación | Skill de coordinación `$orquestador` | ✅ | Skill global instalada en `C:\Users\famg0\.codex\skills\orquestador` y definición canónica en `sourse/spec/skills/orquestador.md`. | Invocarla directamente en Codex con `$orquestador`. |
| Base | API REST con FastAPI | ✅ | API en `http://localhost:8000`; health check disponible. | Añadir pruebas automáticas. |
| Base | Base de datos y modelos SQLAlchemy | ✅ | SQLite local configurado; preparado para `DATABASE_URL`. | Migrar a PostgreSQL para producción. |
| Seguridad | Hash de contraseñas Argon2id | ✅ | Contraseñas nunca se guardan en texto plano. | Definir política de cambio / recuperación. |
| Seguridad | Validación de contraseña | ✅ | Mínimo 12 caracteres, mayúscula, minúscula y número. | Añadir medidor visual de seguridad. |
| Seguridad | Sesiones autenticadas y revocables | ✅ | Cookie HttpOnly, expiración y registro de sesiones. | Agregar cierre de todas las sesiones. |
| Seguridad | Protección CSRF y CORS | ✅ | Operaciones de escritura protegidas; origen del frontend restringido. | Configurar HTTPS y `COOKIE_SECURE=true` en producción. |
| Identidad | Registro de cuenta | ✅ | Crea cuenta, taller inicial y rol de administrador. | Implementar verificación de correo real. |
| Identidad | Inicio y cierre de sesión | ✅ | Flujo de login, mensajes de error y cierre de sesión. | Añadir recuperación de contraseña. |
| Roles | Roles iniciales | ✅ | Administrador, recepcionista, asesor de servicio, técnico, cliente y sistema. | Definir permisos granulares por acción. |
| Roles | Asignación de roles por taller | ✅ | Solo el administrador autoriza cuentas existentes; la pantalla independiente ya está disponible. | Añadir baja, reactivación y listado de personal. |
| Roles | Administración de roles | 🟡 | Tabla por taller, edición de rol y deshabilitación/reactivación sin eliminación física. | Completar pruebas funcionales y automatizadas. |
| Multinegocio | Múltiples talleres por cuenta | ✅ | Una misma cuenta puede crear y alternar talleres. | Añadir edición, activación y desactivación de talleres. |
| Talleres | Alta y administración del taller mecánico | 🟡 | Alta exclusiva de admin, RFC y ubicación postal obligatorios con localidad opcional, carga y reemplazo opcional de foto en alta/edición solo por admin del taller, vista previa en tarjeta, miniatura/visualización completa desde la tabla, tarjetas con espacios uniformes y responsivos, nombre/RFC únicos, edición y deshabilitación sin eliminación física. | Completar pruebas funcionales de fotos, ubicación, duplicados y migración de datos antiguos. |
| Clientes | Registro validado y activación de cuenta | 🟡 | Ficha de cliente activa vinculada a acceso por RFC del taller, correo normalizado sin distinguir mayúsculas, y nombre coincidente; la activación no duplica la ficha. | Validar con el cliente del reporte que se use el RFC del mismo taller; completar pruebas funcionales y automatizadas. |
| Clientes | Actualizar, desactivar y detectar duplicados | 🟡 | `PlanActualizarCliente.md` implementado: pantalla, tabla alineada y desplazable en móvil, modal, contexto del taller en solo lectura, validaciones, eliminación suave y `CustomerRepository`. | Completar pruebas funcionales y automatizadas. |
| Vehículos | Registro, administración, consulta y actualización de vehículos | 🟡 | `PlanRegistroVehiculo.md` y `PlanActualizarVehiculo.md` implementados: alta desde cliente activo con foto opcional JPG/PNG/WebP (máx. 5 MB), tabla de administración con modal **Visualizar** y modal de edición, vista `customer` con tabla alineada y desplazamiento horizontal adaptable, VIN del sistema generado y VIN del automóvil protegido como solo lectura durante la actualización. | Validar la carga, visualización de detalle y fotos con la API y una base SQLite existente; completar pruebas funcionales y automatizadas. |
| Interfaz | Mensajes de éxito, error y confirmación | ✅ | Avisos con título, icono, cierre manual y progreso temporal; diálogos propios para confirmar altas, asignaciones, cambios y deshabilitaciones de talleres, roles, clientes y vehículos. | Mantener el mismo patrón en nuevos módulos y acciones sensibles. |
| Interfaz | Diseño responsivo y temas claro/oscuro | 🟡 | SPA adaptable a móvil, tableta y escritorio; tema persistido en el navegador mediante `localStorage`. Compilación y arranque verificados. | Validar visualmente en navegadores y dispositivos reales. |
| Calidad | Compilación y pruebas automatizadas | 🟡 | Aplicación iniciada manualmente; faltan pruebas de API y UI. | Añadir Pytest y pruebas de componentes. |
| Entorno | `uv` global | ✅ | `uv 0.12.21` instalado globalmente. | Migrar dependencias del backend a `uv` si se decide. |

## Próximos módulos

| Prioridad | Módulo | Alcance inicial | Estado |
|:---:|---|---|:---:|
| 1 | Administración de personal | Invitación, asignación de rol, baja y reactivación de usuarios por taller. | 🟡 |
| 2 | Clientes | Catálogo, búsqueda, edición, historial y vehículos del cliente. | 🟡 |
| 3 | Vehículos | Placa, VIN, marca, modelo, año, kilometraje y relación con cliente. | 🟡 |
| 4 | Órdenes de servicio | Diagnóstico, evidencias, mano de obra, estatus y responsables. | ⬜ |
| 5 | Cotizaciones | Refacciones, servicios, impuestos, autorización del cliente y conversión a orden. | ⬜ |
| 6 | Inventario | Refacciones, existencias, proveedores, entradas, salidas y alertas de mínimo. | ⬜ |
| 7 | Caja y pagos | Anticipos, pagos, facturación y cierre diario. | ⬜ |
| 8 | Agenda y recepción | Citas, recepción del vehículo y recordatorios. | ⬜ |
| 9 | Reportes | Ventas, órdenes, productividad, clientes e inventario. | ⬜ |
| 10 | Producción | PostgreSQL, migraciones, HTTPS, copias de seguridad, monitoreo y despliegue. | ⬜ |

## Caso de uso actual: Registro de Clientes

| Tarea | Estado |
|---|:---:|
| Solo `reception` o `admin` pueden registrar clientes | ✅ |
| Verificar que el usuario tenga membresía activa en el taller | ✅ |
| Verificar que el taller esté activo | ✅ |
| Capturar nombre completo y exigir nombre + apellido | ✅ |
| Validar formato de nombre, teléfono y correo | ✅ |
| Exigir al menos dos medios de contacto: teléfono y correo | ✅ |
| Alertar duplicado por teléfono dentro del taller | ✅ |
| Alertar duplicado por correo dentro del taller | ✅ |
| Solicitar confirmación explícita antes de crear | ✅ |
| No crear registros automáticamente al detectar datos incompletos o duplicados | ✅ |
| Solo `admin` puede asignar roles | ✅ |
| Admin puede asignar roles desde el panel | ✅ |
| Agregar pruebas automatizadas del caso de uso | ⬜ |
| Crear listado y búsqueda de clientes | ✅ |
| Administración de clientes para casos de uso 3, 4 y 5 | 🟡 |
| Registro de vehículos para caso de uso 6 | 🟡 |

## Criterio para cerrar un módulo

Un módulo se marca como ✅ únicamente cuando cumple estos puntos:

- La interfaz permite completar el flujo principal.
- La API valida datos, autorización y aislamiento por taller.
- Los errores y confirmaciones son comprensibles para el usuario.
- Se agregaron pruebas proporcionales al cambio.
- La funcionalidad está documentada en este archivo.
