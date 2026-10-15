from django.db import migrations, models


EQUIVALENCIAS = {'video': 'video', 'photo': 'foto'}


def traducir(apps, schema_editor):
    Medicion = apps.get_model('measurements', 'medicion')
    for antiguo, nuevo in EQUIVALENCIAS.items():
        Medicion.objects.filter(modo_captura=antiguo).update(modo_captura=nuevo)


def revertir(apps, schema_editor):
    Medicion = apps.get_model('measurements', 'medicion')
    for antiguo, nuevo in EQUIVALENCIAS.items():
        Medicion.objects.filter(modo_captura=nuevo).update(modo_captura=antiguo)


class Migration(migrations.Migration):

    dependencies = [
        ('measurements', '0001_initial'),
        ('cattle', '0002_nombres_en_espanol'),
        ('sync', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(model_name='measurement', name='measurement_positive_weight'),
        migrations.RemoveConstraint(model_name='measurement', name='measurement_confidence_interval_valid'),
        migrations.RemoveConstraint(model_name='measurement', name='measurement_positive_body_score'),
        migrations.RemoveConstraint(model_name='measurement', name='measurement_nonnegative_confidence'),
        migrations.RemoveConstraint(
            model_name='morphometricmeasurement', name='unique_active_morphometric_type'
        ),
        migrations.RemoveConstraint(
            model_name='morphometricmeasurement', name='morphometric_nonnegative_value'
        ),
        migrations.RemoveConstraint(model_name='scaleweighing', name='scale_weighing_positive_weight'),
        migrations.RemoveIndex(model_name='measurement', name='measurement_cattle_capture_idx'),
        migrations.RemoveIndex(model_name='scaleweighing', name='scale_weighing_cattle_date_idx'),
        migrations.RenameModel(old_name='Device', new_name='Dispositivo'),
        migrations.RenameModel(old_name='AIModel', new_name='ModeloIa'),
        migrations.RenameModel(old_name='MeasurementType', new_name='TipoMedida'),
        migrations.RenameModel(old_name='Measurement', new_name='Medicion'),
        migrations.RenameModel(old_name='MorphometricMeasurement', new_name='MedidaMorfometrica'),
        migrations.RenameModel(old_name='ScaleWeighing', new_name='Pesaje'),
        migrations.RenameField(model_name='dispositivo', old_name='created_at', new_name='creado_en'),
        migrations.RenameField(model_name='dispositivo', old_name='updated_at', new_name='actualizado_en'),
        migrations.RenameField(model_name='dispositivo', old_name='deleted_at', new_name='eliminado_en'),
        migrations.RenameField(model_name='dispositivo', old_name='owner', new_name='propietario'),
        migrations.RenameField(model_name='dispositivo', old_name='model_name', new_name='modelo'),
        migrations.RenameField(
            model_name='dispositivo', old_name='operating_system', new_name='sistema_operativo'
        ),
        migrations.RenameField(
            model_name='dispositivo', old_name='last_connected_at', new_name='ultima_conexion_en'
        ),
        migrations.RenameField(model_name='modeloia', old_name='created_at', new_name='creado_en'),
        migrations.RenameField(model_name='modeloia', old_name='updated_at', new_name='actualizado_en'),
        migrations.RenameField(model_name='modeloia', old_name='deleted_at', new_name='eliminado_en'),
        migrations.RenameField(model_name='modeloia', old_name='calibration', new_name='calibracion'),
        migrations.RenameField(model_name='modeloia', old_name='active', new_name='activo'),
        migrations.RenameField(model_name='tipomedida', old_name='created_at', new_name='creado_en'),
        migrations.RenameField(model_name='tipomedida', old_name='updated_at', new_name='actualizado_en'),
        migrations.RenameField(model_name='tipomedida', old_name='deleted_at', new_name='eliminado_en'),
        migrations.RenameField(model_name='tipomedida', old_name='name', new_name='nombre'),
        migrations.RenameField(model_name='tipomedida', old_name='unit', new_name='unidad'),
        migrations.RenameField(model_name='medicion', old_name='created_at', new_name='creado_en'),
        migrations.RenameField(model_name='medicion', old_name='updated_at', new_name='actualizado_en'),
        migrations.RenameField(model_name='medicion', old_name='deleted_at', new_name='eliminado_en'),
        migrations.RenameField(model_name='medicion', old_name='cattle', new_name='bovino'),
        migrations.RenameField(model_name='medicion', old_name='created_by', new_name='creado_por'),
        migrations.RenameField(model_name='medicion', old_name='device', new_name='dispositivo'),
        migrations.RenameField(model_name='medicion', old_name='ai_model', new_name='modelo_ia'),
        migrations.RenameField(model_name='medicion', old_name='captured_at', new_name='capturado_en'),
        migrations.RenameField(model_name='medicion', old_name='capture_mode', new_name='modo_captura'),
        migrations.RenameField(
            model_name='medicion', old_name='estimated_weight_kg', new_name='peso_estimado_kg'
        ),
        migrations.RenameField(
            model_name='medicion',
            old_name='confidence_interval_min_kg',
            new_name='intervalo_confianza_min_kg',
        ),
        migrations.RenameField(
            model_name='medicion',
            old_name='confidence_interval_max_kg',
            new_name='intervalo_confianza_max_kg',
        ),
        migrations.RenameField(
            model_name='medicion', old_name='body_condition_score', new_name='condicion_corporal'
        ),
        migrations.RenameField(
            model_name='medicion', old_name='confidence_level', new_name='nivel_confianza'
        ),
        migrations.RenameField(model_name='medicion', old_name='corrects', new_name='corrige'),
        migrations.RenameField(model_name='medidamorfometrica', old_name='created_at', new_name='creado_en'),
        migrations.RenameField(
            model_name='medidamorfometrica', old_name='updated_at', new_name='actualizado_en'
        ),
        migrations.RenameField(
            model_name='medidamorfometrica', old_name='deleted_at', new_name='eliminado_en'
        ),
        migrations.RenameField(model_name='medidamorfometrica', old_name='measurement', new_name='medicion'),
        migrations.RenameField(
            model_name='medidamorfometrica', old_name='measurement_type', new_name='tipo_medida'
        ),
        migrations.RenameField(model_name='medidamorfometrica', old_name='value', new_name='valor'),
        migrations.RenameField(model_name='pesaje', old_name='created_at', new_name='creado_en'),
        migrations.RenameField(model_name='pesaje', old_name='updated_at', new_name='actualizado_en'),
        migrations.RenameField(model_name='pesaje', old_name='deleted_at', new_name='eliminado_en'),
        migrations.RenameField(model_name='pesaje', old_name='cattle', new_name='bovino'),
        migrations.RenameField(model_name='pesaje', old_name='created_by', new_name='creado_por'),
        migrations.RenameField(model_name='pesaje', old_name='weighed_at', new_name='pesado_en'),
        migrations.RenameField(model_name='pesaje', old_name='scale_type', new_name='tipo_bascula'),
        migrations.RenameField(model_name='pesaje', old_name='actual_weight_kg', new_name='peso_real_kg'),
        migrations.RenameField(model_name='pesaje', old_name='corrects', new_name='corrige'),
        migrations.AlterField(
            model_name='medicion',
            name='modo_captura',
            field=models.CharField(choices=[('video', 'Video'), ('foto', 'Foto')], max_length=10),
        ),
        migrations.RunPython(traducir, revertir),
        migrations.AddConstraint(
            model_name='medicion',
            constraint=models.CheckConstraint(
                condition=models.Q(('peso_estimado_kg__gt', 0)), name='medicion_peso_positivo'
            ),
        ),
        migrations.AddConstraint(
            model_name='medicion',
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ('intervalo_confianza_min_kg__gte', 0),
                    ('intervalo_confianza_max_kg__gte', models.F('intervalo_confianza_min_kg')),
                    ('peso_estimado_kg__gte', models.F('intervalo_confianza_min_kg')),
                    ('peso_estimado_kg__lte', models.F('intervalo_confianza_max_kg')),
                ),
                name='medicion_intervalo_confianza_valido',
            ),
        ),
        migrations.AddConstraint(
            model_name='medicion',
            constraint=models.CheckConstraint(
                condition=models.Q(('condicion_corporal__gt', 0)), name='medicion_condicion_positiva'
            ),
        ),
        migrations.AddConstraint(
            model_name='medicion',
            constraint=models.CheckConstraint(
                condition=models.Q(('nivel_confianza__gte', 0)), name='medicion_confianza_no_negativa'
            ),
        ),
        migrations.AddConstraint(
            model_name='medidamorfometrica',
            constraint=models.UniqueConstraint(
                condition=models.Q(('eliminado_en__isnull', True)),
                fields=('medicion', 'tipo_medida'),
                name='medida_morfometrica_tipo_unico',
            ),
        ),
        migrations.AddConstraint(
            model_name='medidamorfometrica',
            constraint=models.CheckConstraint(
                condition=models.Q(('valor__gte', 0)), name='medida_morfometrica_valor_no_negativo'
            ),
        ),
        migrations.AddConstraint(
            model_name='pesaje',
            constraint=models.CheckConstraint(
                condition=models.Q(('peso_real_kg__gt', 0)), name='pesaje_peso_positivo'
            ),
        ),
        migrations.AddIndex(
            model_name='medicion',
            index=models.Index(fields=['bovino', 'capturado_en'], name='medicion_bovino_captura_idx'),
        ),
        migrations.AddIndex(
            model_name='pesaje',
            index=models.Index(fields=['bovino', 'pesado_en'], name='pesaje_bovino_fecha_idx'),
        ),
    ]
