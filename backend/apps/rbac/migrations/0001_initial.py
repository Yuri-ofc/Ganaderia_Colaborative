from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [("accounts", "0002_nombres_en_espanol")]

    operations = [
        migrations.CreateModel(
            name="Recurso",
            fields=[
                ("idrecurso", models.AutoField(primary_key=True, serialize=False)),
                ("nombre", models.CharField(max_length=4, unique=True)),
            ],
            options={"db_table": "recurso", "ordering": ("nombre",)},
        ),
        migrations.CreateModel(
            name="Rol",
            fields=[
                ("Rol_ID", models.AutoField(primary_key=True, serialize=False)),
                ("Rol_nombre", models.CharField(max_length=4, unique=True)),
            ],
            options={"db_table": "rol", "ordering": ("Rol_nombre",)},
        ),
        migrations.CreateModel(
            name="UsuarioHasRol",
            fields=[
                ("rol", models.ForeignKey(db_column="Rol_Rol_ID", on_delete=django.db.models.deletion.CASCADE, related_name="asignaciones_usuario", to="rbac.rol")),
                ("usuario", models.ForeignKey(db_column="Usuario_Usua_ID", on_delete=django.db.models.deletion.CASCADE, related_name="asignaciones_rbac", to=settings.AUTH_USER_MODEL)),
                ("pk", models.CompositePrimaryKey("usuario", "rol", blank=True, editable=False, primary_key=True, serialize=False)),
            ],
            options={"db_table": "usuario_has_rol"},
        ),
        migrations.CreateModel(
            name="RolHasRecurso",
            fields=[
                ("recurso", models.ForeignKey(db_column="recurso_idrecurso", on_delete=django.db.models.deletion.CASCADE, related_name="asignaciones_rol", to="rbac.recurso")),
                ("rol", models.ForeignKey(db_column="rol_Rol_ID", on_delete=django.db.models.deletion.CASCADE, related_name="asignaciones_recurso", to="rbac.rol")),
                ("pk", models.CompositePrimaryKey("rol", "recurso", blank=True, editable=False, primary_key=True, serialize=False)),
            ],
            options={"db_table": "rol_has_recurso"},
        ),
        migrations.AddField(
            model_name="rol",
            name="recursos",
            field=models.ManyToManyField(blank=True, related_name="roles", through="rbac.RolHasRecurso", to="rbac.recurso"),
        ),
    ]
