# G_Computacional

Backend del proyecto de ganadería de precisión: API REST en Django + Django REST
Framework para registrar fincas, bovinos y mediciones morfométricas estimadas
por visión artificial, con trabajo offline y sincronización por dispositivo.

El código, los modelos y las claves JSON de la API están en español. El
repositorio reserva además un espacio vacío para el frontend, que todavía no
tiene código.

## Estructura

```
G_Computacional/
├── backend/                 # Proyecto Django
│   ├── manage.py
│   ├── config/              # settings, urls, wsgi/asgi y lector de .env
│   └── apps/
│       ├── accounts/        # Usuario (UUID) y autenticación por token
│       ├── farms/           # Finca, Membresia e Invitacion
│       ├── cattle/          # Raza, Potrero, Bovino y MovimientoPotrero
│       ├── measurements/    # Dispositivo, ModeloIa, TipoMedida, Medicion, MedidaMorfometrica y Pesaje
│       ├── backups/         # Respaldo (metadatos por finca)
│       ├── sync/            # CambioSincronizacion (cola de los dispositivos)
│       └── common/          # ModeloBaseUuid, permisos y utilidades compartidas
├── frontend/                # Reservado (vacío, sin framework elegido)
│   ├── public/
│   └── src/{assets,components,pages,services,styles}/
├── database/
│   ├── data/                # Base SQLite (db.sqlite3, no se versiona)
│   ├── fixtures/            # Catálogo de datos de demostración
│   └── backups/             # Copias de la base (no se versionan)
├── .env.example
├── requirements.txt
└── README.md
```

Las migraciones de esquema viven dentro de cada app
(`backend/apps/*/migrations/`); en `database/` solo hay datos.

## Modelos y tablas

| Modelo | Tabla | Campos propios |
| --- | --- | --- |
| `Usuario` | `accounts_usuario` | `telefono`, `hash_frase_recuperacion` (más los de Django: `username`, `email`, `password`…) |
| `Finca` | `farms_finca` | `propietario`, `nombre`, `ubicacion` |
| `Membresia` | `farms_membresia` | `finca`, `usuario`, `rol`, `invitado_por` |
| `Invitacion` | `farms_invitacion` | `finca`, `telefono`, `rol`, `token`, `estado`, `expira_en`, `creado_por`, `aceptado_por`, `aceptado_en` |
| `Raza` | `cattle_raza` | `nombre` |
| `Potrero` | `cattle_potrero` | `finca`, `nombre` |
| `Bovino` | `cattle_bovino` | `finca`, `potrero`, `arete`, `raza`, `sexo`, `categoria_productiva`, `estado_fisiologico`, `fecha_nacimiento_estimada`, `estado_operativo`, `url_foto_perfil`, `perfil_aprobado_por`, `creado_por`, `desactivado_en`, `motivo_desactivacion` |
| `MovimientoPotrero` | `cattle_movimientopotrero` | `bovino`, `potrero`, `iniciado_en`, `finalizado_en`, `creado_por` |
| `Dispositivo` | `measurements_dispositivo` | `propietario`, `modelo`, `sistema_operativo`, `ultima_conexion_en` |
| `ModeloIa` | `measurements_modeloia` | `version`, `calibracion`, `activo` |
| `TipoMedida` | `measurements_tipomedida` | `nombre`, `unidad` |
| `Medicion` | `measurements_medicion` | `bovino`, `creado_por`, `dispositivo`, `modelo_ia`, `capturado_en`, `modo_captura`, `peso_estimado_kg`, `intervalo_confianza_min_kg`, `intervalo_confianza_max_kg`, `condicion_corporal`, `nivel_confianza`, `corrige` |
| `MedidaMorfometrica` | `measurements_medidamorfometrica` | `medicion`, `tipo_medida`, `valor` |
| `Pesaje` | `measurements_pesaje` | `bovino`, `creado_por`, `pesado_en`, `tipo_bascula`, `peso_real_kg`, `corrige` |
| `Respaldo` | `backups_respaldo` | `finca`, `creado_por`, `url_almacenamiento`, `suma_verificacion`, `tamano_bytes`, `version`, `cifrado` |
| `CambioSincronizacion` | `sync_cambiosincronizacion` | `finca`, `dispositivo`, `creado_por`, `id_cambio_cliente`, `recurso`, `id_objeto`, `accion`, `contenido`, `sincronizado_en` |

Todos heredan de `ModeloBaseUuid`: `id` (UUID), `creado_en`, `actualizado_en` y
`eliminado_en` (borrado lógico).

Valores de los campos con opciones:

