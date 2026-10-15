import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Farm',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('name', models.CharField(max_length=120)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='owned_farms', to='accounts.user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FarmMembership',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('role', models.CharField(choices=[('administrator', 'Administrador'), ('operator', 'Operario')], max_length=20)),
                ('farm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='farms.farm')),
                ('invited_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sent_membership_invitations', to='accounts.user')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='farm_memberships', to='accounts.user')),
            ],
            options={
                'constraints': [models.UniqueConstraint(condition=models.Q(('deleted_at__isnull', True)), fields=('farm', 'user'), name='unique_active_farm_membership')],
            },
        ),
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('phone_number', models.CharField(max_length=20)),
                ('role', models.CharField(choices=[('administrator', 'Administrador'), ('operator', 'Operario')], max_length=20)),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('accepted', 'Aceptada'), ('cancelled', 'Cancelada'), ('expired', 'Expirada')], default='pending', max_length=10)),
                ('expires_at', models.DateTimeField()),
                ('accepted_at', models.DateTimeField(blank=True, null=True)),
                ('accepted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='accepted_invitations', to='accounts.user')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_invitations', to='accounts.user')),
                ('farm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='farms.farm')),
            ],
            options={
                'indexes': [models.Index(fields=['status', 'expires_at'], name='invitation_status_expiry_idx')],
                'constraints': [models.UniqueConstraint(condition=models.Q(('deleted_at__isnull', True), ('status', 'pending')), fields=('farm', 'phone_number'), name='unique_pending_farm_invitation'), models.CheckConstraint(condition=models.Q(models.Q(('accepted_at__isnull', False), ('accepted_by__isnull', False), ('status', 'accepted')), models.Q(models.Q(('status', 'accepted'), _negated=True), ('accepted_at__isnull', True), ('accepted_by__isnull', True)), _connector='OR'), name='invitation_acceptance_consistent')],
            },
        ),
    ]
