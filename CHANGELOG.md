# Changelog

Todos los cambios importantes del proyecto se registran aquí. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

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
