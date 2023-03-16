import json
import datetime

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from privatechat.models import PrivateMessages
from notifications.models import Notifications


class NotificationConsumer(AsyncWebsocketConsumer):
    connected_channels = set()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_groups = {}

    async def connect(self):
        user = self.scope['user']
        self.connected_channels = set()
        if user.is_anonymous:
            await self.close()
        user_id = self.scope['url_route']['kwargs']['user_id']

        print("SELF.CHANNEL_NAME")
        print(self.channel_name)

        self.room_group_name = f'user_{user_id}'
        if user.id == user_id:
            print("yes indeed")

            print(self.room_group_name)
            print(self.channel_name)
        
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)

            # try:
            #     self.notifications = await database_sync_to_async(Notifications.objects.get)(recipient=user)
            # except Notifications.DoesNotExist:
            #     self.notifications = await database_sync_to_async(Notifications.objects.create)(recipient=user)

            await self.accept()


    async def send_notification(self, event):
            sender = event['sender']
            room_id = event['room_id']
            message = event['message']
            profile_pic = event['profile_pic']
            notification_id = event['notification_id']
            timestamp = event['timestamp']

            await self.send(json.dumps({
                'type': 'message_notification',
                'sender': sender,
                'room_id': room_id,
                'message': message,
                'profile_pic': profile_pic,
                'notification_id': notification_id,
                'timestamp': timestamp
            }))


    def add_message_notification(recipient, room_id, sender, message):
        notification = Notifications.objects.create(recipient=recipient, sender=sender, message=message, link_id=room_id)
        return notification


    async def disconnect(self, close_code):
         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)


# when a private message has been saved to the database, get all the recipients of that message and
# send a notification to them alerting them of who sent the message
@receiver(post_save, sender=PrivateMessages)
def send_notification(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    recipients = instance.room.users.all()
    room_id = instance.room.id
    sender = instance.user
    message = instance.message
    profile_pic = instance.user.profile_image.url

    for recipient in recipients:
        if recipient != sender:
            notification = NotificationConsumer.add_message_notification(recipient=recipient, room_id=room_id, sender=sender, message=message)
            notification_id = notification.id
            notification_timestamp = notification.timestamp.isoformat()
            async_to_sync(channel_layer.group_send)(
                f'user_{recipient.id}',
                {
                    'type': 'send_notification',
                    'sender': sender.username,
                    'room_id': room_id,
                    'message': message,
                    'profile_pic': profile_pic,
                    'notification_id': notification_id,
                    'timestamp': notification_timestamp
                }
            )