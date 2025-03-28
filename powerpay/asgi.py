import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack  # Import AuthMiddleware
from channels.layers import get_channel_layer
from django.core.asgi import get_asgi_application
from . import routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "powerpay.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(  # Wrap WebSocket connections in AuthMiddleware
        URLRouter(routing.websocket_urlpatterns)
    ),
})

channel_layer = get_channel_layer()
