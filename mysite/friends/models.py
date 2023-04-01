from django.db import models
from django.conf import settings


class FriendList(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owner")
    friends = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="friends")

    def __str__(self):
        return self.owner.username

    def add_friend(self, account):
        if not account in self.friends.all():
            self.friends.add(account)

    def remove_friend(self, account):
        # remove friend from your friends list and remove yourself from their friends list
        if account in self.friends.all():
            self.friends.remove(account)
        account_friend_list = FriendList.objects.get(owner=account)
        if self.owner in account_friend_list.friends.all():
            account_friend_list.friends.remove(self.owner)

    def is_mutual_friend(self, account):
        if account in self.friends.all():
            return True
        return False


class FriendRequest(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="receiver")
    is_active_request = models.BooleanField(blank=True, null=False, default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver',)

    def __str__(self):
        return self.sender.username

    def accepted(self):
        sender_friend_list = FriendList.objects.get(owner=self.sender)
        receiver_friend_list = FriendList.objects.get(owner=self.receiver)
        if sender_friend_list and receiver_friend_list:
            sender_friend_list.add_friend(self.receiver)
            receiver_friend_list.add_friend(self.sender)
        else:
            raise Exception("unable to accept friend request")
        self.is_active_request = False
        self.save()

    def declined(self):
        # friend request declined by receiver
        # will remove the request from the senders list of sent requests but notification won't be sent
        self.is_active_request = False
        self.save()

    def cancelled(self):
        # friend request cancelled by sender
        # will remove the notification on the receivers end
        self.is_active_request = False
        self.save()