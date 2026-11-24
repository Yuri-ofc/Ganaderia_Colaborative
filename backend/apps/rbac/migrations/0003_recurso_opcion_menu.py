from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("rbac", "0002_recurso_etiqueta")]

    operations = [
        migrations.AddField(
            model_name="recurso",
            name="opcion_menu",
            field=models.BooleanField(default=False),
        ),
    ]
