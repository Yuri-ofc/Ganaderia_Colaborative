from django.db import migrations, models


VALORES = {
    'membresia': {'rol': {'administrator': 'administrador', 'operator': 'operario'}},
    'invitacion': {
        'rol': {'administrator': 'administrador', 'operator': 'operario'},
        'estado': {
            'pending': 'pendiente',
            'accepted': 'aceptada',
            'cancelled': 'cancelada',
            'expired': 'expirada',
        },
    },
}


def traducir(apps, schema_editor):
    for modelo, campos in VALORES.items():
        Modelo = apps.get_model('farms', modelo)
        for campo, equivalencias in campos.items():
            for antiguo, nuevo in equivalencias.items():
                Modelo.objects.filter(**{campo: antiguo}).update(**{campo: nuevo})


def revertir(apps, schema_editor):
    for modelo, campos in VALORES.items():
        Modelo = apps.get_model('farms', modelo)
        for campo, equivalencias in campos.items():
            for antiguo, nuevo in equivalencias.items():
                Modelo.objects.filter(**{campo: nuevo}).update(**{campo: antiguo})


class Migration(migrations.Migration):

    dependencies = [
        ('farms', '0001_initial'),
        ('accounts', '0002_nombres_en_espanol'),
        ('cattle', '0001_initial'),
        ('backups', '0001_initial'),
        ('sync', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(model_name='farmmembership', name='unique_active_farm_membership'),
        migrations.RemoveConstraint(model_name='invitation', name='unique_pending_farm_invitation'),
        migrations.RemoveConstraint(model_name='invitation', name='invitation_acceptance_consistent'),
        migrations.RemoveIndex(model_name='invitation', name='invitation_status_expiry_idx'),
        migrations.RenameModel(old_name='Farm', new_name='Finca'),
        migrations.RenameModel(old_name='FarmMembership', new_name='Membresia'),
        migrations.RenameModel(old_name='Invitation', new_name='Invitacion'),
        migrations.RenameField(model_name='finca', old_name='created_at', new_name='creado_en'),
        migrations.RenameField(model_name='finca', old_name='updated_at', new_name='actualizado_en'),
        migrations.RenameField(model_name='finca', old_name='deleted_at', new_name='eliminado_en'),
        migrations.RenameField(model_name='finca', old_name='owner', new_name='propietario'),
        migrations.RenameField(model_name='finca', old_name='name', new_name='nombre'),
        migrations.RenameField(model_name='finca', old_name='location', new_name='ubicacion'),
        migrations.RenameField(model_name='membresia', old_name='created_at', new_name='creado_en'),
        migrations.RenameField(model_name='membresia', old_name='updated_at', new_name='actualizado_en'),
        migrations.RenameField(model_name='membresia', old_name='deleted_at', new_name='eliminado_en'),
        migrations.RenameField(model_name='membresia', old_name='farm', new_name='finca'),
        migrations.RenameField(model_name='membresia', old_name='user', new_name='usuario'),
        migrations.RenameField(model_name='membresia', old_name='role', new_name='rol'),
        migrations.RenameField(model_name='membresia', old_name='invited_by', new_name='invitado_por'),
        migrations.RenameField(model_name='invitacion', old_name='created_at', new_name='creado_en'),
        migrations.RenameField(model_name='invitacion', old_name='updated_at', new_name='actualizado_en'),
        migrations.RenameField(model_name='invitacion', old_name='deleted_at', new_name='eliminado_en'),
        migrations.RenameField(model_name='invitacion', old_name='farm', new_name='finca'),
        migrations.RenameField(model_name='invitacion', old_name='phone_number', new_name='telefono'),
        migrations.RenameField(model_name='invitacion', old_name='role', new_name='rol'),
        migrations.RenameField(model_name='invitacion', old_name='status', new_name='estado'),
        migrations.RenameField(model_name='invitacion', old_name='expires_at', new_name='expira_en'),
        migrations.RenameField(model_name='invitacion', old_name='created_by', new_name='creado_por'),
        migrations.RenameField(model_name='invitacion', old_name='accepted_by', new_name='aceptado_por'),
        migrations.RenameField(model_name='invitacion', old_name='accepted_at', new_name='aceptado_en'),
        migrations.AlterField(
            model_name='membresia',
            name='rol',
            field=models.CharField(
                choices=[('administrador', 'Administrador'), ('operario', 'Operario')], max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='invitacion',
            name='rol',
            field=models.CharField(
                choices=[('administrador', 'Administrador'), ('operario', 'Operario')], max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='invitacion',
            name='estado',
            field=models.CharField(
                choices=[
                    ('pendiente', 'Pendiente'),
                    ('aceptada', 'Aceptada'),
                    ('cancelada', 'Cancelada'),
                    ('expirada', 'Expirada'),
                ],
                default='pendiente',
                max_length=10,
            ),
        ),
        migrations.RunPython(traducir, revertir),
        migrations.AddConstraint(
            model_name='membresia',
            constraint=models.UniqueConstraint(
                condition=models.Q(('eliminado_en__isnull', True)),
                fields=('finca', 'usuario'),
                name='membresia_activa_unica_por_finca',
            ),
        ),
        migrations.AddConstraint(
            model_name='invitacion',
            constraint=models.UniqueConstraint(
                condition=models.Q(('eliminado_en__isnull', True), ('estado', 'pendiente')),
                fields=('finca', 'telefono'),
                name='invitacion_pendiente_unica_por_finca',
            ),
        ),
        migrations.AddConstraint(
            model_name='invitacion',
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(('aceptado_en__isnull', False), ('aceptado_por__isnull', False), ('estado', 'aceptada')),
                    models.Q(
                        models.Q(('estado', 'aceptada'), _negated=True),
                        ('aceptado_en__isnull', True),
                        ('aceptado_por__isnull', True),
                    ),
                    _connector='OR',
                ),
                name='invitacion_aceptacion_consistente',
            ),
        ),
        migrations.AddIndex(
            model_name='invitacion',
            index=models.Index(fields=['estado', 'expira_en'], name='invitacion_estado_expira_idx'),
        ),
    ]
