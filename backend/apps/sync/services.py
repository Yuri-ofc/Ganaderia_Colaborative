"""Detección y resolución de conflictos de la cola offline.

Un conflicto es que dos dispositivos hayan editado sin conexión el mismo objeto
(mismo ``recurso`` + ``id_objeto``) y los dos cambios sigan sin sincronizar. No
se comparan los contenidos: ``contenido`` es JSON libre y no hay esquema por
recurso, así que mezclar campos sería adivinar. Lo que se decide aquí es cuál
de los cambios queda como el bueno y cuáles se descartan, dejando rastro de
quién lo resolvió.
"""

import operator
from functools import reduce

from django.db.models import Count, Q
from django.db import transaction
from django.utils import timezone

from .models import CambioSincronizacion

Estado = CambioSincronizacion.Estado


def _cola_abierta(finca):
    """Cambios de la finca que todavía esperan sincronizarse."""
    return CambioSincronizacion.objects.filter(
        finca=finca, eliminado_en__isnull=True, sincronizado_en__isnull=True
    ).exclude(estado=Estado.DESCARTADO)


def claves_en_conflicto(finca):
    """Pares ``(recurso, id_objeto)`` con más de un cambio sin sincronizar."""
    grupos = (
        _cola_abierta(finca)
        .values("recurso", "id_objeto")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
    )
    return {(grupo["recurso"], grupo["id_objeto"]) for grupo in grupos}


def detectar_conflictos(finca):
    """Sincroniza el campo ``estado`` con los conflictos que existen ahora.

    Se llama al listar: un cambio deja de estar en conflicto en cuanto el otro
    lado se resuelve o se confirma, y el estado debe reflejarlo sin depender de
    una tarea en segundo plano (el proyecto no tiene cola de tareas).
    """
    claves = claves_en_conflicto(finca)
    cola = _cola_abierta(finca)
    ahora = timezone.now()
    if claves:
        filtro = reduce(
            operator.or_, (Q(recurso=recurso, id_objeto=objeto) for recurso, objeto in claves)
        )
        cola.filter(filtro).exclude(estado=Estado.CONFLICTO).update(
            estado=Estado.CONFLICTO, actualizado_en=ahora
        )
        sin_conflicto = cola.exclude(filtro)
    else:
        sin_conflicto = cola
    sin_conflicto.exclude(estado=Estado.PENDIENTE).update(
        estado=Estado.PENDIENTE, actualizado_en=ahora
    )
    return claves


def grupos_en_conflicto(finca):
    """Conflictos agrupados, con sus cambios del más reciente al más antiguo."""
    detectar_conflictos(finca)
    cambios = (
        CambioSincronizacion.objects.filter(
            finca=finca, eliminado_en__isnull=True, estado=Estado.CONFLICTO
        )
        .select_related("dispositivo", "creado_por")
        .order_by("recurso", "id_objeto", "-creado_en", "-id")
    )
    grupos = {}
    for cambio in cambios:
        grupos.setdefault((cambio.recurso, cambio.id_objeto), []).append(cambio)
    return [
        {
            "recurso": recurso,
            "id_objeto": objeto,
            # Propuesta por omisión: el cambio más reciente, que el usuario
            # puede cambiar al resolver.
            "sugerido": lista[0].pk,
            "cambios": lista,
        }
        for (recurso, objeto), lista in grupos.items()
    ]


def resolver_conflicto(ganador, usuario):
    """Deja ``ganador`` como el cambio válido y descarta los demás del grupo."""
    ahora = timezone.now()
    grupo = _cola_abierta(ganador.finca).filter(
        recurso=ganador.recurso, id_objeto=ganador.id_objeto
    )
    with transaction.atomic():
        grupo.exclude(pk=ganador.pk).update(
            estado=Estado.DESCARTADO, resuelto_por=usuario, resuelto_en=ahora, actualizado_en=ahora
        )
        CambioSincronizacion.objects.filter(pk=ganador.pk).update(
            estado=Estado.PENDIENTE, resuelto_por=usuario, resuelto_en=ahora, actualizado_en=ahora
        )
    ganador.refresh_from_db()
    return ganador
