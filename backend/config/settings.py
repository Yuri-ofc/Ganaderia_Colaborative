import os
from pathlib import Path

from .env import cargar_env, leer_bool, leer_entero, leer_lista, leer_ruta, leer_texto

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

ENV_FILE = cargar_env(
    os.environ.get("DJANGO_ENV_FILE", PROJECT_ROOT / ".env"),
    BASE_DIR / ".env",
)

DEBUG = leer_bool("DEBUG", True)

if DEBUG:
    SECRET_KEY = leer_texto("SECRET_KEY", "django-insecure-solo-para-desarrollo-local")
else:
    SECRET_KEY = leer_texto("SECRET_KEY")

ALLOWED_HOSTS = leer_lista("ALLOWED_HOSTS", ["localhost", "127.0.0.1"] if DEBUG else [])

CSRF_TRUSTED_ORIGINS = leer_lista("CSRF_TRUSTED_ORIGINS", [])


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'apps.common',
    'apps.accounts',
    'apps.farms',
    'apps.cattle',
    'apps.measurements',
    'apps.backups',
    'apps.sync',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


DATABASE_DIR = PROJECT_ROOT / 'database'
DATABASE_DATA_DIR = DATABASE_DIR / 'data'
DATABASE_FIXTURES_DIR = DATABASE_DIR / 'fixtures'
DATABASE_BACKUPS_DIR = leer_ruta('DATABASE_BACKUPS_DIR', DATABASE_DIR / 'backups', relativa_a=PROJECT_ROOT)

FIXTURE_DIRS = [DATABASE_FIXTURES_DIR]

DATABASE_ENGINE = leer_texto('DATABASE_ENGINE', 'django.db.backends.sqlite3')

if DATABASE_ENGINE.endswith('sqlite3'):
    DATABASE_NAME = leer_ruta('DATABASE_NAME', DATABASE_DATA_DIR / 'db.sqlite3', relativa_a=PROJECT_ROOT)
else:
    DATABASE_NAME = leer_texto('DATABASE_NAME')

DATABASES = {
    'default': {
        'ENGINE': DATABASE_ENGINE,
        'NAME': str(DATABASE_NAME),
        'USER': leer_texto('DATABASE_USER', ''),
        'PASSWORD': leer_texto('DATABASE_PASSWORD', ''),
        'HOST': leer_texto('DATABASE_HOST', ''),
        'PORT': leer_texto('DATABASE_PORT', ''),
        'CONN_MAX_AGE': leer_entero('DATABASE_CONN_MAX_AGE', 0),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = leer_texto('LANGUAGE_CODE', 'es-co')

TIME_ZONE = leer_texto('TIME_ZONE', 'America/Bogota')

USE_I18N = True

USE_TZ = True


STATIC_URL = leer_texto('STATIC_URL', 'static/')
STATIC_ROOT = leer_ruta('STATIC_ROOT', BASE_DIR / 'staticfiles', relativa_a=BASE_DIR)
MEDIA_URL = leer_texto('MEDIA_URL', 'media/')
MEDIA_ROOT = leer_ruta('MEDIA_ROOT', BASE_DIR / 'media', relativa_a=BASE_DIR)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.Usuario'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.TokenAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['apps.common.permissions.PermisoUsuarioActivo'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': leer_entero('API_PAGE_SIZE', 25),
    'DEFAULT_THROTTLE_RATES': {
        'auth': leer_texto('API_THROTTLE_AUTH', '10/minute'),
        'registration': leer_texto('API_THROTTLE_REGISTRATION', '5/hour'),
    },
}


# --- CORS -------------------------------------------------------------------
# En desarrollo se permiten todos los orígenes; en producción se usa la lista
# definida en la variable de entorno CORS_ALLOWED_ORIGINS.
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = leer_lista('CORS_ALLOWED_ORIGINS', [])
CORS_ALLOW_CREDENTIALS = True


EMAIL_BACKEND = leer_texto('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = leer_texto('EMAIL_HOST', '')
EMAIL_PORT = leer_entero('EMAIL_PORT', 25)
EMAIL_HOST_USER = leer_texto('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = leer_texto('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = leer_bool('EMAIL_USE_TLS', False)
# Si no se define, cae al mismo EMAIL_HOST_USER: con Gmail, el remitente debe
# coincidir con la cuenta autenticada o el envío se rechaza/reescribe.
DEFAULT_FROM_EMAIL = leer_texto('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'no-reply@g-computacional.local')

# URL base del frontend, usada para armar enlaces dentro de los correos (ej. invitaciones).
FRONTEND_URL = leer_texto('FRONTEND_URL', 'http://localhost:5173')


if not DEBUG:
    SECURE_SSL_REDIRECT = leer_bool('SECURE_SSL_REDIRECT', True)
    SESSION_COOKIE_SECURE = leer_bool('SESSION_COOKIE_SECURE', True)
    CSRF_COOKIE_SECURE = leer_bool('CSRF_COOKIE_SECURE', True)
    SECURE_HSTS_SECONDS = leer_entero('SECURE_HSTS_SECONDS', 31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
