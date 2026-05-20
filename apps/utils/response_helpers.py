from rest_framework import status
from rest_framework.response import Response



# ─────────────────────────────────────────────────────────────────────────────
# Response helpers
# ─────────────────────────────────────────────────────────────────────────────

def ok(message: str, data=None, http_status=status.HTTP_200_OK) -> Response:
    body = {"status": "success", "message": message}
    if data is not None:
        body['data'] = data
    return Response(body, status=http_status)

def created(message: str, data=None) -> Response:
    return ok(message, data, http_status=status.HTTP_201_CREATED)

def not_found(message: str = "Not found.") -> Response:
    return Response({"status": "error", "message": message}, status=status.HTTP_404_NOT_FOUND)

def forbidden(message: str = "Permission denied") -> Response:
    return Response({"status": "error", "message": message}, status=status.HTTP_403_FORBIDDEN)