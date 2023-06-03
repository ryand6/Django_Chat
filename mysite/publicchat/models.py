from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.conf import settings


class PublicChat(models.Model):
    title = models.CharField(max_length=200, unique=True, blank=False, validators=[MinLengthValidator(3, "Title must be greater than 2 characters")])
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, help_text="Users currently in the chat")

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # make sure there can only be one instance of the public chatroom model
        if not PublicChat.objects.filter(pk=self.pk).exists() and PublicChat.objects.exists():
            raise ValidationError('There can only be one instance of this model') 
        return super(PublicChat, self).save(*args, **kwargs)


class PublicChatMessagesManager(models.Manager):
    def by_room(self, room):
        qs = PublicChatMessagesManager.objects.filter(room=room).order_by("-created_at")
        return qs


class PublicMessages(models.Model):
    room = models.ForeignKey('PublicChat', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(unique=False, blank=False)
    code = models.BooleanField(default=False)
    language = models.TextField(blank=True, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    # overwrite objects using newly created manager
    objects = PublicChatMessagesManager()

    def __str__(self):
        return self.message
