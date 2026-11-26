"""Respaldos, exportaciones y restauración de los datos de una finca.

El respaldo es un volcado JSON de las filas de la finca, cifrado opcionalmente
con Fernet y guardado en ``settings.RESPALDOS_DIR``. La exportación es otra
cosa: datos legibles (CSV o JSON) para usarlos fuera del sistema, sin cifrar y
sin servir para restaurar.
"""

import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

from django.conf import settings
from django.core import serializers as serializadores_django
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.cattle.models import Bovino, MovimientoPotrero, Potrero
from apps.farms.models import Invitacion, Membresia
from apps.measurements.models import Medicion, MedidaMorfometrica, Pesaje
from apps.sync.models import CambioSincronizacion
from apps.vision.models import CapturaVision

from .models import Respaldo

VERSION_FORMATO = "1.0"


def _fernet():
    from cryptography.fernet import Fernet

    clave = settings.RESPALDO_CLAVE_CIFRADO
    if not clave:
        raise ValidationError(
            {
                "cifrado": "Falta BACKUP_ENCRYPTION_KEY en el entorno. Configúrela o "
                "genere el respaldo sin cifrado."
            }
        )
    try:
        return Fernet(clave.encode())
    except (ValueError, TypeError) as error:
        raise ValidationError(
            {"cifrado": "BACKUP_ENCRYPTION_KEY no es una clave Fernet válida."}
        ) from error


def _conjuntos_de_finca(finca):
    """Filas que pertenecen a la finca, en orden de dependencia.

    Se escribe el respaldo en este orden y se borra en el inverso, de modo que
    ningún ``on_delete=PROTECT`` quede apuntando a una fila ya eliminada.
    """
    return (
        (Membresia, Membresia.objects.filter(finca=finca)),
        (Invitacion, Invitacion.objects.filter(finca=finca)),
        (Potrero, Potrero.objects.filter(finca=finca)),
        (Bovino, Bovino.objects.filter(finca=finca)),
        (MovimientoPotrero, MovimientoPotrero.objects.filter(bovino__finca=finca)),
        (Medicion, Medicion.objects.filter(bovino__finca=finca)),
        (MedidaMorfometrica, MedidaMorfometrica.objects.filter(medicion__bovino__finca=finca)),
        (Pesaje, Pesaje.objects.filter(bovino__finca=finca)),
        (CapturaVision, CapturaVision.objects.filter(bovino__finca=finca)),
        (CambioSincronizacion, CambioSincronizacion.objects.filter(finca=finca)),
    )


def _serializar_finca(finca):
    objetos = [finca]
    for _modelo, consulta in _conjuntos_de_finca(finca):
        objetos.extend(consulta.order_by("creado_en", "id"))
    return serializadores_django.serialize("json", objetos, indent=1)


def _ruta_absoluta(respaldo):
    return Path(settings.RESPALDOS_DIR) / respaldo.ruta_relativa


def generar_respaldo(finca, usuario, *, cifrado=True, base_url=""):
    """Escribe el archivo de respaldo y registra sus metadatos verificables."""
    datos = _serializar_finca(finca).encode("utf-8")
    if cifrado:
        datos = _fernet().encrypt(datos)

    respaldo = Respaldo(finca=finca, creado_por=usuario, version=VERSION_FORMATO, cifrado=cifrado)
    respaldo.ruta_relativa = f"{finca.pk}/{respaldo.pk}.json{'.enc' if cifrado else ''}"
    destino = _ruta_absoluta(respaldo)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(datos)

    respaldo.suma_verificacion = hashlib.sha256(datos).hexdigest()
    respaldo.tamano_bytes = len(datos)
    descarga = reverse("backup-download", args=[respaldo.pk])
    respaldo.url_almacenamiento = f"{base_url.rstrip('/')}{descarga}" if base_url else descarga
    respaldo.save()
    return respaldo


