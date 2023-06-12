from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('public_chat/<room_id>/', consumers.PublicChatConsumer.as_asgi(), name="test")
]