"""Contratos de módulos documentados que aún no tienen lógica de negocio."""

from rest_framework.response import Response
from rest_framework.views import APIView


class VistaModuloPendiente(APIView):
    """Ruta protegida y estable para que el frontend integre el módulo después."""

    recurso_requerido = None
    modulo = None
    nombre = None
    punto_extension = None

    def get(self, request):
        return Response(
            {
                "modulo": self.modulo,
                "nombre": self.nombre,
                "estado": "pendiente",
                "punto_extension": self.punto_extension,
            }
        )