| Campo | Valores |
| --- | --- |
| `Membresia.rol`, `Invitacion.rol` | `administrador`, `operario` |
| `Invitacion.estado` | `pendiente`, `aceptada`, `cancelada`, `expirada` |
| `Bovino.sexo` | `hembra`, `macho` |
| `Bovino.estado_operativo` | `perfil_pendiente`, `activo`, `vendido`, `muerto`, `retirado` |
| `Medicion.modo_captura` | `video`, `foto` |
| `CambioSincronizacion.accion` | `crear`, `actualizar`, `eliminar` |

## Puesta en marcha

Se necesita Python 3.12 o superior.

### 1. Entorno virtual

```bash
cd G_Computacional
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Este repositorio ya trae un entorno virtual llamado `Desarrollo/` (ignorado por
git). Para reutilizarlo: `source Desarrollo/bin/activate`.

### 2. Variables de entorno

```bash
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

Pegue la clave generada en `SECRET_KEY`. El archivo `.env` vive en la raíz del
repositorio, no se versiona y lo lee `backend/config/env.py` al iniciar Django
(sin dependencias externas). Las variables ya presentes en el entorno del proceso
tienen prioridad sobre el archivo, de modo que un despliegue puede inyectarlas.

Variables principales (todas documentadas en `.env.example`):

| Variable | Para qué sirve | Valor por omisión |
| --- | --- | --- |
| `SECRET_KEY` | Clave criptográfica de Django | obligatoria si `DEBUG=False` |
| `DEBUG` | Modo depuración | `True` |
| `ALLOWED_HOSTS` | Hosts permitidos, separados por comas | `localhost,127.0.0.1` |
| `DATABASE_ENGINE` | Motor de base de datos | `django.db.backends.sqlite3` |
| `DATABASE_NAME` | Ruta o nombre de la base | `database/data/db.sqlite3` |
| `API_PAGE_SIZE` | Tamaño de página de la API | `25` |
| `API_THROTTLE_AUTH` / `API_THROTTLE_REGISTRATION` | Límites de login y registro | `10/minute` / `5/hour` |
| `TIME_ZONE` / `LANGUAGE_CODE` | Localización | `America/Bogota` / `es-co` |

Con `DEBUG=False` se exige `SECRET_KEY` y se activan HSTS, redirección a HTTPS y
cookies seguras; en desarrollo con `runserver` debe quedar en `True`.

### 3. Migraciones

```bash
cd backend
python manage.py migrate
```

La base SQLite se crea o se abre en `database/data/db.sqlite3`.

### 4. Datos de demostración

```bash
python manage.py seed_demo            # inserta 100 registros de negocio
python manage.py seed_demo --dry-run  # simula y deshace la transacción
```

El comando lee `database/fixtures/demo_seed.json`, es idempotente (cada registro
tiene un UUID derivado del catálogo, así que una segunda ejecución no duplica
nada) y nunca modifica ni borra registros preexistentes. Al terminar imprime los
registros creados por tabla y el total.

Reparto de los 100 registros:

| Tabla | Registros |
| --- | --- |
| `accounts_usuario` | 6 |
| `farms_finca` | 3 |
| `farms_membresia` | 6 |
| `cattle_raza` | 4 |
| `cattle_potrero` | 6 |
| `cattle_bovino` | 24 |
| `measurements_dispositivo` | 5 |
| `measurements_modeloia` | 2 |
| `measurements_tipomedida` | 4 |
| `measurements_medicion` | 20 |
| `measurements_medidamorfometrica` | 12 |
| `measurements_pesaje` | 8 |
| **Total** | **100** |

Las tres fincas de demostración quedan con propietaria, administrador y operarios
distintos; la contraseña de todos los usuarios demo está en el campo
`clave_demo` del catálogo (`Demo.Ganaderia.2026`). Son datos de prueba: no los
use en producción.

Para un superusuario propio:

```bash
python manage.py createsuperuser
```

### 5. Servidor

```bash
python manage.py runserver
```

- API: http://127.0.0.1:8000/api/v1/
- Admin: http://127.0.0.1:8000/admin/

La raíz `/` no tiene ruta: responde 404 a propósito.

### 6. Pruebas

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run   # no debe detectar cambios
python manage.py test
```

## API

Todas las rutas cuelgan de `/api/v1/`. La respuesta siempre es JSON y las listas
vienen paginadas (`count`, `next`, `previous`, `results`).

### Autenticación

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/api/v1/` | Índice de endpoints (no requiere token) |
| `POST` | `/api/v1/auth/register/` | Crea una cuenta (`username`, `email`, `telefono`, `password`) |
| `POST` | `/api/v1/auth/token/` | Devuelve el token de un usuario |
| `POST` | `/api/v1/auth/logout/` | Revoca el token actual |

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo_ana_propietaria","password":"Demo.Ganaderia.2026"}' \
  | python -c 'import json,sys; print(json.load(sys.stdin)["token"])')

