"""Routing configuration for Django Channels."""
from django.conf.urls import url

from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter

from resolwe.flow.consumers import PurgeConsumer
from resolwe.flow.managers.consumer import ManagerConsumer
from resolwe.flow.managers.state import MANAGER_CONTROL_CHANNEL
from resolwe.flow.protocol import CHANNEL_PURGE_WORKER
from rest_framework_reactive.consumers import ClientConsumer, PollObserversConsumer, WorkerConsumer
from rest_framework_reactive.protocol import CHANNEL_POLL_OBSERVER, CHANNEL_WORKER_NOTIFY

application = ProtocolTypeRouter({  # pylint: disable=invalid-name
    # Client-facing consumers.
    'websocket': URLRouter([
        # To change the prefix, you can import ClientConsumer in your custom
        # Channels routing definitions instead of using these defaults.
        url(r'^ws/(?P<subscriber_id>.+)$', ClientConsumer),
    ]),

    # Background worker consumers.
    'channel': ChannelNameRouter({
        MANAGER_CONTROL_CHANNEL: ManagerConsumer,
        CHANNEL_POLL_OBSERVER: PollObserversConsumer,
        CHANNEL_WORKER_NOTIFY: WorkerConsumer,
        CHANNEL_PURGE_WORKER: PurgeConsumer,
    })
})
