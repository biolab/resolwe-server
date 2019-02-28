"""CSRF configuration."""
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework.decorators import api_view
from rest_framework.response import Response


__all__ = (
    'csrf_view',
)


@ensure_csrf_cookie
@api_view(['GET'])
def csrf_view(request):
    """View that sends the CSRF cookie."""
    return Response()
