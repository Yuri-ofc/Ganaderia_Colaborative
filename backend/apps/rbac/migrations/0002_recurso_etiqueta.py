from django.db import migrations, models

# Etiquetas que hoy muestra el menú del dashboard para cada código.
ETIQUETAS_INICIALES = {
    "RBAC": "Control de acceso",
    "FINC": "Fincas",
    "BOVI": "Bovinos",
    "MIEM": "Equipo",
    "INVT": "Invitaciones",
    "VCOM": "Visión computacional",
    "SYNC": "Sincronización",
    "RESP": "Respaldos",
    "EXPO": "Exportaciones",
    "RECU": "Recuperación",
}


def cargar_etiquetas(apps, schema_editor):
    Recurso = apps.get_model("rbac", "Recurso")
    for recurso in Recurso.objects.filter(etiqueta=""):
        recurso.etiqueta = ETIQUETAS_INICIALES.get(recurso.nombre, recurso.nombre)
        recurso.save(update_fields=("etiqueta",))


class Migration(migrations.Migration):
    dependencies = [("rbac", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="recurso",
            name="etiqueta",
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.RunPython(cargar_etiquetas, migrations.RunPython.noop),
    ]
