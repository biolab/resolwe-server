"""Url router."""
from django.apps import apps
from django.conf.urls import include, url
from django.contrib import admin

from rest_framework import routers

from resolwe.flow.views import (
    CollectionViewSet,
    ProcessViewSet,
    DataViewSet,
    DescriptorSchemaViewSet,
    EntityViewSet,
    StorageViewSet,
    RelationViewSet,
)

from resolwe_server.base import views as base_views
from resolwe_server.uploader import views as uploader_views


api_router = routers.DefaultRouter(trailing_slash=False)  # pylint: disable=invalid-name
api_router.register(r'collection', CollectionViewSet)
api_router.register(r'entity', EntityViewSet)
api_router.register(r'relation', RelationViewSet)
api_router.register(r'process', ProcessViewSet)
api_router.register(r'data', DataViewSet)
api_router.register(r'descriptorschema', DescriptorSchemaViewSet)
api_router.register(r'storage', StorageViewSet)
api_router.register(r'user', base_views.UserViewSet, 'user')
api_router.register(r'group', base_views.GroupViewSet, 'group')

urlpatterns = [  # pylint: disable=invalid-name
    url(r'^api/base/', include('resolwe_server.base.urls')),
    url(r'^api/queryobserver/', include('rest_framework_reactive.api_urls')),
    url(r'^api/', include(api_router.urls, namespace='resolwe-api')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^rest-auth/', include('rest_auth.urls')),
    url(r'^admin/', admin.site.urls),
    # Use this pattern if NGINX UPLOAD MODULE not installed
    url(r'^upload/$', uploader_views.file_upload),
    url(r'^data/(?P<data_id>[0-9]+)/(?P<uri>.*)', uploader_views.file_download),
    url(
        r'^datagzip/(?P<data_id>[0-9]+)/(?P<uri>.*)',
        uploader_views.file_download,
        {'gzip_header': True},
    ),
    url(
        r'^token/(?P<token>[a-zA-Z0-9]+)/data/(?P<data_id>[0-9]+)/(?P<uri>.*)',
        uploader_views.file_download,
    ),
]

if apps.is_installed('genesis.testing'):
    urlpatterns += [url(r'^testing/', include('genesis.testing.urls'))]
