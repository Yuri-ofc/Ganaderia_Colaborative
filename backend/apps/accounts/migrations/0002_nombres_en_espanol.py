from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('farms', '0001_initial'),
        ('cattle', '0001_initial'),
        ('measurements', '0001_initial'),
        ('backups', '0001_initial'),
        ('sync', '0001_initial'),
    ]

    run_before = [
        ('admin', '0001_initial'),
        ('authtoken', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(model_name='user', name='unique_active_user_phone'),
        migrations.RenameModel(old_name='User', new_name='Usuario'),
        migrations.RenameField(model_name='usuario', old_name='created_at', new_name='creado_en'),
        migrations.RenameField(model_name='usuario', old_name='updated_at', new_name='actualizado_en'),
        migrations.RenameField(model_name='usuario', old_name='deleted_at', new_name='eliminado_en'),
        migrations.RenameField(model_name='usuario', old_name='phone_number', new_name='telefono'),
        migrations.RenameField(
            model_name='usuario', old_name='recovery_phrase_hash', new_name='hash_frase_recuperacion'
        ),
        migrations.AddConstraint(
            model_name='usuario',
            constraint=models.UniqueConstraint(
                condition=models.Q(('eliminado_en__isnull', True), ('telefono__isnull', False)),
                fields=('telefono',),
                name='telefono_usuario_activo_unico',
            ),
        ),
    ]
