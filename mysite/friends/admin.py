from django.contrib import admin
from friends.models import FriendList, FriendRequest

class FriendListAdmin(admin.ModelAdmin):
    list_filter = ['owner']
    list_display = ['owner']
    search_fields = ['owner']
    readonly_fields = ['owner__username', 'owner__email']

    class Meta:
        model = FriendList


class FriendRequestAdmin(admin.ModelAdmin):
    list_filter = ['sender', 'receiver']
    list_display = ['sender', 'receiver']
    search_fields = ['sender__username', 'sender__email', 'receiver__username', 'receiver__email']

    class Meta:
        model = FriendRequest
        

admin.site.register(FriendList)
admin.site.register(FriendRequest)