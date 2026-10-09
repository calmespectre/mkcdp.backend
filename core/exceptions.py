import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        return Response({"success": False, "errors": {"detail": exc.messages}}, status=status.HTTP_400_BAD_REQUEST)
    if isinstance(exc, IntegrityError):
        logger.exception("Integrity error")
        return Response({"success": False, "errors": {"detail": ["Database integrity error."]}}, status=status.HTTP_400_BAD_REQUEST)
    response = exception_handler(exc, context)
    if response is None:
        logger.exception("Unhandled exception")
        return Response({"success": False, "errors": {"detail": ["Internal server error."]}}, status=500)
    if isinstance(response.data, dict) and "detail" not in response.data:
        response.data = {"success": False, "errors": response.data}
    elif isinstance(response.data, dict):
        response.data = {"success": False, "errors": {"detail": [str(response.data.get("detail"))]}}
    else:
        response.data = {"success": False, "errors": {"detail": response.data}}
    return response