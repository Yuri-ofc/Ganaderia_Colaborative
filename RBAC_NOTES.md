# Módulo RBAC

## Referencias leídas

- `Retroalimentacion_E1_01_Ganaderia.pdf` (2 páginas).
- `Ganaderia_ER_Scrum-1 (1).pdf` (7 páginas).
- `rbac.jpeg` suministrado.

## Política de autorización vigente

La fuente de verdad local para los permisos operativos es `README.md`, sección
**"Reglas de acceso"** y la tabla inmediatamente anterior de rutas. En caso de
discrepancia se aplica mínimo privilegio. `SESION_RBAC.md` conserva la referencia
previa a RF-24/RNF-17, que reserva respaldo, exportación y recuperación al
propietario; por ello esa regla más restrictiva prevalece sobre la nota antigua
de la tabla que menciona administradores para respaldos.

| Rol | Permisos de módulo efectivos |
| --- | --- |
| `SUPR` | Todos los módulos, incluido RBAC y visión pendiente. |
| `PROP` | Fincas, miembros, invitaciones, lotes, bovinos, mediciones, pesajes, sincronización, respaldos, exportación y recuperación. |
| `ADMI` | Fincas, miembros, invitaciones, lotes, bovinos, mediciones, pesajes y sincronización. |
| `OPER` | Consulta de finca/lotes y registro-consulta de bovinos, mediciones, pesajes y sincronización. |

Los catálogos se leen con una sesión activa y solo los escribe `is_staff`; los
dispositivos son personales y se limitan al propietario. No se representan como
privilegios de una finca. `apps.rbac.services.puede_ejecutar` evalúa recurso y
acción; los serializers solo verifican el alcance del objeto.

## Decisiones

- Se aplican los roles de los PDFs con códigos compatibles con `VARCHAR(4)`: `SUPR`, `PROP`, `ADMI` y `OPER`. Los recursos también son códigos de cuatro caracteres; `seed_rbac` los crea sin crear usuarios ni contraseñas.
- Se mantienen las tablas del ERD: `rol`, `recurso`, `usuario_has_rol` y `rol_has_recurso`, incluyendo los nombres de columnas de unión. El proyecto ya tiene `accounts_usuario` con UUID y contraseña hash de Django; por RNF-15 se conserva esa tabla en vez de crear el `usuario.Usua_ID INT(11)` del dibujo.
- El login usa el hash de contraseña de Django y devuelve los roles y recursos efectivos. El middleware de permisos resuelve `usuario -> usuario_has_rol -> rol -> rol_has_recurso -> recurso` en el servidor. Las reglas de finca existentes siguen comprobando el aislamiento por finca y restricciones finas (por ejemplo, propietario del recurso).
- Las rutas de negocio declaran su recurso de cuatro caracteres. Login, perfil, logout y raíz de API quedan como excepciones de sesión para hacer posible la autenticación; no exponen acciones de negocio. Los superusuarios de Django tienen acceso de arranque y pueden asignar el rol `SUPR` desde el panel RBAC.

## Diferencias detectadas

- El ERD adjunto declara `usuario.Usua_ID INT(11)` pero los PDFs exigen UUID para datos sincronizables (RNF-15), y el proyecto existente usa UUID. Se priorizó el requisito y el esquema existente.
- El ERD no tiene una columna de contraseña; el PDF RF-01 la exige. Se usa `accounts_usuario.password`, hash seguro de Django, sin crear ni fijar credenciales.
- `Rol_nombre VARCHAR(4)` y `recurso.nombre VARCHAR(4)` no pueden contener los nombres descriptivos del PDF. Por eso se almacenan códigos de cuatro caracteres y se documentan en el comando de carga.
- Los PDFs describen roles por finca; el ERD describe rol global de usuario. RBAC autoriza el recurso global y los filtros/reglas existentes conservan el alcance de cada finca.

## Pantallas pendientes

Las áreas de visión computacional, mediciones, sincronización y respaldos no solicitadas para esta entrega no se rediseñaron. El módulo muestra un marcador explícito para extensiones RBAC pendientes de dichas áreas.

## Arranque manual

1. Cree el usuario inicial manualmente: `cd backend && python manage.py createsuperuser`.
2. Aplique migraciones y cargue únicamente el catálogo RBAC: `python manage.py migrate && python manage.py seed_rbac`.
3. Ingrese con esas credenciales; no hay credenciales generadas ni almacenadas en el código.
