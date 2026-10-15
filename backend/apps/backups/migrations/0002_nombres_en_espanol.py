from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backups', '0001_initial'),
        ('farms', '0002_nombres_en_espanol'),
    ]

    operations = [
        migrations.RemoveConstraint(model_name='backup', name='backup_nonempty_size'),
        migrations.RemoveIndex(model_name='backup', name='backup_farm_created_idx'),
        migrations.RenameModel(old_name='Backup', new_name='Respaldo'),
        migrations.RenameField(model_name='respaldo', old_name='created_at', new_name='creado_en'),
        migrations.RenameField(model_name='respaldo', old_name='updated_at', new_name='actualizado_en'),
        migrations.RenameField(model_name='respaldo', old_name='deleted_at', new_name='eliminado_en'),
        migrations.RenameField(model_name='respaldo', old_name='farm', new_name='finca'),
        migrations.RenameField(model_name='respaldo', old_name='created_by', new_name='creado_por'),
        migrations.RenameField(
            model_name='respaldo', old_name='storage_url', new_name='url_almacenamiento'
        ),
        migrations.RenameField(model_name='respaldo', old_name='checksum', new_name='suma_verificacion'),
        migrations.RenameField(model_name='respaldo', old_name='size_bytes', new_name='tamano_bytes'),
        migrations.RenameField(model_name='respaldo', old_name='encrypted', new_name='cifrado'),
        migrations.AddConstraint(
            model_name='respaldo',
            constraint=models.CheckConstraint(
                condition=models.Q(('tamano_bytes__gt', 0)), name='respaldo_tamano_positivo'
            ),
        ),
        migrations.AddIndex(
            model_name='respaldo',
            index=models.Index(fields=['finca', 'creado_en'], name='respaldo_finca_creado_idx'),
        ),
    ]
