import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cattle', '0003_nombres_relacionados'),
        ('measurements', '0002_nombres_en_espanol'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='dispositivo',
            name='propietario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='dispositivos', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='medicion',
            name='bovino',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='mediciones', to='cattle.bovino'),
        ),
        migrations.AlterField(
            model_name='medicion',
            name='corrige',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='correcciones', to='measurements.medicion'),
        ),
        migrations.AlterField(
            model_name='medicion',
            name='creado_por',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='mediciones', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='medicion',
            name='dispositivo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='mediciones', to='measurements.dispositivo'),
        ),
        migrations.AlterField(
            model_name='medicion',
            name='modelo_ia',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='mediciones', to='measurements.modeloia'),
        ),
        migrations.AlterField(
            model_name='medidamorfometrica',
            name='medicion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='medidas_morfometricas', to='measurements.medicion'),
        ),
        migrations.AlterField(
            model_name='medidamorfometrica',
            name='tipo_medida',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='registros', to='measurements.tipomedida'),
        ),
        migrations.AlterField(
            model_name='pesaje',
            name='bovino',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pesajes', to='cattle.bovino'),
        ),
        migrations.AlterField(
            model_name='pesaje',
            name='corrige',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='correcciones', to='measurements.pesaje'),
        ),
        migrations.AlterField(
            model_name='pesaje',
            name='creado_por',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pesajes', to=settings.AUTH_USER_MODEL),
        ),
    ]
