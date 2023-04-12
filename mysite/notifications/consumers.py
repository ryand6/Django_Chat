import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from privatechat.models import PrivateChat, PrivateMessages
from notifications.models import MessageNotifications, FriendNotifications
from friends.models import FriendRequest, FriendList
from account.models import Account


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


    async def send_friend_notification(self, event):
        sender = event['sender']
        sender_id = event['sender_id']
        status = event['status']
        profile_pic = event['profile_pic']
        notification_id = event['notification_id']
        friend_request_id = event['friend_request_id']
        timestamp = event['timestamp']

        await self.send(json.dumps({
            'type': 'friend_notification',
            'sender': sender,
            'sender_id': sender_id,
            'status': status,
            'profile_pic': profile_pic,
            'notification_id': notification_id,
            'friend_request_id': friend_request_id,
            'timestamp': timestamp
        }))

    def add_message_notification(recipient, room_id, sender, message):
        room = PrivateChat.objects.get(id=room_id)
        notification = MessageNotifications.objects.create(recipient=recipient, sender=sender, message=message, room=room)
        return notification
    
    def add_friend_notification(recipient, sender, status, friend_request_id):
        received_request = False
        accepted_request = False
        if status == "friend request received":
            received_request = True
        elif status == "friend request accepted":
            accepted_request = True
        try:
            # make notification active again
            notification = FriendNotifications.objects.get(recipient=recipient, sender=sender, friend_request_id=friend_request_id)
            notification.engaged = False
            notification.save()
        except FriendNotifications.DoesNotExist:
            notification = FriendNotifications.objects.create(recipient=recipient, sender=sender, received_request=received_request, accepted_request=accepted_request, friend_request_id=friend_request_id)
        return notification

    async def disconnect(self, close_code):
         print("disconnect notifications")
         print("notifications room group: ")
         print(self.room_group_name)
         print("notifications disconnect channel name: ")
         print(self.channel_name)
         print("notifications disconnect channel name type: ")
         print(type(self.channel_name))
         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
         print("notifications discard")


class OnlineStatusConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.room_group_name = 'online_status'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        user = self.scope['user']
        user_id = user.id

        print(user_id)

        print(self.channel_name)

        await self.channel_layer.group_send(
            self.room_group_name,
            # event
            {
                'type': 'send.userid',
                'user_id': user_id,
                'status': 'connected',
            }
        )

        
    async def send_userid(self, event):
        print("send_userid called")

        user_id = event['user_id']
        status = event['status']

        print(status)

        online_status = "offline"

        if status == "connected":
            online_status = "online"
        elif status == "away":
            online_status == "away"

        await self.set_user_status(user_id, online_status)

        await self.send(text_data=json.dumps({'user_id': user_id, 'status': status}))


    @database_sync_to_async
    def set_user_status(self, user_id, online_status):
        print("set_user_status called")
        print(online_status)
        user = Account.objects.get(pk=user_id)
        user.online_status = online_status
        user.save()


    async def disconnect(self, close_code):

        user = self.scope['user']
        user_id = user.id

        print("diconnect online status")
        print(self.room_group_name)
        print(user_id)
        print("online status disconnect channel name: ")
        print(self.channel_name)
        print("online status disconnect channel name type: ")
        print(type(self.channel_name))

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        print("discard called")
        
        await self.channel_layer.group_send(
            self.room_group_name,
            # event
            {
                'type': 'send_userid',
                'user_id': user_id,
                'status': 'disconnected',
            }
        )

        print("disconnected")


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


@receiver(post_save, sender=FriendRequest)
def send_friend_notification(sender, instance, **kwargs):
    print("FRIEND NOTIFICATION RECEIVED")
    print(instance.sender.friends.all())
    print(instance.receiver)
    channel_layer = get_channel_layer()
    if instance.is_active_request:
        status = "friend request received"
        recipient = instance.receiver
        sender = instance.sender
        friend_request_id = instance.id
    elif instance.sender.friends.filter(id=instance.receiver.id).exists():
        print("FRIEND REQUEST ACCEPTED")
        status = "friend request accepted"
        recipient = instance.sender
        sender = instance.receiver
        friend_request_id = None
    else:
        print("WE GOT A PROBLEM")
        return
    profile_pic = instance.sender.profile_image.url
    notification = NotificationConsumer.add_friend_notification(recipient=recipient, sender=sender, status=status, friend_request_id=friend_request_id)
    notification_id = notification.id
    notification_timestamp = notification.timestamp.isoformat()
    async_to_sync(channel_layer.group_send)(
        f'user_{recipient.id}',
        {
            'type': 'send_friend_notification',
            'sender': sender.username,
            'sender_id': sender.id,
            'friend_request_id': friend_request_id,
            'profile_pic': profile_pic,
            'status': status,
            'notification_id': notification_id,
            'timestamp': notification_timestamp
        }
    )