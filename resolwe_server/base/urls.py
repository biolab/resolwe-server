"""General router."""
from django.conf.urls import url

from . import views


urlpatterns = [  # pylint: disable=invalid-name
    url(r'^csrf$', views.csrf_view),
    url(r'^auth', views.authorization, name='authorization'),
]
