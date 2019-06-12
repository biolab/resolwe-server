"""Url router."""
from django.apps import apps
from django.contrib import admin
from django.urls import include, path

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


api_router = routers.DefaultRouter(
    trailing_slash=False)  # pylint: disable=invalid-name
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
    path('api/base/', include('resolwe_server.base.urls')),
    path('api/queryobserver/', include('rest_framework_reactive.api_urls')),
    path('api/', include((api_router.urls, 'resolwe-api'))),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('rest-auth/', include('rest_auth.urls')),
    path('admin/', admin.site.urls),
    # Use this pattern if NGINX UPLOAD MODULE not installed
    path('upload/', uploader_views.file_upload),
    path('data/<int:data_id>/<str:uri>', uploader_views.file_download),
    path('datagzip/<int:data_id>/<str:uri>',
         uploader_views.file_download, {'gzip_header': True}),
    path('token/<str:token>/data/<int:data_id>/<str:uri>',
         uploader_views.file_download),
]

if apps.is_installed('genesis.testing'):
    urlpatterns += [path('testing/', include('genesis.testing.urls'))]
