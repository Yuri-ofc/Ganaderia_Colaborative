from django.db import migrations

# Una medición exige un ModeloIa, y solo el personal de Django puede crear ese
# catálogo por API. Sin estas filas, una instalación nueva no podría registrar
# mediciones manuales desde el panel.
MODELO_MANUAL = ("manual-v1", "Captura y digitación manual, sin modelo de IA")

TIPOS_DE_MEDIDA = (
    ("Altura a la cruz", "cm"),
    ("Perímetro torácico", "cm"),
    ("Longitud corporal", "cm"),
)


def sembrar(apps, schema_editor):
    ModeloIa = apps.get_model("measurements", "ModeloIa")
    TipoMedida = apps.get_model("measurements", "TipoMedida")
    version, calibracion = MODELO_MANUAL
    ModeloIa.objects.get_or_create(
        version=version, defaults={"calibracion": calibracion, "activo": True}
    )
    for nombre, unidad in TIPOS_DE_MEDIDA:
        TipoMedida.objects.get_or_create(nombre=nombre, defaults={"unidad": unidad})


def revertir(apps, schema_editor):
    ModeloIa = apps.get_model("measurements", "ModeloIa")
    TipoMedida = apps.get_model("measurements", "TipoMedida")
    # Solo se retiran si nadie los usó; borrarlos con mediciones asociadas
    # rompería el histórico.
    modelo = ModeloIa.objects.filter(version=MODELO_MANUAL[0], mediciones__isnull=True).first()
    if modelo:
        modelo.delete()
    TipoMedida.objects.filter(
        nombre__in=[nombre for nombre, _ in TIPOS_DE_MEDIDA], registros__isnull=True
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("measurements", "0003_nombres_relacionados")]

    operations = [migrations.RunPython(sembrar, revertir)]
