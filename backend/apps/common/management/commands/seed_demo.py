import json
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.cattle.models import Bovino, Potrero, Raza
from apps.farms.models import Finca, Membresia
from apps.measurements.models import (
    Dispositivo,
    Medicion,
    MedidaMorfometrica,
    ModeloIa,
    Pesaje,
    TipoMedida,
)

Usuario = get_user_model()


class _Simulacion(Exception):
    pass


def _decimal(valor, posiciones="0.01"):
    return Decimal(str(valor)).quantize(Decimal(posiciones))


class Command(BaseCommand):
    help = "Inserta 100 registros de demostración idempotentes en las tablas de negocio."

    def add_arguments(self, parser):
        parser.add_argument(
            "--catalogo",
            default=None,
            help="Catálogo JSON a usar (por omisión database/fixtures/demo_seed.json).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Calcula lo que se crearía y deshace la transacción al terminar.",
        )

    def handle(self, *args, **opciones):
        ruta = (
            Path(opciones["catalogo"])
            if opciones["catalogo"]
            else Path(settings.DATABASE_FIXTURES_DIR) / "demo_seed.json"
        )
        if not ruta.is_file():
            raise CommandError(f"No se encontró el catálogo de demostración: {ruta}")
        try:
            self.datos = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"El catálogo {ruta} no es JSON válido: {exc}") from exc

        self.espacio = uuid.uuid5(uuid.NAMESPACE_URL, self.datos["espacio_nombres"])
        self.ahora = timezone.now()
        self.creados = {}
        self.sembrados = {}

        try:
            with transaction.atomic():
                self._sembrar()
                if opciones["dry_run"]:
                    raise _Simulacion
        except _Simulacion:
            self._informar(ruta, simulacion=True)
            return
        self._informar(ruta, simulacion=False)

    def _uuid(self, tipo, clave):
        return uuid.uuid5(self.espacio, f"{tipo}:{clave}")

    def _asegurar(self, clase, tipo, clave, /, **campos):
        pk = self._uuid(tipo, clave)
        etiqueta = clase._meta.db_table
        self.sembrados.setdefault(etiqueta, (clase, []))[1].append(pk)
        objeto, creado = clase.objects.get_or_create(pk=pk, defaults=campos)
        self.creados[etiqueta] = self.creados.get(etiqueta, 0) + int(creado)
        return objeto

    def _sembrar(self):
        datos = self.datos
        usuarios = {
            entrada["clave"]: self._asegurar(
                Usuario,
                "usuario",
                entrada["clave"],
                username=entrada["usuario"],
                first_name=entrada.get("nombres", ""),
                last_name=entrada.get("apellidos", ""),
                email=entrada.get("correo", ""),
                telefono=entrada.get("telefono") or None,
                password=make_password(datos["clave_demo"]),
                is_active=True,
                is_staff=entrada.get("es_personal", False),
            )
            for entrada in datos["usuarios"]
        }

        fincas = {
            entrada["clave"]: self._asegurar(
                Finca,
                "finca",
                entrada["clave"],
                propietario=usuarios[entrada["propietario"]],
                nombre=entrada["nombre"],
                ubicacion=entrada.get("ubicacion", ""),
            )
            for entrada in datos["fincas"]
        }

        miembros_por_finca = {clave: [finca.propietario] for clave, finca in fincas.items()}
        administradores_por_finca = {clave: [finca.propietario] for clave, finca in fincas.items()}
        for entrada in datos["membresias"]:
            finca = fincas[entrada["finca"]]
            miembro = usuarios[entrada["usuario"]]
            self._asegurar(
                Membresia,
                "membresia",
                f"{entrada['finca']}:{entrada['usuario']}",
                finca=finca,
                usuario=miembro,
                rol=entrada["rol"],
                invitado_por=finca.propietario,
            )
            miembros_por_finca[entrada["finca"]].append(miembro)
            if entrada["rol"] == Membresia.Rol.ADMINISTRADOR:
                administradores_por_finca[entrada["finca"]].append(miembro)

        razas = [
            self._asegurar(Raza, "raza", entrada["clave"], nombre=entrada["nombre"])
            for entrada in datos["razas"]
        ]

        dispositivos = {
            entrada["clave"]: self._asegurar(
                Dispositivo,
                "dispositivo",
                entrada["clave"],
                propietario=usuarios[entrada["propietario"]],
                modelo=entrada["modelo"],
                sistema_operativo=entrada["sistema_operativo"],
                ultima_conexion_en=self.ahora - timedelta(hours=indice + 1),
            )
            for indice, entrada in enumerate(datos["dispositivos"])
        }

        modelos_ia = [
            self._asegurar(
                ModeloIa,
                "modelo_ia",
                entrada["clave"],
                version=entrada["version"],
                calibracion=entrada["calibracion"],
                activo=entrada.get("activo", True),
            )
            for entrada in datos["modelos_ia"]
        ]

        tipos_medida = [
            self._asegurar(
                TipoMedida,
                "tipo_medida",
                entrada["clave"],
                nombre=entrada["nombre"],
                unidad=entrada["unidad"],
            )
            for entrada in datos["tipos_medida"]
        ]

        parejas_captura = {}
        for clave_finca, miembros in miembros_por_finca.items():
            parejas = [
                (miembro, dispositivo)
                for miembro in miembros
                for dispositivo in dispositivos.values()
                if dispositivo.propietario_id == miembro.pk
            ]
            parejas_captura[clave_finca] = parejas or [(miembros[0], None)]

        bovinos = self._sembrar_bovinos(
            datos, fincas, miembros_por_finca, administradores_por_finca, razas
        )
        mediciones = self._sembrar_mediciones(datos, bovinos, parejas_captura, modelos_ia)
        self._sembrar_morfometricas(datos, mediciones, tipos_medida)
        self._sembrar_pesajes(datos, bovinos, parejas_captura)

    def _sembrar_bovinos(self, datos, fincas, miembros_por_finca, administradores_por_finca, razas):
        perfil = datos["perfil_bovinos"]
        categorias = perfil["categorias_productivas"]
        estados = perfil["estados_fisiologicos"]
        desactivaciones = {
            (entrada["finca"], entrada["indice_arete"]): entrada
            for entrada in perfil.get("desactivados", ())
        }

        creados = []
        contadores = {}
        indice = 0
        for entrada_potrero in datos["potreros"]:
            clave_finca = entrada_potrero["finca"]
            finca = fincas[clave_finca]
            potrero = self._asegurar(
                Potrero, "potrero", entrada_potrero["clave"], finca=finca, nombre=entrada_potrero["nombre"]
            )
            miembros = miembros_por_finca[clave_finca]
            administradores = administradores_por_finca[clave_finca]
            for _ in range(entrada_potrero["bovinos"]):
                numero = contadores.get(clave_finca, 0) + 1
                contadores[clave_finca] = numero
                arete = f"DEM-{numero:03d}"
                hembra = indice % 4 != 3
                desactivacion = desactivaciones.get((clave_finca, numero))

                campos = {
                    "finca": finca,
                    "potrero": potrero,
                    "arete": arete,
                    "raza": razas[indice % len(razas)],
                    "sexo": Bovino.Sexo.HEMBRA if hembra else Bovino.Sexo.MACHO,
                    "categoria_productiva": categorias[indice % len(categorias)],
                    "estado_fisiologico": estados[indice % len(estados)] if hembra else "",
                    "fecha_nacimiento_estimada": (self.ahora - timedelta(days=420 + indice * 37)).date(),
                    "url_foto_perfil": (
                        f"https://demo.g-computacional.local/{clave_finca}/{arete.lower()}.jpg"
                    ),
                    "creado_por": miembros[indice % len(miembros)],
                }
                if desactivacion is not None:
                    campos.update(
                        estado_operativo=desactivacion["estado"],
                        desactivado_en=self.ahora - timedelta(days=15 + indice),
                        motivo_desactivacion=desactivacion["motivo"],
                        perfil_aprobado_por=administradores[indice % len(administradores)],
                    )
                elif indice % 5 == 4:
                    campos.update(estado_operativo=Bovino.EstadoOperativo.PERFIL_PENDIENTE)
                else:
                    campos.update(
                        estado_operativo=Bovino.EstadoOperativo.ACTIVO,
                        perfil_aprobado_por=administradores[indice % len(administradores)],
                    )

                creados.append(
                    (clave_finca, self._asegurar(Bovino, "bovino", f"{clave_finca}:{arete}", **campos))
                )
                indice += 1
        return creados

    def _sembrar_mediciones(self, datos, bovinos, parejas_captura, modelos_ia):
        total = datos["plan"]["mediciones"]
        creadas = []
        for indice, (clave_finca, animal) in enumerate(bovinos[:total]):
            parejas = parejas_captura[clave_finca]
            miembro, dispositivo = parejas[indice % len(parejas)]
            if dispositivo is None:
                continue
            estimado = _decimal(235 + (indice * 17) % 190)
            creadas.append(
                self._asegurar(
                    Medicion,
                    "medicion",
                    f"{clave_finca}:{animal.arete}:1",
                    bovino=animal,
                    creado_por=miembro,
                    dispositivo=dispositivo,
                    modelo_ia=modelos_ia[indice % len(modelos_ia)],
                    capturado_en=self.ahora - timedelta(days=total - indice, hours=indice % 12),
                    modo_captura=(
                        Medicion.ModoCaptura.VIDEO if indice % 2 == 0 else Medicion.ModoCaptura.FOTO
                    ),
                    peso_estimado_kg=estimado,
                    intervalo_confianza_min_kg=estimado - _decimal(12.5),
                    intervalo_confianza_max_kg=estimado + _decimal(14.5),
                    condicion_corporal=_decimal(2.5 + (indice % 5) * 0.4, "0.1"),
                    nivel_confianza=_decimal(82.5 + (indice % 7)),
                )
            )
        return creadas

    def _sembrar_morfometricas(self, datos, mediciones, tipos_medida):
        total = datos["plan"]["medidas_morfometricas"]
        if not mediciones or not tipos_medida:
            return
        por_medicion = max(1, min(len(tipos_medida), total // max(1, len(mediciones)) or 2))
        creadas = 0
        for indice, medicion in enumerate(mediciones):
            for desplazamiento in range(por_medicion):
                if creadas >= total:
                    return
                tipo = tipos_medida[(indice + desplazamiento) % len(tipos_medida)]
                self._asegurar(
                    MedidaMorfometrica,
                    "medida_morfometrica",
                    f"{medicion.pk}:{tipo.nombre}",
                    medicion=medicion,
                    tipo_medida=tipo,
                    valor=_decimal(148 + (indice * 7 + desplazamiento * 23) % 60),
                )
                creadas += 1

    def _sembrar_pesajes(self, datos, bovinos, parejas_captura):
        total = datos["plan"]["pesajes"]
        basculas = ("Báscula fija demo", "Báscula móvil demo")
        for indice, (clave_finca, animal) in enumerate(bovinos[:total]):
            parejas = parejas_captura[clave_finca]
            miembro, _ = parejas[indice % len(parejas)]
            self._asegurar(
                Pesaje,
                "pesaje",
                f"{clave_finca}:{animal.arete}:1",
                bovino=animal,
                creado_por=miembro,
                pesado_en=self.ahora - timedelta(days=total - indice, hours=6),
                tipo_bascula=basculas[indice % len(basculas)],
                peso_real_kg=_decimal(240 + (indice * 23) % 170),
            )

    def _informar(self, ruta, *, simulacion):
        ancho = max(len(etiqueta) for etiqueta in self.creados) if self.creados else 0
        total_creados = sum(self.creados.values())
        total_presentes = 0
        self.stdout.write(f"Catálogo: {ruta}")
        self.stdout.write("")
        self.stdout.write(f"{'tabla'.ljust(ancho)}  creados  presentes")
        for etiqueta in sorted(self.creados):
            modelo, ids = self.sembrados[etiqueta]
            presentes = len(ids) if simulacion else modelo.objects.filter(pk__in=ids).count()
            total_presentes += presentes
            self.stdout.write(
                f"{etiqueta.ljust(ancho)}  {self.creados[etiqueta]:>7}  {presentes:>9}"
            )
        self.stdout.write("")
        esperado = self.datos.get("total_esperado")
        self.stdout.write(f"{'TOTAL creados'.ljust(ancho)}  {total_creados:>7}  {total_presentes:>9}")
        if simulacion:
            self.stdout.write(
                self.style.WARNING("Simulación: la transacción se deshizo, no se guardó nada.")
            )
            return
        if esperado is not None and total_presentes != esperado:
            raise CommandError(
                f"Se esperaban {esperado} registros de demostración y hay {total_presentes}."
            )
        if total_creados == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Los {total_presentes} registros de demostración ya existían; nada que crear."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Se crearon {total_creados} registros; {total_presentes} de demostración en total."
                )
            )
