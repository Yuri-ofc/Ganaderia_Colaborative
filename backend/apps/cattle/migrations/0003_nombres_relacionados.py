import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cattle', '0002_nombres_en_espanol'),
        ('farms', '0003_nombres_relacionados'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='bovino',
            name='creado_por',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bovinos_creados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='bovino',
            name='finca',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bovinos', to='farms.finca'),
        ),
        migrations.AlterField(
            model_name='bovino',
            name='perfil_aprobado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='perfiles_aprobados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='bovino',
            name='potrero',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bovinos', to='cattle.potrero'),
        ),
        migrations.AlterField(
            model_name='bovino',
            name='raza',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bovinos', to='cattle.raza'),
        ),
        migrations.AlterField(
            model_name='movimientopotrero',
            name='bovino',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimientos', to='cattle.bovino'),
        ),
        migrations.AlterField(
            model_name='movimientopotrero',
            name='creado_por',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='movimientos_creados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='movimientopotrero',
            name='potrero',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='movimientos', to='cattle.potrero'),
        ),
        migrations.AlterField(
            model_name='potrero',
            name='finca',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='potreros', to='farms.finca'),
        ),
    ]