curl -s http://127.0.0.1:8000/api/v1/cattle/ -H "Authorization: Token $TOKEN"
```

### Recursos

Las rutas conservan sus nombres originales; los campos del cuerpo y de la
respuesta van en español.

| Ruta | Modelo | Métodos | Notas |
| --- | --- | --- | --- |
| `/farms/` | `Finca` | `GET` `POST` `PATCH` `PUT` `DELETE` | Solo el propietario modifica o elimina |
| `/memberships/` | `Membresia` | `GET` `POST` `PATCH` `PUT` `DELETE` | Solo propietario o administrador |
| `/invitations/` | `Invitacion` | `GET` `POST` `PATCH` `PUT` `DELETE` | `POST /invitations/accept/` canjea el `token` |
| `/breeds/` | `Raza` | `GET` + escritura de staff | Catálogo global |
| `/lots/` | `Potrero` | `GET` `POST` `PATCH` `PUT` `DELETE` | Escritura para propietario o administrador |
| `/cattle/` | `Bovino` | `GET` `POST` `PATCH` `PUT` `DELETE` | `POST /cattle/{id}/approve-profile/`; `POST /cattle/{id}/deactivate/` con `{"estado": "vendido", "motivo": "…"}` |
| `/lot-movements/` | `MovimientoPotrero` | `GET` `POST` `PATCH` | Sin borrado; el movimiento abierto fija el potrero actual |
| `/devices/` | `Dispositivo` | `GET` `POST` `PATCH` `PUT` `DELETE` | Cada usuario ve solo sus dispositivos |
| `/ai-models/` | `ModeloIa` | `GET` + escritura de staff | Catálogo global |
| `/measurement-types/` | `TipoMedida` | `GET` + escritura de staff | Catálogo global |
| `/measurements/` | `Medicion` | `GET` `POST` | Inmutables: una corrección es un registro nuevo (`corrige`) |
| `/morphometric-measurements/` | `MedidaMorfometrica` | `GET` `POST` | Inmutables |
| `/scale-weighings/` | `Pesaje` | `GET` `POST` | Inmutables |
| `/backups/` | `Respaldo` | `GET` `POST` | Solo propietario o administrador |
| `/sync-changes/` | `CambioSincronizacion` | `GET` `POST` | `POST /sync-changes/{id}/acknowledge/` lo confirma el dueño del dispositivo |

Filtros de consulta: `?finca=`, `?potrero=`, `?bovino=`, `?dispositivo=`,
`?medicion=`, `?estado=`, `?search=`, `?ordering=` y `?page=`.

## Reglas de acceso

- **Propietario**: creador de la finca. Único que puede renombrarla, eliminarla,
  asignar o retirar administradores.
- **Administrador**: gestiona potreros, membresías de operarios, invitaciones y
  respaldos de su finca.
- **Operario**: consulta la finca y registra bovinos, mediciones, pesajes y
  cambios de sincronización.
- Las consultas de cada vista se filtran por las fincas del usuario, así que un
  usuario no ve ni modifica datos de una finca a la que no pertenece: obtiene
  `404` en los detalles ajenos y `400` si intenta referenciarlos al crear.
- Las mediciones, medidas morfométricas y pesajes no se editan ni se borran
  (`405`); para corregir se crea un registro nuevo que apunta al anterior con
  `corrige`.
- El borrado de fincas, potreros, bovinos, membresías y dispositivos es lógico
  (`eliminado_en`), de modo que el historial se conserva.
- Los identificadores de todas las tablas de negocio son UUID.

## Respaldos de la base

```bash
cp database/data/db.sqlite3 "database/backups/db-$(date +%Y%m%d-%H%M).sqlite3"
```

La carpeta `database/backups/` se versiona vacía; su contenido queda fuera de git,
igual que `database/data/`.

## Frontend

`frontend/` solo contiene la estructura de carpetas (`public/`, `src/assets/`,
`src/components/`, `src/pages/`, `src/services/`, `src/styles/`), con archivos
`.gitkeep` para que git las conserve. No hay framework elegido ni código de
interfaz todavía. Si el frontend se sirve desde otro puerto, agregue su origen a
`CSRF_TRUSTED_ORIGINS` en el `.env` y considere habilitar CORS.
