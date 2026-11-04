# Registro de sesión: implementación RBAC

Fecha de trabajo: 30 de octubre de 2026.

## Objetivo atendido

Se implementó un módulo de control de acceso basado en roles (RBAC) para el sistema de gestión ganadera. Incluye la persistencia de roles, recursos y asignaciones; autorización de rutas en servidor; login con roles y permisos; panel de superusuario; y pruebas automatizadas.

El alcance se mantuvo en RBAC y las pantallas de dashboard asociadas. Los módulos funcionales de fincas, bovinos, mediciones, sincronización y respaldos conservan sus reglas de negocio y su aislamiento por finca.

## Fuentes revisadas

Se leyeron completos los siguientes documentos antes de implementar:

1. `Retroalimentacion_E1_01_Ganaderia.pdf` (2 páginas).
2. `Ganaderia_ER_Scrum-1 (1).pdf` (7 páginas).
3. `rbac.jpeg`, diagrama entidad-relación aportado para el RBAC.

También se revisó el código existente de Django REST Framework, React/Vite y las pruebas del repositorio.

### Hallazgos relevantes de los PDFs

- RF-01 exige cuenta protegida con contraseña o PIN y frase de recuperación.
- RF-03 y RF-04 establecen propietario, administrador y operario, con roles asociados al contexto de una finca.
- RF-05 y RNF-11 requieren aislamiento por finca y verificación de cada acción sensible.
- RNF-15 exige identificadores únicos para evitar conflictos de sincronización offline; la retroalimentación recomienda UUID para entidades sincronizables.
- RF-24 y RNF-17 limitan respaldo, exportación y recuperación al propietario.

## Diferencias y prioridades aplicadas

| Tema | Diagrama RBAC | PDFs / proyecto actual | Decisión |
| --- | --- | --- | --- |
| Identificador de usuario | `Usua_ID INT(11)` | El proyecto usa `accounts_usuario.id` UUID; RNF-15 respalda UUID | Se conservó el usuario UUID existente. |
| Contraseña | No aparece en la tabla `usuario` | RF-01 obliga credenciales seguras | Se usa `accounts_usuario.password` con hash de Django; nunca texto plano. |
| Nombre de rol/recurso | `VARCHAR(4)` | Los nombres del dominio son más largos | Se usan códigos de cuatro caracteres, por ejemplo `SUPR`, `OPER`, `RBAC` y `FINC`. |
| Alcance del rol | Global por usuario | PDFs describen roles por finca | RBAC autoriza recursos globales; las consultas y validaciones ya existentes mantienen el alcance por finca. |

El ERD fue respetado para las tablas nuevas y sus columnas. La única diferencia estructural necesaria es que `Usuario_Usua_ID` referencia al UUID del usuario existente, no a un entero, para no contradecir RNF-15 ni refactorizar la identidad del proyecto.

## Esquema implementado

La app nueva es `backend/apps/rbac` y contiene estas tablas:

- `rol`: `Rol_ID` y `Rol_nombre`.
- `recurso`: `idrecurso` y `nombre`.
- `usuario_has_rol`: `Usuario_Usua_ID` y `Rol_Rol_ID`, con clave primaria compuesta.
- `rol_has_recurso`: `rol_Rol_ID` y `recurso_idrecurso`, con clave primaria compuesta.

`usuario` corresponde al modelo preexistente `accounts_usuario`. Sus datos de autenticación y contraseña no se duplican.

## Flujo de autorización aplicado

La autorización se evalúa en el servidor con esta cadena:

```text
Usuario autenticado
  -> usuario_has_rol
  -> rol
  -> rol_has_recurso
  -> recurso requerido por la vista
  -> autorización o respuesta 403
```

Los superusuarios de Django pueden realizar el arranque inicial y acceder al panel para asignar el rol `SUPR`. Esto evita introducir credenciales de arranque en el código.

Las rutas de negocio declararon su recurso requerido, entre ellos:

- `FINC`: fincas.
- `MIEM`: membresías.
- `INVT`: invitaciones.
- `RAZA`, `LOTE`, `BOVI`: catálogos, potreros y bovinos.
- `DISP`, `MODI`, `TIPO`, `MEDI`, `PESA`: dispositivos, IA, tipos, mediciones y pesajes.
- `RESP` y `SYNC`: respaldos y sincronización.
- `RBAC`: administración de roles, recursos y asignaciones.

Login, perfil, cierre de sesión y raíz de API son excepciones de sesión: permiten autenticarse o terminar sesión, pero no exponen una operación de negocio.

## Roles y recursos iniciales

El comando manual `python manage.py seed_rbac` crea o actualiza el catálogo sin crear usuarios, contraseñas ni tokens.

Roles iniciales:

