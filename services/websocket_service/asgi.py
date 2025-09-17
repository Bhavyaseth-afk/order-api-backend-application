"""
ASGI config for WebSocket Service.
"""
import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'services.websocket_service.settings')

# Initialize Django
django.setup()

# Import routing after Django setup
from . import routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
}) 