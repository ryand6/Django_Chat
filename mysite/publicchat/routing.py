from django.urls import re_path, path
from . import consumers


websocket_urlpatterns = [
    path('ws/public_chat/', consumers.PublicChatRoomConsumer.as_asgi()),
]