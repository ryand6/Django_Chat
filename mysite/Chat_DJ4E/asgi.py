"""
ASGI config for mysite project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os
import django
from decouple import config

from django.urls import path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'{config("PROJECT_NAME")}.settings')
django_asgi_app = get_asgi_application()
django.setup()

from publicchat.consumers import PublicChatRoomConsumer
from privatechat.consumers import PrivateChatRoomConsumer, AllPrivateChatRoomsConsumer
from notifications.consumers import NotificationConsumer, OnlineStatusConsumer

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter([
                    path('ws/notifications/<int:user_id>/', NotificationConsumer.as_asgi()),
                    path('ws/online_status/', OnlineStatusConsumer.as_asgi()),
                    path('ws/public_chat/', PublicChatRoomConsumer.as_asgi()),
                    path('ws/private_chat/<int:room_id>/', PrivateChatRoomConsumer.as_asgi()),
                    path('ws/all_private_chats/<int:user_id>/', AllPrivateChatRoomsConsumer.as_asgi()),
            ])
        )
    ),
})
