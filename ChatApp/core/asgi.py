"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""
import os

from django.urls import path
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
# Give access to tvhe user sessions object
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

from public_chat.consumers import PublicChatConsumer
from private_chat.consumers import PrivateChatConsumer
from notification.consumers import NotificationConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
# django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": get_asgi_application(),

    # WebSocket chat handler
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                path("", NotificationConsumer.as_asgi()),
                path("public_chat/<room_id>/", PublicChatConsumer.as_asgi()),
                path("private_chat/<room_id>/", PrivateChatConsumer.as_asgi()),   
            ])
        )
    )
})
