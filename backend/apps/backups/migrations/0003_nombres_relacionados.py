import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backups', '0002_nombres_en_espanol'),
        ('farms', '0003_nombres_relacionados'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='respaldo',
            name='creado_por',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='respaldos', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='respaldo',
            name='finca',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='respaldos', to='farms.finca'),
        ),
    ]
