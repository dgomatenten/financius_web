"""
Custom DRF exception handler that wraps all error responses in the standard
{ data, error, meta } envelope so Android Retrofit clients get a consistent shape
regardless of whether the error is a validation failure, 401, 403, or 404.
"""
from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def envelope_exception_handler(exc: Exception, context: Any) -> Response | None:
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    # Only wrap if not already in envelope format
    if isinstance(response.data, dict) and "data" in response.data:
        return response

    detail = response.data.get("detail", str(response.data)) if isinstance(response.data, dict) else str(response.data)
    code_attr = getattr(getattr(exc, "detail", None), "code", None)
    code = str(code_attr) if code_attr else "error"

    response.data = {
        "data": None,
        "error": {"code": code, "message": str(detail)},
        "meta": {},
    }
    return response