- `SUPR`: superusuario RBAC.
- `PROP`: propietario.
- `ADMI`: administrador.
- `OPER`: operario.

El comando define recursos según los módulos actuales. Las asignaciones se pueden modificar después desde el panel RBAC.

## Endpoints RBAC

Todas estas rutas están bajo `/api/v1/rbac/` y exigen el recurso `RBAC` o un superusuario Django:

| Método | Ruta | Uso |
| --- | --- | --- |
| `GET`, `POST` | `/roles/` | Consultar y crear roles. |
| `GET`, `PATCH`, `DELETE` | `/roles/{id}/` | Consultar, editar o eliminar un rol. |
| `GET`, `POST` | `/resources/` | Consultar y crear recursos. |
| `GET`, `PATCH`, `DELETE` | `/resources/{id}/` | Gestionar recursos. |
| `GET` | `/usuarios/?q=` | Buscar usuarios activos y sus roles. |
| `GET`, `PUT` | `/usuarios/{uuid}/roles/` | Consultar o reemplazar los roles de un usuario. |

El inicio de sesión en `/api/v1/auth/token/` acepta correo electrónico o nombre de usuario y devuelve token, perfil, roles y recursos efectivos.

## Frontend

Se agregó la pantalla `frontend/src/pages/RbacAdmin.jsx`, disponible en `/rbac` para usuarios con `RBAC` o superusuarios. Permite:

- Crear, editar y eliminar roles.
- Asignar o retirar recursos de cada rol.
- Crear y eliminar recursos.
- Buscar usuarios.
- Asociar uno o más roles a cada usuario.
- Ver un marcador explícito para extensiones de auditoría y módulos futuros.

La interfaz adopta la dirección visual `Framed sheet`: marco verde grisáceo, hoja blanca, densidad de panel administrativo y ausencia de sombras o gradientes en reposo. Se reutilizó la estructura visual existente del proyecto.

## Seguridad

- Las contraseñas se gestionan con `set_password` y `check_password` de Django.
- No se generaron usuarios, contraseñas, tokens ni credenciales de prueba para producción.
- El login carga roles y permisos para la interfaz, pero la decisión de acceso se mantiene en el servidor.
- Las validaciones originales de ámbito por finca continúan activas después de la validación RBAC.
- Se conserva el filtrado de usuarios activos y no eliminados.

## Pruebas y comprobaciones realizadas

Se ejecutó correctamente:

```bash
cd backend
../Desarrollo/bin/python manage.py test --verbosity 1
../Desarrollo/bin/python manage.py check
../Desarrollo/bin/python manage.py makemigrations --check --dry-run

cd ../frontend
npm run build
```

Resultado final:

- 92 pruebas backend aprobadas.
- Comprobación de Django sin incidencias.
- No hay cambios de migración pendientes.
- Build de Vite aprobado.

Las pruebas RBAC cubren:

- Asignación de varios roles a un usuario.
- Verificación de permiso por recurso.
- Denegación de acceso sin recurso.
- Login que devuelve roles y recursos efectivos.

El linter de diseño detectó patrones visuales ya existentes en pantallas fuera del alcance RBAC (emojis, sombras y una interfaz anterior de permisos). No se refactorizaron para respetar el alcance solicitado. La inspección por capturas no pudo ejecutarse porque el entorno no tenía Chromium instalado.

## Puesta en marcha manual

```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_rbac
```

Después, inicie sesión con el usuario creado manualmente. El superusuario puede abrir `/rbac` y asignarse o asignar a otros el rol `SUPR`. No se debe usar ninguna credencial de demostración para producción.

## Archivos principales modificados o agregados

- `backend/apps/rbac/`: modelos, migración, serializadores, vistas, permisos, URLs, administración, comando y pruebas.
- `backend/apps/common/permissions.py`: consulta de recurso RBAC en servidor.
- `backend/apps/accounts/serializers.py` y `views.py`: perfil y login con roles/recursos.
- Vistas de módulos de negocio: declaración de recurso requerido.
- `frontend/src/pages/RbacAdmin.jsx`: panel de superusuario.
- `frontend/src/services/rbacService.js`: cliente API RBAC.
- `frontend/src/components/ResourceRoute.jsx`: guardia de interfaz complementaria.
- `frontend/src/App.jsx`, `DashboardLayout.jsx` y `styles/tailwind.css`: ruta, navegación y estilos del panel.
- `RBAC_NOTES.md`: resumen técnico más breve de decisiones y arranque.

## Pendientes explícitos

- Auditoría histórica de cambios de roles y permisos.
- Reportes de permisos específicos para módulos futuros de visión computacional.
- Diseño o rediseño de las pantallas funcionales ajenas al RBAC, que quedaron fuera de esta entrega.
