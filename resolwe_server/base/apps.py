"""Application configuration."""
from django.apps import AppConfig


class BaseConfig(AppConfig):
    """Application configuration."""

    name = 'resolwe_server.base'

    def ready(self):
        """Perform application initialization."""
        from rest_framework_reactive.decorators import observable
        from resolwe.flow import views as flow_views

        flow_views.DataViewSet = observable(flow_views.DataViewSet)
        flow_views.ProcessViewSet = observable(flow_views.ProcessViewSet)
        # flow_views.StorageViewSet = observable(flow_views.StorageViewSet)
