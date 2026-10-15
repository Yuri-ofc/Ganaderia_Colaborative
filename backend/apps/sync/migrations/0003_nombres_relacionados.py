import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('farms', '0003_nombres_relacionados'),
        ('measurements', '0003_nombres_relacionados'),
        ('sync', '0002_nombres_en_espanol'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='cambiosincronizacion',
            name='creado_por',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cambios_sincronizacion', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='cambiosincronizacion',
            name='dispositivo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cambios_sincronizacion', to='measurements.dispositivo'),
        ),
        migrations.AlterField(
            model_name='cambiosincronizacion',
            name='finca',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cambios_sincronizacion', to='farms.finca'),
        ),
    ]
