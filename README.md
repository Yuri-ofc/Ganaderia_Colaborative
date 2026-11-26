# G_Computacional — Ganadería de precisión

**Versión actual: v1.2.0** · [Cambios](CHANGELOG.md) · [Cómo contribuir](CONTRIBUTING.md)

## ¿Qué hace el proyecto?

Sistema web para la gestión de fincas ganaderas. Permite:

- Registrar **fincas**, **potreros** y **bovinos** (arete, raza, sexo, estado, movimientos).
- Trabajar en equipo por finca con roles de **propietario**, **administrador** y **operario**, y **invitar** miembros con un código por finca.
- Guardar **mediciones morfométricas** y **pesajes** reales (los registros no se editan: una corrección es un registro nuevo enlazado al original).
- Analizar una **captura de visión computacional** (foto o video) que genera una medición. La estimación es **simulada**, no sale de un modelo de IA entrenado, y queda marcada como tal en cada registro.
- Resolver la **sincronización offline**: cola de cambios por dispositivo y resolución manual cuando dos dispositivos tocan el mismo objeto.
- Generar **respaldos** por finca (cifrado opcional con Fernet, huella SHA-256 verificada antes de descargar o restaurar) y **restaurarlos**.
- Descargar **exportaciones** en CSV o JSON para leer los datos fuera del sistema (no sirven para restaurar).
- Administrar el **control de acceso (RBAC)**: roles, recursos del menú y etiquetas editables.
- Consultar una **landing pública** en `/inicio`.

El código, los modelos y las claves JSON de la API están en español.

## Tecnologías

| Capa | Tecnología |
| --- | --- |
| Backend | Python 3.12, Django 6.1, Django REST Framework 3.18, django-cors-headers |
| Base de datos | SQLite (por defecto) o PostgreSQL (configurable en `.env`) |
| Frontend | React 18, Vite 5, React Router 6, Tailwind CSS 3, axios, Leaflet |
| Autenticación | Token con caducidad de 30 días (`API_TOKEN_TTL_DIAS`) |

## Requisitos

- Python **3.12 o superior**
- Node.js **18 o superior** y npm
- Git

## Instalación

```bash
git clone https://github.com/Yuri-ofc/Ganaderia_Colaborative.git
cd Ganaderia_Colaborative
```

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                   # el .env no se versiona
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
# pegue la clave generada en SECRET_KEY dentro de .env

cd backend
python manage.py migrate
python manage.py seed_rbac             # crea roles y recursos (no crea credenciales)
python manage.py seed_demo             # opcional: 100 registros de demostración
```

Los usuarios de demostración comparten la contraseña `Demo.Ganaderia.2026`. Son datos de prueba: no los use en producción. Para una cuenta propia: `python manage.py createsuperuser`.

### Frontend

```bash
cd frontend
npm install
```

## Ejecución

En dos terminales:

```bash
# Terminal 1 — API en http://127.0.0.1:8000/api/v1/
cd backend && python manage.py runserver

# Terminal 2 — interfaz en http://localhost:5173
cd frontend && npm run dev
```

El servidor de Vite reenvía las peticiones `/api` al backend (`frontend/vite.config.js`). La landing está en `http://localhost:5173/inicio` y el login en `/`.

Para generar la versión de producción del frontend: `cd frontend && npm run build`.

### Pruebas

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run   # no debe detectar cambios
python manage.py test
```

El frontend todavía no tiene pruebas automáticas ni linter (ver [issue #12](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/12)); la comprobación mínima es `npm run build`.

## Variables de entorno principales

Todas están documentadas en `.env.example`.

| Variable | Para qué sirve | Por omisión |
| --- | --- | --- |
| `SECRET_KEY` | Clave criptográfica de Django | obligatoria si `DEBUG=False` |
| `DEBUG` | Modo depuración | `True` (ver [issue #11](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/11)) |
| `ALLOWED_HOSTS` | Hosts permitidos | `localhost,127.0.0.1` |
| `DATABASE_ENGINE` / `DATABASE_NAME` | Base de datos | SQLite en `database/data/db.sqlite3` |
| `FRONTEND_URL` | URL del frontend para los enlaces de correo | `http://localhost:5173` |
| `EMAIL_BACKEND` y `EMAIL_*` | Envío de correo (invitaciones) | consola |

Con `DEBUG=False` se exige `SECRET_KEY` y se activan HSTS, redirección a HTTPS y cookies seguras. Nunca escriba secretos en el código ni los suba al repositorio.

## Estructura

```
backend/    Django + DRF (apps: accounts, rbac, farms, cattle, measurements, backups, sync, common)
frontend/   React + Vite + Tailwind (pages, components, context, services, styles)
database/   Base SQLite local, fixtures de demostración y copias (los datos no se versionan)
docs/       Deuda técnica, evidencias del mantenimiento y referencia del backend
```

## Documentación

- [`docs/REFERENCIA_BACKEND.md`](docs/REFERENCIA_BACKEND.md): modelos, tablas, API y reglas de acceso.
- [`docs/DEUDA_TECNICA.md`](docs/DEUDA_TECNICA.md): diagnóstico de deuda técnica.
- [`docs/EVIDENCIAS.md`](docs/EVIDENCIAS.md): trazabilidad, estado del software y reflexión del ciclo de mantenimiento.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) y [`CHANGELOG.md`](CHANGELOG.md).
- Notas de diseño: `Mejoria.md` (landing), `RBAC_NOTES.md`, `SESION_RBAC.md` y `sistema.md`.
