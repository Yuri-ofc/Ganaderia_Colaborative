from django.core.management.base import BaseCommand

from apps.rbac.models import Recurso, Rol


RECURSOS = (
    "RBAC", "FINC", "MIEM", "INVT", "LOTE", "BOVI", "MEDI", "PESA", "RESP", "SYNC",
    "VCOM", "EXPO", "RECU",
)

# Texto inicial de cada opción del menú (editable luego desde el panel RBAC).
ETIQUETAS_INICIALES = {
    "RBAC": "Control de acceso", "FINC": "Fincas", "BOVI": "Bovinos", "MIEM": "Equipo",
    "INVT": "Invitaciones", "VCOM": "Visión computacional", "SYNC": "Sincronización",
    "RESP": "Respaldos", "EXPO": "Exportaciones", "RECU": "Recuperación",
}

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
        # La etiqueta solo se rellena si está vacía: lo que el administrador
        # haya cambiado desde Control de acceso nunca se sobrescribe.
        for codigo, recurso in recursos.items():
            if not recurso.etiqueta:
                recurso.etiqueta = ETIQUETAS_INICIALES.get(codigo, codigo)
                recurso.save(update_fields=("etiqueta",))
        for codigo, permisos in PERMISOS_POR_ROL.items():
            rol, _ = Rol.objects.get_or_create(Rol_nombre=codigo)
            rol.recursos.set([recursos[permiso] for permiso in permisos])

        # Los códigos retirados (DISP, MODI, RAZA, TIPO) pueden seguir en bases
        # antiguas. Solo se eliminan si ningún rol los usa: si alguien los
        # asignó a un rol personalizado, la decisión es del administrador.
        obsoletos = [
            recurso
            for recurso in Recurso.objects.exclude(nombre__in=RECURSOS).exclude(opcion_menu=True)
            if not recurso.roles.exists()
        ]
        for recurso in obsoletos:
            recurso.delete()

        detalle = f"{len(PERMISOS_POR_ROL)} roles y {len(RECURSOS)} recursos administrados"
        if obsoletos:
            detalle += f"; {len(obsoletos)} recurso(s) obsoleto(s) sin uso eliminado(s)"
        self.stdout.write(
            self.style.SUCCESS(f"RBAC actualizado: {detalle}; no se crearon credenciales.")
        )
