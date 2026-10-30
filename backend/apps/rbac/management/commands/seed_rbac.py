from django.core.management.base import BaseCommand

from apps.rbac.models import Recurso, Rol


RECURSOS = (
    "RBAC", "FINC", "MIEM", "INVT", "RAZA", "LOTE", "BOVI", "DISP", "MODI", "TIPO", "MEDI", "PESA", "RESP", "SYNC",
)

# Los códigos son deliberadamente de cuatro caracteres para ajustarse al ERD.
PERMISOS_POR_ROL = {
    "SUPR": RECURSOS,
    "PROP": RECURSOS,
    "ADMI": ("FINC", "MIEM", "INVT", "LOTE", "BOVI", "DISP", "MEDI", "PESA", "SYNC"),
    "OPER": ("FINC", "BOVI", "DISP", "MEDI", "PESA", "SYNC"),
}


class Command(BaseCommand):
    help = "Crea o actualiza los roles y recursos RBAC sin crear usuarios ni contraseñas."

    def handle(self, *args, **options):
        recursos = {codigo: Recurso.objects.get_or_create(nombre=codigo)[0] for codigo in RECURSOS}
        for codigo, permisos in PERMISOS_POR_ROL.items():
            rol, _ = Rol.objects.get_or_create(Rol_nombre=codigo)
            rol.recursos.set([recursos[permiso] for permiso in permisos])
        self.stdout.write(self.style.SUCCESS("RBAC preparado: 4 roles y 14 recursos; no se crearon credenciales."))
