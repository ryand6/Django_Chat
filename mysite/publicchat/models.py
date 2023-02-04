from django.db import models
from django.core.validators import MinLengthValidator
from django.conf import settings


class PublicChat(models.Model):
    title = models.CharField(max_length=200, unique=True, blank=False, validators=[MinLengthValidator(3, "Title must be greater than 2 characters")])
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, help_text="Users currently in the chat")

    def __str__(self):
        return self.title

    def connect_user(self, user):
        # checks if current user is stored in list of active users and adds them if not
        if not user in self.users.all():
            self.users.add(user)
            self.save()

    def disconnect_user(self, user):
        # removes active user when they disconnect from chatroom
        if user in self.users.all():
            self.users.remove(user)
            self.save()

    @property
    def group_name(self):
        return f"PublicChat-#{self.id}"


class PublicChatMessagesManager(models.Manager):
    def by_room(self, room):
        qs = PublicChatMessagesManager.objects.filter(room=room).order_by("-created_at")
        return qs


class PublicMessages(models.Model):
    room = models.ForeignKey('PublicChat', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(unique=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # overwrite objects using newly created manager
    objects = PublicChatMessagesManager()

    def __str__(self):
        return self.message