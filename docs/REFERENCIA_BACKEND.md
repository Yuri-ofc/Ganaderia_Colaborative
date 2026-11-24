# Referencia del backend

Detalle técnico del backend (estructura, modelos, API y reglas de acceso). Para instalar y ejecutar el proyecto, vea el [README](../README.md).

## Estructura

```
G_Computacional/
├── backend/                 # Proyecto Django
│   ├── manage.py
│   ├── config/              # settings, urls, wsgi/asgi y lector de .env
│   └── apps/
│       ├── accounts/        # Usuario (UUID) y autenticación por token
│       ├── rbac/            # Roles, recursos (menú) y etiquetas editables
│       ├── farms/           # Finca, Membresia e Invitacion
│       ├── cattle/          # Raza, Potrero, Bovino y MovimientoPotrero
│       ├── measurements/    # Dispositivo, ModeloIa, TipoMedida, Medicion, MedidaMorfometrica y Pesaje
│       ├── backups/         # Respaldo (metadatos por finca)
│       ├── sync/            # CambioSincronizacion (cola de los dispositivos)
│       └── common/          # ModeloBaseUuid, permisos y utilidades compartidas
├── frontend/                # React 18 + Vite + Tailwind (ver README)
│   ├── public/
│   └── src/{components,context,pages,services,styles}/
├── database/
│   ├── data/                # Base SQLite (db.sqlite3, no se versiona)
│   ├── fixtures/            # Catálogo de datos de demostración
│   └── backups/             # Copias de la base (no se versionan)
├── docs/                    # Deuda técnica, evidencias y esta referencia
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
