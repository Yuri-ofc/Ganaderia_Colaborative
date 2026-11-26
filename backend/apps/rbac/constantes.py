"""Catálogo base de RBAC, compartido por el seed y las vistas.

Los códigos de esta lista sostienen el sistema de permisos completo: si se
renombran o se borran, los `recurso_requerido` declarados en las vistas dejan
de encontrar su recurso y nadie puede volver a entrar a administrar nada. Por
eso viven aquí en un solo lugar y las vistas los tratan como inmutables.
"""

RECURSOS = (
    "RBAC", "FINC", "MIEM", "INVT", "LOTE", "BOVI", "MEDI", "PESA", "RESP", "SYNC",
    "VCOM", "EXPO", "RECU",
)

ROLES_SISTEMA = frozenset(("SUPR", "PROP", "ADMI", "OPER"))

RECURSOS_SISTEMA = frozenset(RECURSOS)
