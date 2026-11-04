# Sistema Ganadería

## Visión general
Este proyecto es una **aplicación web completa** para la gestión de una granja, construida con:

- **Backend**: Django + Django REST Framework (DRF).  Todas las APIs están versionadas bajo el prefijo `/api/v1/`.
- **Frontend**: React 18 con Vite, Tailwind CSS y React‑Router.

La arquitectura sigue el patrón **API‑first**: el frontend se comunica exclusivamente vía peticiones HTTP JSON con el backend.

## Estructura del proyecto
```
Proyecto-Ganaderia/
├─ backend/                # Django project
│   ├─ apps/               # Aplicaciones de dominio (accounts, cattle, farms, …)
│   │   ├─ accounts/       # Autenticación y usuarios
│   │   │   ├─ models.py    # Modelo `Usuario`
│   │   │   ├─ serializers.py
│   │   │   ├─ views.py      # VistaRegistro, VistaInicioSesion, VistaCierreSesion
│   │   │   ├─ urls.py       # /register/, /token/, /logout/
│   │   └─ …
│   ├─ config/            # Settings, URLs raíz
│   └─ manage.py
├─ frontend/               # React + Vite
│   ├─ public/
│   │   └─ index.html
│   ├─ src/
│   │   ├─ assets/          # (vacío por ahora)
│   │   ├─ components/      # componentes reutilizables
│   │   ├─ pages/
│   │   │   └─ Login.jsx    # Página de login (copia del ejemplo prebuiltui)
│   │   ├─ services/        # (para futuros wrappers de API)
│   │   ├─ styles/
│   │   │   └─ tailwind.css # Tailwind directives
│   │   ├─ App.jsx          # Router principal
│   │   ├─ main.jsx         # Punto de entrada React
│   ├─ vite.config.js      # Proxy `/api` → Django (localhost:8000)
│   ├─ tailwind.config.js  # Configuración Tailwind
│   └─ package.json        # Dependencias y scripts (`dev`, `build`, `preview`)
├─ Desarrollo/             # Entorno virtual (`pip install -r requirements.txt`)
└─ sistema.md              # **Este documento**
```

## Backend – Endpoints clave
| Área | Endpoint | Método | Descripción |
|------|----------|--------|-------------|
| **Auth** | `/api/v1/auth/register/` | `POST` | Registro de usuario (`SerializerRegistro`). |
| **Auth** | `/api/v1/auth/token/` | `POST` | Login – devuelve `token`. Usa `SerializerInicioSesion`. |
| **Auth** | `/api/v1/auth/logout/` | `POST` | Cierre de sesión – elimina el token activo. |
| **Otros** | `…` | `…` | Cada app (`cattle`, `farms`, `measurements`, …) expone sus propios recursos bajo `/api/v1/`.

### Modelo de usuario
```python
class Usuario(ModeloBaseUuid, AbstractUser):
    telefono = models.CharField(max_length=20, null=True, blank=True)
    hash_frase_recuperacion = models.CharField(max_length=255, blank=True)
```
Se hereda de `AbstractUser`, por lo que el **username** y **email** siguen disponibles.  El campo `telefono` tiene una restricción única condicional para usuarios activos.

## Frontend – Flujo de login
1. El usuario abre `http://localhost:5173/` (servidor Vite).
2. La ruta `/` renderiza `Login.jsx`.
3. Al enviar el formulario, se llama a:
   ```js
   axios.post('/api/v1/auth/token/', { email, password })
   ```
4. El token JWT recibido se guarda en `localStorage` (`authToken`).
5. `navigate('/dashboard')` redirige a la página principal (todavía por crear).

### Tecnologías usadas
- **React** y **React‑Router** para SPA.
- **Axios** para peticiones HTTP.
- **Tailwind CSS** para estilos rápidos y responsivos.
- **Vite** con proxy automático que reenvía cualquier ruta que empiece con `/api` al backend Django (`http://127.0.0.1:8000`).

## Cómo iniciar el proyecto
```bash
# Backend ---------------------------------------------------
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver  # http://127.0.0.1:8000/

# Frontend -------------------------------------------------
cd ../frontend
npm install               # instala react, vite, tailwind, axios, react-router-dom
npm run dev               # http://localhost:5173/
```

Una vez ambos servidores estén activos, la aplicación está lista para usarse.

---
> **Nota**: El proyecto está preparado para ampliarse.  Puedes agregar nuevas páginas dentro `frontend/src/pages/`, crear componentes reutilizables en `frontend/src/components/` y exponer nuevos endpoints REST en Django bajo la ruta `/api/v1/`.

---
*Este documento (`sistema.md`) sirve como referencia rápida para nuevos desarrolladores y para la documentación del proyecto.*
