"""Instrumentación de bajo coste para las APIs locales."""

from time import perf_counter

from django.conf import settings


class ApiServerTimingMiddleware:
    """Expone el tiempo de servidor en desarrollo sin alterar respuestas JSON.

    El encabezado estándar Server-Timing permite separar en el navegador la
    latencia de red del tiempo que Django tardó en procesar el endpoint. Nunca
    se publica en producción.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        inicio = perf_counter()
        response = self.get_response(request)
        if settings.DEBUG and request.path.startswith("/api/"):
            duracion_ms = (perf_counter() - inicio) * 1000
            response["Server-Timing"] = f'app;dur={duracion_ms:.2f};desc="Django"'
        return response
