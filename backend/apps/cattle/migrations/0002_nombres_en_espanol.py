from django.db import migrations, models


VALORES = {
    'sexo': {'female': 'hembra', 'male': 'macho'},
    'estado_operativo': {
        'pending_profile': 'perfil_pendiente',
        'active': 'activo',
        'sold': 'vendido',
        'deceased': 'muerto',
        'retired': 'retirado',
    },
}


def traducir(apps, schema_editor):
    Bovino = apps.get_model('cattle', 'bovino')
    for campo, equivalencias in VALORES.items():
        for antiguo, nuevo in equivalencias.items():
            Bovino.objects.filter(**{campo: antiguo}).update(**{campo: nuevo})


def revertir(apps, schema_editor):
    Bovino = apps.get_model('cattle', 'bovino')
    for campo, equivalencias in VALORES.items():
        for antiguo, nuevo in equivalencias.items():
            Bovino.objects.filter(**{campo: nuevo}).update(**{campo: antiguo})


class Migration(migrations.Migration):

    dependencies = [
        ('cattle', '0001_initial'),
        ('farms', '0002_nombres_en_espanol'),
        ('measurements', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(model_name='breed', name='unique_active_breed_name'),
        migrations.RemoveConstraint(model_name='lot', name='unique_active_lot_per_farm'),
        migrations.RemoveConstraint(model_name='cattle', name='unique_active_ear_tag_per_farm'),
        migrations.RemoveConstraint(model_name='cattle', name='cattle_deactivation_has_reason'),
        migrations.RemoveConstraint(model_name='lotmovement', name='lot_movement_dates_ordered'),
        migrations.RemoveConstraint(model_name='lotmovement', name='unique_open_lot_movement'),
        migrations.RemoveIndex(model_name='cattle', name='cattle_farm_status_idx'),
        migrations.RemoveIndex(model_name='lotmovement', name='lot_movement_cattle_start_idx'),
        migrations.RenameModel(old_name='Breed', new_name='Raza'),
        migrations.RenameModel(old_name='Lot', new_name='Potrero'),
        migrations.RenameModel(old_name='Cattle', new_name='Bovino'),
        migrations.RenameModel(old_name='LotMovement', new_name='MovimientoPotrero'),
        migrations.RenameField(model_name='raza', old_name='created_at', new_name='creado_en'),
        migrations.RenameField(model_name='raza', old_name='updated_at', new_name='actualizado_en'),
        migrations.RenameField(model_name='raza', old_name='deleted_at', new_name='eliminado_en'),
        migrations.RenameField(model_name='raza', old_name='name', new_name='nombre'),
        migrations.RenameField(model_name='potrero', old_name='created_at', new_name='creado_en'),
        migrations.RenameField(model_name='potrero', old_name='updated_at', new_name='actualizado_en'),
        migrations.RenameField(model_name='potrero', old_name='deleted_at', new_name='eliminado_en'),
        migrations.RenameField(model_name='potrero', old_name='farm', new_name='finca'),
        migrations.RenameField(model_name='potrero', old_name='name', new_name='nombre'),
        migrations.RenameField(model_name='bovino', old_name='created_at', new_name='creado_en'),
        migrations.RenameField(model_name='bovino', old_name='updated_at', new_name='actualizado_en'),
        migrations.RenameField(model_name='bovino', old_name='deleted_at', new_name='eliminado_en'),
        migrations.RenameField(model_name='bovino', old_name='farm', new_name='finca'),
        migrations.RenameField(model_name='bovino', old_name='lot', new_name='potrero'),
        migrations.RenameField(model_name='bovino', old_name='ear_tag', new_name='arete'),
        migrations.RenameField(model_name='bovino', old_name='breed', new_name='raza'),
        migrations.RenameField(model_name='bovino', old_name='sex', new_name='sexo'),
        migrations.RenameField(
            model_name='bovino', old_name='productive_category', new_name='categoria_productiva'
        ),
        migrations.RenameField(
            model_name='bovino', old_name='physiological_status', new_name='estado_fisiologico'
        ),
        migrations.RenameField(
            model_name='bovino', old_name='estimated_birth_date', new_name='fecha_nacimiento_estimada'
        ),
        migrations.RenameField(
            model_name='bovino', old_name='operational_status', new_name='estado_operativo'
        ),
        migrations.RenameField(model_name='bovino', old_name='profile_photo_url', new_name='url_foto_perfil'),
        migrations.RenameField(
            model_name='bovino', old_name='profile_approved_by', new_name='perfil_aprobado_por'
        ),
        migrations.RenameField(model_name='bovino', old_name='created_by', new_name='creado_por'),
        migrations.RenameField(model_name='bovino', old_name='deactivated_at', new_name='desactivado_en'),
        migrations.RenameField(
            model_name='bovino', old_name='deactivation_reason', new_name='motivo_desactivacion'
        ),
        migrations.RenameField(model_name='movimientopotrero', old_name='created_at', new_name='creado_en'),
        migrations.RenameField(
            model_name='movimientopotrero', old_name='updated_at', new_name='actualizado_en'
        ),
        migrations.RenameField(model_name='movimientopotrero', old_name='deleted_at', new_name='eliminado_en'),
        migrations.RenameField(model_name='movimientopotrero', old_name='cattle', new_name='bovino'),
        migrations.RenameField(model_name='movimientopotrero', old_name='lot', new_name='potrero'),
        migrations.RenameField(model_name='movimientopotrero', old_name='started_at', new_name='iniciado_en'),
        migrations.RenameField(model_name='movimientopotrero', old_name='ended_at', new_name='finalizado_en'),
        migrations.RenameField(model_name='movimientopotrero', old_name='created_by', new_name='creado_por'),
        migrations.AlterField(
            model_name='bovino',
            name='sexo',
            field=models.CharField(choices=[('hembra', 'Hembra'), ('macho', 'Macho')], max_length=10),
        ),
        migrations.AlterField(
            model_name='bovino',
            name='estado_operativo',
            field=models.CharField(
                choices=[
                    ('perfil_pendiente', 'Pendiente de perfil'),
                    ('activo', 'Activo'),
                    ('vendido', 'Vendido'),
                    ('muerto', 'Muerto'),
                    ('retirado', 'Retirado'),
                ],
                default='perfil_pendiente',
                max_length=20,
            ),
        ),
        migrations.RunPython(traducir, revertir),
        migrations.AddConstraint(
            model_name='raza',
            constraint=models.UniqueConstraint(
                condition=models.Q(('eliminado_en__isnull', True)),
                fields=('nombre',),
                name='raza_activa_nombre_unico',
            ),
        ),
        migrations.AddConstraint(
            model_name='potrero',
            constraint=models.UniqueConstraint(
                condition=models.Q(('eliminado_en__isnull', True)),
                fields=('finca', 'nombre'),
                name='potrero_activo_unico_por_finca',
            ),
        ),
        migrations.AddConstraint(
            model_name='bovino',
            constraint=models.UniqueConstraint(
                condition=models.Q(('eliminado_en__isnull', True)),
                fields=('finca', 'arete'),
                name='arete_activo_unico_por_finca',
            ),
        ),
        migrations.AddConstraint(
            model_name='bovino',
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ('desactivado_en__isnull', True),
                    models.Q(('motivo_desactivacion', ''), _negated=True),
                    _connector='OR',
                ),
                name='bovino_desactivacion_con_motivo',
            ),
        ),
        migrations.AddConstraint(
            model_name='movimientopotrero',
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ('finalizado_en__isnull', True),
                    ('finalizado_en__gte', models.F('iniciado_en')),
                    _connector='OR',
                ),
                name='movimiento_fechas_ordenadas',
            ),
        ),
        migrations.AddConstraint(
            model_name='movimientopotrero',
            constraint=models.UniqueConstraint(
                condition=models.Q(('eliminado_en__isnull', True), ('finalizado_en__isnull', True)),
                fields=('bovino',),
                name='movimiento_abierto_unico',
            ),
        ),
        migrations.AddIndex(
            model_name='bovino',
            index=models.Index(fields=['finca', 'estado_operativo'], name='bovino_finca_estado_idx'),
        ),
        migrations.AddIndex(
            model_name='movimientopotrero',
            index=models.Index(fields=['bovino', 'iniciado_en'], name='movimiento_bovino_inicio_idx'),
        ),
    ]
