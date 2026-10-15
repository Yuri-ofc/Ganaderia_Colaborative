from django.db import migrations, models


EQUIVALENCIAS = {'create': 'crear', 'update': 'actualizar', 'delete': 'eliminar'}


def traducir(apps, schema_editor):
    Cambio = apps.get_model('sync', 'cambiosincronizacion')
    for antiguo, nuevo in EQUIVALENCIAS.items():
        Cambio.objects.filter(accion=antiguo).update(accion=nuevo)


def revertir(apps, schema_editor):
    Cambio = apps.get_model('sync', 'cambiosincronizacion')
    for antiguo, nuevo in EQUIVALENCIAS.items():
        Cambio.objects.filter(accion=nuevo).update(accion=antiguo)


class Migration(migrations.Migration):

    dependencies = [
        ('sync', '0001_initial'),
        ('measurements', '0002_nombres_en_espanol'),
    ]

    operations = [
        migrations.RemoveConstraint(model_name='syncchange', name='unique_device_client_change'),
        migrations.RemoveConstraint(model_name='syncchange', name='sync_time_after_creation'),
        migrations.RemoveIndex(model_name='syncchange', name='sync_farm_created_idx'),
        migrations.RenameModel(old_name='SyncChange', new_name='CambioSincronizacion'),
        migrations.RenameField(
            model_name='cambiosincronizacion', old_name='created_at', new_name='creado_en'
        ),
        migrations.RenameField(
            model_name='cambiosincronizacion', old_name='updated_at', new_name='actualizado_en'
        ),
        migrations.RenameField(
            model_name='cambiosincronizacion', old_name='deleted_at', new_name='eliminado_en'
        ),
        migrations.RenameField(model_name='cambiosincronizacion', old_name='farm', new_name='finca'),
        migrations.RenameField(
            model_name='cambiosincronizacion', old_name='device', new_name='dispositivo'
        ),
        migrations.RenameField(
            model_name='cambiosincronizacion', old_name='created_by', new_name='creado_por'
        ),
        migrations.RenameField(
            model_name='cambiosincronizacion', old_name='client_change_id', new_name='id_cambio_cliente'
        ),
        migrations.RenameField(model_name='cambiosincronizacion', old_name='resource', new_name='recurso'),
        migrations.RenameField(model_name='cambiosincronizacion', old_name='object_id', new_name='id_objeto'),
        migrations.RenameField(model_name='cambiosincronizacion', old_name='action', new_name='accion'),
        migrations.RenameField(model_name='cambiosincronizacion', old_name='payload', new_name='contenido'),
        migrations.RenameField(
            model_name='cambiosincronizacion', old_name='synchronized_at', new_name='sincronizado_en'
        ),
        migrations.AlterField(
            model_name='cambiosincronizacion',
            name='accion',
            field=models.CharField(
                choices=[('crear', 'Crear'), ('actualizar', 'Actualizar'), ('eliminar', 'Eliminar')],
                max_length=10,
            ),
        ),
        migrations.RunPython(traducir, revertir),
        migrations.AddConstraint(
            model_name='cambiosincronizacion',
            constraint=models.UniqueConstraint(
                fields=('dispositivo', 'id_cambio_cliente'), name='cambio_cliente_unico_por_dispositivo'
            ),
        ),
        migrations.AddConstraint(
            model_name='cambiosincronizacion',
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ('sincronizado_en__isnull', True),
                    ('sincronizado_en__gte', models.F('creado_en')),
                    _connector='OR',
                ),
                name='sincronizacion_posterior_a_creacion',
            ),
        ),
        migrations.AddIndex(
            model_name='cambiosincronizacion',
            index=models.Index(fields=['finca', 'creado_en'], name='cambio_finca_creado_idx'),
        ),
    ]
