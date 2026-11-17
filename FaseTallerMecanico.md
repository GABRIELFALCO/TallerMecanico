# Fase 3 — Alta y administración del taller mecánico

> Estado: 🟡 Implementación lista; pendiente de prueba funcional  
> Fecha: 6 de noviembre de 2026  
> Acceso: únicamente `admin`

## Objetivo

Permitir que un administrador registre y administre sus talleres como empresas identificadas por nombre comercial y RFC, evitando duplicados y reduciendo errores de captura.

## Alcance implementado

- Pestaña independiente **Talleres** en el menú lateral.
- Alta de un taller con nombre comercial, RFC y ubicación postal obligatoria.
- Consulta de código postal mediante API pública y selección guiada de estado, municipio, localidad y colonia.
- Línea de progreso visual para completar identidad fiscal, ubicación y confirmación.
- Validación de RFC de 12 o 13 caracteres mediante expresión regular.
- Normalización automática del RFC a mayúsculas.
- Prevención de nombres duplicados sin distinguir mayúsculas/minúsculas.
- Prevención de RFC duplicado.
- Edición de nombre y RFC.
- Activación y deshabilitación sin eliminación física.
- Resumen de talleres registrados, activos y deshabilitados.
- Tabla administrativa de empresas.
- Tarjetas de resumen y administración con separación uniforme, ajustada para escritorio y móvil.
- Carga opcional de foto JPG, PNG o WebP de hasta 5 MB durante el alta, con vista previa.
- Almacenamiento de la foto en la base de datos, con validación de firma del archivo y acceso protegido por membresía administrativa del taller.
- Vista previa en la tarjeta **Taller seleccionado**, miniatura en la tabla **Mis talleres** y acción **Visualizar** que abre los datos completos del taller.
- Acceso protegido para administradores con taller activo.
- Datos postales persistidos en el taller: estado, municipio, localidad, colonia y código postal.
- Migración de arranque compatible con bases SQLite existentes; agrega las columnas de ubicación sin eliminar talleres.
- Consulta de ubicación encapsulada en el cliente y consumida por los componentes mediante `TallerMecanicoFacade`.

## Reglas estrictas

- Solo `admin` puede crear, editar, activar o deshabilitar talleres.
- El nombre comercial es obligatorio y no puede repetirse.
- El RFC es obligatorio y no puede repetirse.
- En la creación del taller la localidad es opcional; se requieren estado, municipio, colonia y código postal de 5 dígitos.
- En la edición del taller la localidad puede quedar vacía; estado, municipio, colonia y código postal continúan siendo obligatorios.
- En el registro inicial de cuenta y al administrar un taller existente, la localidad también es opcional.
- El código postal se valida y se consulta contra el catálogo postal antes de guardar.
- Las fotos opcionales admiten únicamente JPEG, PNG o WebP, no superan 5 MB y se validan por contenido binario además del tipo declarado por el navegador.
- La foto se sirve por una ruta autenticada y solo el administrador activo del taller puede consultarla.
- El RFC se guarda normalizado en mayúsculas.
- El RFC aceptado debe cumplir: `^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$`.
- No existe eliminación física del taller.
- Un taller deshabilitado conserva sus datos e historial.
- Las operaciones de escritura requieren sesión válida y CSRF.
- La API postal se utiliza únicamente para ayudar a capturar la ubicación; el backend valida nuevamente los cinco campos antes de guardar.
- El frontend debe consumir exclusivamente `TallerMecanicoFacade`.
- El backend debe usar `WorkshopRepository`, nunca consultas directas en el router.

## Flujo de alta

1. El administrador abre el menú lateral.
2. Selecciona **Talleres**.
3. Introduce el nombre comercial.
4. Introduce el RFC con ayuda del ejemplo y validación de formato.
5. Introduce el código postal y consulta la ubicación.
6. Selecciona estado, municipio, localidad y colonia.
7. El sistema normaliza el RFC y valida la ubicación.
8. El sistema valida que nombre y RFC no existan.
9. El administrador confirma el alta.
10. Si eligió una foto, el sistema comprueba formato y tamaño antes de guardarla.
11. El taller queda activo y asociado al administrador.

## Acciones administrativas

| Acción | Resultado |
|---|---|
| Crear | Alta de taller activo. |
| Editar | Actualiza nombre y RFC después de validar duplicados. |
| Deshabilitar | Bloquea operación sin eliminar información. |
| Reactivar | Vuelve a habilitar un taller existente. |

## Ubicación postal

El formulario solicita el código postal mexicano y consulta un catálogo postal para proponer el estado, municipio, localidad y colonias disponibles. El administrador debe revisar las selecciones antes de confirmar. La ubicación queda asociada al taller y también se solicita al registrar la cuenta que crea su primer taller.

## Mensajes esperados

| Situación | Mensaje |
|---|---|
| RFC inválido | “Usa un RFC válido de 12 o 13 caracteres.” |
| Nombre duplicado | “Ya existe un taller con ese nombre.” |
| RFC duplicado | “Ya existe un taller con ese RFC.” |
| Usuario no admin | “Solo un administrador puede administrar talleres.” |
| Alta correcta | “Taller creado y asociado correctamente.” |
| Deshabilitación correcta | “Taller deshabilitado correctamente.” |

## Criterios de aceptación

- [x] Existe una pestaña independiente para talleres.
- [x] El alta permite adjuntar una foto opcional, muestra vista previa y limita el tamaño y los formatos.
- [x] La foto se conserva al reiniciar la aplicación y se expone mediante una ruta protegida.
- [x] La tarjeta de taller seleccionado muestra la foto y los datos generales.
- [x] La tabla incluye miniatura y acción **Visualizar** con foto y datos completos.
- [x] Solo `admin` puede acceder funcionalmente.
- [x] El nombre es obligatorio y no se duplica.
- [x] El RFC es obligatorio y se valida en frontend y backend.
- [x] La localidad es opcional en alta y edición; los demás campos postales siguen siendo obligatorios.
- [x] La pantalla ofrece consulta de CP, catálogos de ubicación y línea de progreso.
- [x] La ubicación se guarda junto con el taller y se puede actualizar desde la administración.
- [x] Los talleres existentes se conservan durante la migración de columnas de domicilio.
- [x] Se puede editar el taller.
- [x] Se puede deshabilitar y reactivar.
- [x] Las altas, ediciones y cambios de estado muestran un diálogo de confirmación antes de guardar.
- [x] No existe eliminación física.
- [x] Se mantienen Facade y Repository como patrones obligatorios.
- [x] La aplicación muestra estados y mensajes claros.
- [ ] Pruebas funcionales de RFC y duplicados.
- [ ] Pruebas automatizadas de autorización y estado.
- [ ] Pruebas funcionales de carga, visualización y rechazo de fotos inválidas.

## Ajuste del 14 de noviembre de 2026

- Permite omitir localidad en el alta y en su indicador de progreso.
- Agrega o reemplaza la foto desde la edición del taller; conserva la anterior si no se envía una nueva.
- Mantiene autorización por membresía activa de administrador del taller y protección CSRF.
- Valida `photo_data_url` opcional en `PATCH /api/admin/workshops/{workshop_id}`: JPEG, PNG o WebP, hasta 5 MB.
- Rechaza cambios sin membresía administrativa con HTTP 403 y fotos inválidas con HTTP 422.
- Verifica seis pruebas unitarias en `server/tests/test_workshop_changes.py`, compilación Python y build Vue.
- Deja pendiente la comprobación visual interactiva y las pruebas HTTP de extremo a extremo.
