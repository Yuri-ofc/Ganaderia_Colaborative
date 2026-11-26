# Changelog

Todos los cambios importantes del proyecto se registran aquí. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [1.2.0] - 2026-11-25

Versión **MINOR**: completa los cinco módulos que solo tenían contrato de API y agrega dos pantallas nuevas. Los endpoints anteriores no cambian de forma incompatible; los `modules/*` que devolvían «módulo en preparación» se reemplazan por rutas reales.

### Agregado
- **Respaldos**: generación de una copia por finca, cifrado opcional con Fernet (`BACKUP_ENCRYPTION_KEY`), huella SHA-256 calculada en el servidor, descarga y restauración completa dentro de una transacción. Nuevo `apps/backups/services.py` y acciones `download` y `restore`.
- **Exportaciones**: endpoint `exports/` que arma CSV (uno o varios en ZIP) o JSON al vuelo con bovinos, mediciones, pesajes, potreros y equipo.
- **Sincronización**: estados de la cola (`pendiente`, `sincronizado`, `conflicto`, `descartado`), detección de conflictos por `(finca, recurso, id_objeto)` y resolución manual reservada a propietario y administrador.
- **Visión computacional**: app `apps.vision` con `CapturaVision` (foto o video) que genera una `Medicion`. La estimación es **simulada** (heurística por edad y sexo, modelo `simulado-v1`) y queda marcada como tal en la API y en la interfaz.
- **Pantallas nuevas**: Mediciones, Pesajes, Visión, Sincronización, Respaldos y Exportaciones, con estados vacíos, validación en vivo del intervalo de confianza, gráfica de evolución en SVG sin dependencias nuevas y confirmación explícita antes de restaurar.
- `frontend/src/services/apiError.js` para leer los errores de la API en un solo sitio.
- Catálogo inicial de medición (`manual-v1` y tres tipos de medida) por migración de datos, para que un usuario sin permisos de staff pueda registrar mediciones.

### Cambiado
- `DEBUG` ahora vale `False` si no se configura; sin `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS` y `CORS_ALLOWED_ORIGINS` son obligatorias y el servidor no arranca si faltan. `CORS_ALLOW_CREDENTIALS` pasa a `False` (deuda técnica DT-02).
- El menú lateral incorpora Mediciones, Pesajes, Visión, Sincronización, Respaldos y Exportaciones; `/recuperacion` deja de ser una entrada propia y su acción vive dentro de Respaldos.
- Las pruebas escriben respaldos y archivos subidos en un directorio temporal, nunca dentro del repositorio.

### Corregido
- Los roles y recursos del sistema ya no se pueden borrar ni renombrar, `SUPR` conserva siempre todos los recursos y nadie puede editar sus propios roles (deuda técnica DT-04).
- Los campos de integridad de un respaldo (tamaño, huella y ruta) los calcula el servidor; el cliente ya no puede enviarlos.
- `seed_rbac` completa las etiquetas que faltaban (`MEDI`, `PESA`, `LOTE`) y repara las que habían quedado guardadas con el propio código.

## [1.1.0] - 2026-11-23

Versión **MINOR**: agrega una mejora compatible hacia atrás (componente `Modal` accesible) e incluye dos correcciones. No hay cambios incompatibles en la API, por lo que MAJOR no cambia. Como incluye funcionalidad nueva, no basta con un incremento PATCH.

### Agregado
- Componente `Modal` único y accesible (`role="dialog"`, `aria-modal`, `aria-labelledby`, cierre con Escape y clic en el fondo, altura máxima con scroll). ([#9], PR [#15])
- `CONTRIBUTING.md`, `CHANGELOG.md`, plantillas de issue y de Pull Request en `.github/`, y `docs/` con el diagnóstico de deuda técnica, las evidencias del mantenimiento y la referencia del backend. ([#16], PR [#17])

### Cambiado
- Los modales de Bovinos, Fincas, Invitaciones y Membresías usan el componente compartido; se eliminaron 4 copias duplicadas (deuda técnica DT-01). ([#9], PR [#15])
- `README.md` reescrito: describe el sistema completo (frontend React, RBAC, landing), requisitos, instalación y ejecución. El detalle de modelos y API pasó a `docs/REFERENCIA_BACKEND.md`. ([#16], PR [#17])

### Corregido
- El login devolvía un token ya vencido y la primera petición respondía 401; ahora se descarta el token vencido y se emite uno nuevo. Se agregaron pruebas de regresión. ([#8], PR [#13])
- La fecha de expiración sugerida al crear una invitación quedaba desplazada por usar UTC en un campo de hora local. ([#10], PR [#14])

## [1.0.0] - 2026-11-23

Línea base del sistema, integrada desde `sexto-commit` (PR [#7]).

### Agregado
- API REST (Django + DRF) de fincas, membresías, invitaciones, razas, potreros, bovinos, movimientos, dispositivos, mediciones, pesajes, respaldos y cola de sincronización, con borrado lógico e identificadores UUID.
- Autenticación por token con caducidad configurable y límites de intentos en login y registro.
- Control de acceso (RBAC) con roles, recursos del menú, **etiquetas editables** y **opciones de menú personalizadas**, administrables desde el panel de la interfaz.
- Frontend en React + Vite + Tailwind: login, registro, paneles por rol, gestión de fincas, bovinos, membresías e invitaciones.
- Landing pública en `/inicio`.

### Corregido
- Login con correo duplicado (cuentas eliminadas con el mismo correo) y actualización de la sesión tras cambios de rol.

[#7]: https://github.com/Yuri-ofc/Ganaderia_Colaborative/pull/7
[#8]: https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/8
[#9]: https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/9
[#10]: https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/10
[#13]: https://github.com/Yuri-ofc/Ganaderia_Colaborative/pull/13
[#14]: https://github.com/Yuri-ofc/Ganaderia_Colaborative/pull/14
[#15]: https://github.com/Yuri-ofc/Ganaderia_Colaborative/pull/15
[#16]: https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/16
[#17]: https://github.com/Yuri-ofc/Ganaderia_Colaborative/pull/17
[1.1.0]: https://github.com/Yuri-ofc/Ganaderia_Colaborative/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Yuri-ofc/Ganaderia_Colaborative/releases/tag/v1.0.0
