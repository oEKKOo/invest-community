from rest_framework.views import exception_handler as drf_exception_handler

from .api_exceptions import ApiError


def custom_exception_handler(exc, context):
    if isinstance(exc, ApiError):
        payload = {"code": exc.code, "message": exc.message}
        if exc.errors is not None:
            payload["errors"] = exc.errors
        from rest_framework.response import Response

        return Response(payload, status=exc.status_code)

    return drf_exception_handler(exc, context)
