"""General router."""
from django.urls import path

from . import views


urlpatterns = [  # pylint: disable=invalid-name
    path('csrf', views.csrf_view),
    path('auth', views.authorization, name='authorization'),
]
