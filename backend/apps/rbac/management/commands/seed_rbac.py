from django.core.management.base import BaseCommand

from apps.rbac.models import Recurso, Rol


RECURSOS = (
    "RBAC", "FINC", "MIEM", "INVT", "LOTE", "BOVI", "MEDI", "PESA", "RESP", "SYNC",
    "VCOM", "EXPO", "RECU",
)

# Los códigos son deliberadamente de cuatro caracteres para ajustarse al ERD.
PERMISOS_POR_ROL = {
    "SUPR": RECURSOS,
    "PROP": ("FINC", "MIEM", "INVT", "LOTE", "BOVI", "MEDI", "PESA", "RESP", "SYNC", "EXPO", "RECU"),
    "ADMI": ("FINC", "MIEM", "INVT", "LOTE", "BOVI", "MEDI", "PESA", "SYNC"),
    "OPER": ("FINC", "LOTE", "BOVI", "MEDI", "PESA", "SYNC"),
}


class Command(BaseCommand):
    help = "Crea o actualiza los roles y recursos RBAC sin crear usuarios ni contraseñas."

    def handle(self, *args, **options):
        recursos = {codigo: Recurso.objects.get_or_create(nombre=codigo)[0] for codigo in RECURSOS}
        for codigo, permisos in PERMISOS_POR_ROL.items():
            rol, _ = Rol.objects.get_or_create(Rol_nombre=codigo)
            rol.recursos.set([recursos[permiso] for permiso in permisos])
        self.stdout.write(self.style.SUCCESS("RBAC actualizado: 4 roles y 13 recursos administrados; no se crearon credenciales."))
