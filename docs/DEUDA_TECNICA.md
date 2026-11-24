# Diagnóstico de deuda técnica

Revisión del repositorio realizada sobre la línea base **v1.0.0** (fecha: 2026-11-23). Cada deuda tiene evidencia verificada en el código (`ruta:línea`, número de línea medido sobre `main` en el momento del diagnóstico; el DT-01 se refiere a la versión previa a su corrección).

## Tabla de deudas

| ID | Deuda técnica | Impacto | Riesgo | Prioridad | Acción propuesta |
| --- | --- | --- | --- | --- | --- |
| DT-01 | Código duplicado: el componente `Modal` copiado 4 veces y sin accesibilidad | Medio | Bajo | Media | Refactorizar a un componente único y accesible |
| DT-02 | Configuración insegura por defecto: `DEBUG=True`, clave de desarrollo y CORS abierto si falta `.env` | Alto | Alto | Crítica | Valores por defecto seguros; exigir `SECRET_KEY`; CORS abierto solo con `DEBUG` explícito |
| DT-03 | Ausencia de pruebas y de linter en el frontend | Alto | Alto | Alta | Incorporar ESLint (con `react-hooks`) y Vitest con pruebas de servicios y utilidades |
| DT-04 | Roles y recursos del sistema sin protección (cualquiera con el recurso `RBAC` puede borrarlos o renombrarlos) | Alto | Alto | Alta | Bloquear edición y borrado de roles protegidos y la autoedición de roles |
| DT-05 | Consultas N+1 en listados (`get_mi_rol` por finca; roles y recursos por usuario en el panel RBAC) | Medio | Medio | Media | `Subquery`/`prefetch_related` y pruebas con `assertNumQueries` |
| DT-06 | Código duplicado: el bloque que arma el mensaje de error de la API está repetido en 5 lugares | Medio | Medio | Media | Extraer una utilidad `utils/apiError.js` |
| DT-07 | Manejo de errores inadecuado: `catch` vacíos y promesas sin `catch` (la carga falla sin avisar) | Medio | Medio | Media | Mostrar el error al usuario y manejar la carga fallida |
| DT-08 | Funciones extensas: componentes de más de 400 líneas que mezclan estado, lógica y presentación | Medio | Bajo | Baja | Dividir en componentes y hooks |
| DT-09 | Falta de documentación: README desactualizado y sin `CONTRIBUTING.md` ni `CHANGELOG.md` | Medio | Medio | Media | Reescribir el README y crear las guías |
| DT-10 | Código obsoleto: funciones y datos sin uso | Bajo | Bajo | Baja | Eliminarlos o retirar el alias temporal |

## Evidencia

**DT-01.** Cuatro copias idénticas de `function Modal` en `Bovinos.jsx`, `Fincas.jsx`, `Invitaciones.jsx` y `Membresias.jsx`, sin `role="dialog"`, `aria-modal` ni cierre con Escape; solo `Bovinos` limitaba la altura (`max-h-[90vh]`).

**DT-02.** `backend/config/settings.py:14` (`DEBUG = leer_bool("DEBUG", True)`), `:17` (clave `django-insecure-solo-para-desarrollo-local`), `:161` (`CORS_ALLOW_ALL_ORIGINS = True`) y `:164` (`CORS_ALLOW_CREDENTIALS = True`, innecesario porque la autenticación usa el header `Authorization`). Si falta el `.env`, el sistema arranca así.

**DT-03.** `frontend/package.json:5-9`: solo `dev`, `build`, `preview` y `measure:api`. No hay ESLint, Prettier ni Vitest, y ningún archivo `*.test.*`. Los 108 tests de Django cubren solo el backend.

**DT-04.** `backend/apps/rbac/views.py:31-40`: `VistaRoles` y `VistaRecursos` son `ModelViewSet` completos protegidos solo por el recurso `RBAC`; no distinguen los roles del sistema (`SUPR`, `PROP`, `ADMI`, `OPER`), así que se pueden borrar (con CASCADE sobre las asignaciones) o renombrar.

**DT-05.** `backend/apps/farms/serializers.py:34`: `get_mi_rol` consulta `Membresia` una vez por finca de la página. `backend/apps/rbac/views.py:53`: `roles_y_recursos_usuario(usuario)` se invoca por cada usuario del listado. No hay `assertNumQueries` en las pruebas.

**DT-06.** El bucle `for (const key in data)` que une los mensajes del backend aparece en `Fincas.jsx:171`, `Invitaciones.jsx:106` y `:147`, `Bovinos.jsx:144` y `Membresias.jsx:128`; además `RbacAdmin.jsx:32` (`messageFrom`) es una variante del mismo helper.

**DT-07.** `Fincas.jsx:103` (`.catch(() => {})`: si falla la carga se muestra «no tienes fincas»); `Bovinos.jsx:73` (`getRazas().then(...)` sin `catch`: el select queda vacío sin mensaje); `AuthContext.jsx:104` borra la sesión ante cualquier error al cargar el perfil, incluso un fallo de red transitorio.

**DT-08.** `Bovinos()` (`Bovinos.jsx:31-439`, ~408 líneas) y `RbacAdmin()` (`RbacAdmin.jsx:45-451`, ~406 líneas); `Fincas()` e `Invitaciones()` superan las 300 líneas.

**DT-09.** El `README.md` anterior decía que `frontend/` estaba «vacío, sin framework elegido» cuando ya tenía React con más de 10 páginas, y no mencionaba RBAC, correo ni la landing. No existían `CONTRIBUTING.md`, `CHANGELOG.md` ni plantillas en `.github/`.

**DT-10.** `frontend/src/services/authService.js:3` exporta `login`, que ningún archivo usa (Login y Signup llaman a `api.post` directamente); `backend/apps/rbac/services.py:159` mantiene el alias temporal `tiene_recurso`; `backend/apps/common/testing.py:37` incluye códigos de recurso (`RAZA`, `DISP`, `MODI`, `TIPO`) que `seed_rbac` ya considera obsoletos.

## Estado tras el ciclo de mantenimiento (versión 1.1.0)

| ID | Estado | Cómo |
| --- | --- | --- |
| DT-01 | **Corregida** | Issue [#9](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/9), PR [#15](https://github.com/Yuri-ofc/Ganaderia_Colaborative/pull/15): `components/Modal.jsx` único y accesible |
| DT-09 | **Corregida** | Issue [#16](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/16), PR [#17](https://github.com/Yuri-ofc/Ganaderia_Colaborative/pull/17): README, `CONTRIBUTING.md`, `CHANGELOG.md`, plantillas y `docs/` |
| DT-02 | Pendiente | Issue [#11](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/11) |
| DT-03 | Pendiente | Issue [#12](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/12) |
| DT-04, DT-05, DT-06, DT-07, DT-08, DT-10 | Pendientes | Aún sin issue; ver «Mejoras pendientes» en `docs/EVIDENCIAS.md` |

Además se corrigieron dos errores detectados durante la revisión: el token vencido en el login (#8, PR #13) y la zona horaria de la expiración de invitaciones (#10, PR #14).
