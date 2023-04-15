from django.db import models
from django.core.validators import MinLengthValidator
from django.conf import settings
from fernet_fields import EncryptedTextField


class PrivateChat(models.Model):
    title = models.CharField(max_length=200, unique=True, blank=False, validators=[MinLengthValidator(3, "Title must be greater than 2 characters")])
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, help_text="Users currently in the chat", related_name="chatrooms")
    unread_messages = models.IntegerField(default=0)

    def __str__(self):
        return self.title


class PrivateChatMessagesManager(models.Manager):
    def by_room(self, room):
        qs = PrivateChatMessagesManager.objects.filter(room=room).order_by("-created_at")
        return qs
 

class PrivateMessages(models.Model):
    room = models.ForeignKey('PrivateChat', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = EncryptedTextField(unique=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # overwrite objects using newly created manager
    objects = PrivateChatMessagesManager()

    def __str__(self):
        return self.message