def verificar_integridad(respaldo):
    """True si el archivo existe y su sha256 sigue coincidiendo."""
    ruta = _ruta_absoluta(respaldo)
    if not respaldo.ruta_relativa or not ruta.is_file():
        return False
    return hashlib.sha256(ruta.read_bytes()).hexdigest() == respaldo.suma_verificacion


def leer_contenido(respaldo):
    """Contenido JSON del respaldo, verificado y descifrado."""
    if not verificar_integridad(respaldo):
        raise ValidationError(
            {"suma_verificacion": "El archivo del respaldo no existe o fue alterado."}
        )
    datos = _ruta_absoluta(respaldo).read_bytes()
    if not respaldo.cifrado:
        return datos.decode("utf-8")
    from cryptography.fernet import InvalidToken

    try:
        return _fernet().decrypt(datos).decode("utf-8")
    except InvalidToken as error:
        raise ValidationError(
            {
                "cifrado": "No se pudo descifrar el respaldo con la clave actual. "
                "Debe usarse la misma BACKUP_ENCRYPTION_KEY con la que se generó."
            }
        ) from error


def bytes_para_descarga(respaldo):
    """Archivo tal cual está en disco, tras comprobar su integridad."""
    if not verificar_integridad(respaldo):
        raise ValidationError(
            {"suma_verificacion": "El archivo del respaldo no existe o fue alterado."}
        )
    return _ruta_absoluta(respaldo).read_bytes()


def restaurar_respaldo(respaldo, usuario):
    """Reemplaza los datos de la finca por los del respaldo, todo o nada.

    Lo creado después del respaldo se pierde: es el sentido de restaurar, y la
    interfaz lo confirma antes de llamar aquí. Las filas conservan su UUID, así
    que se reinsertan con la misma identidad que tenían.
    """
    contenido = leer_contenido(respaldo)
    objetos = list(serializadores_django.deserialize("json", contenido))
    conjuntos = _conjuntos_de_finca(respaldo.finca)

    with transaction.atomic():
        # Las correcciones se apuntan entre sí con PROTECT; sin romper el
        # enlace, el borrado del histórico se rechazaría a sí mismo.
        Medicion.objects.filter(bovino__finca=respaldo.finca).update(corrige=None)
        Pesaje.objects.filter(bovino__finca=respaldo.finca).update(corrige=None)
        for _modelo, consulta in reversed(conjuntos):
            consulta.delete()
        for objeto in objetos:
            objeto.save()

    conteo = {}
    for modelo, consulta in _conjuntos_de_finca(respaldo.finca):
        conteo[modelo._meta.model_name] = consulta.count()
    return conteo


# --- Exportaciones ----------------------------------------------------------

def _filas_potreros(finca):
    consulta = Potrero.objects.filter(finca=finca, eliminado_en__isnull=True).order_by("nombre")
    return ["nombre", "creado_en"], [[p.nombre, p.creado_en.isoformat()] for p in consulta]


def _filas_miembros(finca):
    consulta = (
        Membresia.objects.filter(finca=finca, eliminado_en__isnull=True)
        .select_related("usuario")
        .order_by("usuario__username")
    )
    return (
        ["usuario", "email", "rol", "desde"],
        [[m.usuario.username, m.usuario.email, m.rol, m.creado_en.isoformat()] for m in consulta],
    )


def _filas_bovinos(finca):
    consulta = (
        Bovino.objects.filter(finca=finca, eliminado_en__isnull=True)
        .select_related("raza", "potrero")
        .order_by("arete")
    )
    return (
        ["arete", "raza", "sexo", "categoria_productiva", "estado_fisiologico", "potrero",
         "estado_operativo", "fecha_nacimiento_estimada"],
        [
            [
                b.arete, b.raza.nombre, b.sexo, b.categoria_productiva, b.estado_fisiologico,
                b.potrero.nombre, b.estado_operativo,
                b.fecha_nacimiento_estimada.isoformat() if b.fecha_nacimiento_estimada else "",
            ]
            for b in consulta
        ],
    )


