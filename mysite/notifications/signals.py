import logging

from channels.db import database_sync_to_async
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from privatechat.models import PrivateMessages
from notifications.models import MessageNotifications, FriendNotifications
from friends.models import FriendRequest
from notifications.consumers import NotificationConsumer

# when a private message has been saved to the database, get all the recipients of that message and
# send a notification to them alerting them of who sent the message
@receiver(post_save, sender=PrivateMessages)
def send_notification(sender, instance, **kwargs):
    logging.debug(post_save.receivers)
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
    logging.debug("send_friend_notification called")
    channel_layer = get_channel_layer()
    if instance.is_active_request:
        logging.debug('request received')
        status = "friend request received"
        recipient = instance.receiver
        sender = instance.sender
        friend_request_id = instance.id
    elif instance.sender.friends.filter(id=instance.receiver.id).exists():
        logging.debug('request accepted')
        status = "friend request accepted"
        recipient = instance.sender
        sender = instance.receiver
        friend_request_id = None
    else:
        logging.error('send_friend_notification in notifications consumer called without there being a new valid instance of a friend notification')
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

post_save.connect(send_friend_notification, sender=FriendRequest)   