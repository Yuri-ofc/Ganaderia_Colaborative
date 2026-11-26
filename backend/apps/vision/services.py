"""Estimación simulada de peso y condición corporal a partir de una captura.

MARCADOR DE IMPLEMENTACIÓN: aquí no hay inferencia real. La estimación sale de
una curva de crecimiento aproximada más una variación aleatoria acotada, para
que el flujo completo (captura -> medición -> histórico) funcione de punta a
punta mientras no exista un modelo entrenado.

Para enchufar un modelo real basta reemplazar ``estimar_captura`` y registrar
su versión como un ``ModeloIa`` distinto de ``VERSION_SIMULADA``: las
mediciones ya guardan de qué modelo vinieron, así que los datos históricos
siguen distinguiéndose sin ambigüedad.
"""

import random
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from apps.measurements.models import Dispositivo, Medicion, ModeloIa

VERSION_SIMULADA = "simulado-v1"
CALIBRACION_SIMULADA = "Estimación heurística sin modelo entrenado (marcador de implementación)"

MODELO_DISPOSITIVO_WEB = "Captura web"

# Curva de crecimiento aproximada de un bovino de carne, suficiente para que
# los valores simulados sean verosímiles frente a la edad del animal.
PESO_AL_NACER_KG = Decimal("35")
GANANCIA_DIARIA_KG = Decimal("0.65")
PESO_ADULTO_KG = {"macho": Decimal("550"), "hembra": Decimal("450")}

MARGEN_INTERVALO = Decimal("0.08")
VARIACION_MAXIMA = Decimal("0.10")
CONFIANZA_MINIMA = Decimal("60")
CONFIANZA_MAXIMA = Decimal("75")
CENTESIMA = Decimal("0.01")


def modelo_simulado():
    """``ModeloIa`` con el que se marcan todas las mediciones simuladas."""
    modelo, creado = ModeloIa.objects.get_or_create(
        version=VERSION_SIMULADA, defaults={"calibracion": CALIBRACION_SIMULADA, "activo": True}
    )
    if not creado and not modelo.activo:
        modelo.activo = True
        modelo.save(update_fields=("activo", "actualizado_en"))
    return modelo


def dispositivo_de_captura(usuario):
    """Dispositivo virtual del usuario para las capturas hechas desde la web.

    El modelo de datos exige un dispositivo por medición, pero una captura
    desde el navegador no viene de un equipo registrado; se reutiliza siempre
    el mismo para no llenar la lista de dispositivos del usuario.
    """
    dispositivo = Dispositivo.objects.filter(
        propietario=usuario, modelo=MODELO_DISPOSITIVO_WEB, eliminado_en__isnull=True
    ).first()
    if dispositivo is None:
        dispositivo = Dispositivo.objects.create(
            propietario=usuario, modelo=MODELO_DISPOSITIVO_WEB, sistema_operativo="Navegador"
        )
    dispositivo.ultima_conexion_en = timezone.now()
    dispositivo.save(update_fields=("ultima_conexion_en", "actualizado_en"))
    return dispositivo


def _peso_base(bovino):
    minimo = Decimal(settings.VISION_PESO_MIN_KG)
    maximo = Decimal(settings.VISION_PESO_MAX_KG)
    if not bovino.fecha_nacimiento_estimada:
        return (minimo + maximo) / 2
    dias = max((date.today() - bovino.fecha_nacimiento_estimada).days, 0)
    techo = PESO_ADULTO_KG.get(bovino.sexo, maximo)
    return min(PESO_AL_NACER_KG + GANANCIA_DIARIA_KG * dias, techo)


def estimar_captura(bovino):
    """Valores simulados que cumplen las restricciones de ``Medicion``."""
    base = _peso_base(bovino)
    factor = Decimal(str(random.uniform(float(-VARIACION_MAXIMA), float(VARIACION_MAXIMA))))
    peso = max(base * (Decimal("1") + factor), Decimal("1")).quantize(CENTESIMA)
    margen = (peso * MARGEN_INTERVALO).quantize(CENTESIMA)
    confianza = Decimal(str(random.uniform(float(CONFIANZA_MINIMA), float(CONFIANZA_MAXIMA))))
    return {
        "peso_estimado_kg": peso,
        "intervalo_confianza_min_kg": max(peso - margen, Decimal("0")).quantize(CENTESIMA),
        "intervalo_confianza_max_kg": (peso + margen).quantize(CENTESIMA),
        "condicion_corporal": Decimal(str(round(random.uniform(2.5, 4.0), 1))),
        "nivel_confianza": confianza.quantize(CENTESIMA),
    }


def crear_medicion_simulada(bovino, usuario, tipo_archivo):
    """Medición trazada como simulada para la captura recién subida."""
    modo = (
        Medicion.ModoCaptura.VIDEO
        if tipo_archivo == "video"
        else Medicion.ModoCaptura.FOTO
    )
    return Medicion.objects.create(
        bovino=bovino,
        creado_por=usuario,
        dispositivo=dispositivo_de_captura(usuario),
        modelo_ia=modelo_simulado(),
        capturado_en=timezone.now(),
        modo_captura=modo,
        **estimar_captura(bovino),
    )
