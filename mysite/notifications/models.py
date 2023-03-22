from django.db import models
from django.conf import settings
from privatechat.models import PrivateChat

class MessageNotifications(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_recipient")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_sender")
    message = models.CharField(max_length=255, null=True)
    room = models.ForeignKey(PrivateChat, on_delete=models.CASCADE, related_name="notification_chatroom")
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return self.recipient.username + "notifications"


class FriendNotifications(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="friend_notification_recipient")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="friend_notification_sender")
    timestamp = models.DateTimeField(auto_now_add=True)
    friend_request_id = models.IntegerField(blank=True, null=True)
    received_request = models.BooleanField(default=False)
    accepted_request = models.BooleanField(default=False)
    engaged = models.BooleanField(default=False)

    class Meta:
        unique_together = ('sender', 'recipient', 'friend_request_id',)

    def __str__(self):
        return self.recipient.username + "friend notifications"