def _filas_mediciones(finca):
    consulta = (
        Medicion.objects.filter(bovino__finca=finca, eliminado_en__isnull=True)
        .select_related("bovino", "modelo_ia")
        .order_by("-capturado_en")
    )
    return (
        ["arete", "capturado_en", "modo_captura", "peso_estimado_kg", "intervalo_min_kg",
         "intervalo_max_kg", "condicion_corporal", "nivel_confianza", "modelo_ia", "corrige_a"],
        [
            [
                m.bovino.arete, m.capturado_en.isoformat(), m.modo_captura, str(m.peso_estimado_kg),
                str(m.intervalo_confianza_min_kg), str(m.intervalo_confianza_max_kg),
                str(m.condicion_corporal), str(m.nivel_confianza), m.modelo_ia.version,
                str(m.corrige_id or ""),
            ]
            for m in consulta
        ],
    )


def _filas_pesajes(finca):
    consulta = (
        Pesaje.objects.filter(bovino__finca=finca, eliminado_en__isnull=True)
        .select_related("bovino")
        .order_by("-pesado_en")
    )
    return (
        ["arete", "pesado_en", "tipo_bascula", "peso_real_kg", "corrige_a"],
        [
            [p.bovino.arete, p.pesado_en.isoformat(), p.tipo_bascula, str(p.peso_real_kg),
             str(p.corrige_id or "")]
            for p in consulta
        ],
    )


CONJUNTOS_EXPORTABLES = {
    "potreros": _filas_potreros,
    "miembros": _filas_miembros,
    "bovinos": _filas_bovinos,
    "mediciones": _filas_mediciones,
    "pesajes": _filas_pesajes,
}


def _csv(encabezados, filas):
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(encabezados)
    escritor.writerows(filas)
    return salida.getvalue().encode("utf-8")


def exportar_finca(finca, *, formato="csv", incluir=()):
    """Devuelve ``(nombre_archivo, tipo_contenido, bytes)`` para descargar.

    Varios conjuntos en CSV no caben en una sola tabla, así que se entregan
    comprimidos; en JSON van todos en un mismo objeto.
    """
    conjuntos = [nombre for nombre in incluir if nombre in CONJUNTOS_EXPORTABLES]
    if not conjuntos:
        raise ValidationError(
            {"incluir": f"Elija al menos un conjunto: {', '.join(CONJUNTOS_EXPORTABLES)}."}
        )
    if formato not in {"csv", "json"}:
        raise ValidationError({"formato": "Formatos admitidos: csv, json."})

    marca = timezone.now().strftime("%Y%m%d-%H%M")
    base = f"export-{finca.nombre[:20].strip().replace(' ', '_')}-{marca}"

    if formato == "json":
        datos = {"finca": finca.nombre, "generado_en": timezone.now().isoformat()}
        for nombre in conjuntos:
            encabezados, filas = CONJUNTOS_EXPORTABLES[nombre](finca)
            datos[nombre] = [dict(zip(encabezados, fila)) for fila in filas]
        contenido = json.dumps(datos, ensure_ascii=False, indent=1).encode("utf-8")
        return f"{base}.json", "application/json", contenido

    if len(conjuntos) == 1:
        encabezados, filas = CONJUNTOS_EXPORTABLES[conjuntos[0]](finca)
        return f"{base}-{conjuntos[0]}.csv", "text/csv; charset=utf-8", _csv(encabezados, filas)

    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w", zipfile.ZIP_DEFLATED) as archivo:
        for nombre in conjuntos:
            encabezados, filas = CONJUNTOS_EXPORTABLES[nombre](finca)
            archivo.writestr(f"{nombre}.csv", _csv(encabezados, filas))
    return f"{base}.zip", "application/zip", memoria.getvalue()
