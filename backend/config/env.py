import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

VALORES_VERDADEROS = {"1", "true", "t", "yes", "y", "on", "si", "sí"}
VALORES_FALSOS = {"0", "false", "f", "no", "n", "off"}

_SIN_VALOR = object()


def cargar_env(*rutas):
    for ruta in rutas:
        ruta = Path(ruta)
        if not ruta.is_file():
            continue
        for linea_original in ruta.read_text(encoding="utf-8").splitlines():
            linea = linea_original.strip()
            if not linea or linea.startswith("#"):
                continue
            if linea.startswith("export "):
                linea = linea[len("export "):].strip()
            clave, separador, valor = linea.partition("=")
            if not separador:
                continue
            clave = clave.strip()
            if not clave:
                continue
            valor = valor.strip()
            if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
                valor = valor[1:-1]
            os.environ.setdefault(clave, valor)
        return ruta
    return None


def leer_texto(nombre, defecto=_SIN_VALOR):
    valor = os.environ.get(nombre)
    if valor is None or valor == "":
        if defecto is _SIN_VALOR:
            raise ImproperlyConfigured(
                f"Falta la variable de entorno obligatoria {nombre}. "
                "Copie .env.example a .env y complete los valores."
            )
        return defecto
    return valor


def leer_bool(nombre, defecto=_SIN_VALOR):
    valor = os.environ.get(nombre)
    if valor is None or valor == "":
        if defecto is _SIN_VALOR:
            raise ImproperlyConfigured(f"Falta la variable de entorno obligatoria {nombre}.")
        return defecto
    normalizado = valor.strip().lower()
    if normalizado in VALORES_VERDADEROS:
        return True
    if normalizado in VALORES_FALSOS:
        return False
    raise ImproperlyConfigured(f"{nombre} debe ser un booleano (true/false), no {valor!r}.")


def leer_entero(nombre, defecto=_SIN_VALOR):
    valor = os.environ.get(nombre)
    if valor is None or valor == "":
        if defecto is _SIN_VALOR:
            raise ImproperlyConfigured(f"Falta la variable de entorno obligatoria {nombre}.")
        return defecto
    try:
        return int(valor.strip())
    except ValueError as exc:
        raise ImproperlyConfigured(f"{nombre} debe ser un número entero, no {valor!r}.") from exc


def leer_lista(nombre, defecto=_SIN_VALOR, separador=","):
    valor = os.environ.get(nombre)
    if valor is None or valor.strip() == "":
        if defecto is _SIN_VALOR:
            raise ImproperlyConfigured(f"Falta la variable de entorno obligatoria {nombre}.")
        return list(defecto)
    return [elemento.strip() for elemento in valor.split(separador) if elemento.strip()]


def leer_ruta(nombre, defecto=_SIN_VALOR, *, relativa_a=None):
    valor = os.environ.get(nombre)
    if valor is None or valor.strip() == "":
        if defecto is _SIN_VALOR:
            raise ImproperlyConfigured(f"Falta la variable de entorno obligatoria {nombre}.")
        return defecto
    ruta = Path(valor.strip()).expanduser()
    if not ruta.is_absolute() and relativa_a is not None:
        ruta = Path(relativa_a) / ruta
    return ruta
