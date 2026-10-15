import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('farms', '0002_nombres_en_espanol'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='finca',
            name='propietario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='fincas_propias', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='invitacion',
            name='aceptado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='invitaciones_aceptadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='invitacion',
            name='creado_por',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='invitaciones_creadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='invitacion',
            name='finca',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitaciones', to='farms.finca'),
        ),
        migrations.AlterField(
            model_name='membresia',
            name='finca',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='membresias', to='farms.finca'),
        ),
        migrations.AlterField(
            model_name='membresia',
            name='invitado_por',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='membresias_invitadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='membresia',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='membresias', to=settings.AUTH_USER_MODEL),
        ),
    ]
