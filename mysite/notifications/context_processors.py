from .models import MessageNotifications, FriendNotifications


def unread_message_notifications(request):
    # return a count of all the unread message a user has (if any)
    if request.user.is_authenticated:
        unread_notifications = MessageNotifications.objects.filter(recipient=request.user, read=False).count()
        return {'unread_message_notifications': unread_notifications}
    else:
        return {}
    

def get_active_friend_notifications(request):
    # return a count of all unengaged friend notifications has as well as the notifications themselves
    if request.user.is_authenticated:
        active_friend_notifications = FriendNotifications.objects.filter(recipient=request.user, engaged=False).order_by('-timestamp')
        friend_notifications_count = active_friend_notifications.count()
        return {'active_friend_notifications': active_friend_notifications, 'friend_notifications_count': friend_notifications_count}
    else:
        return {}
