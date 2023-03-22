import json
from django.shortcuts import render
from django.http import HttpResponse

from notifications.models import MessageNotifications, FriendNotifications


def update_message_notifications(request):
    payload = {}
    if request.method == "GET":
        if request.user.is_authenticated:
            payload['unread_notifications'] = MessageNotifications.objects.filter(recipient=request.user, read=False).count()
        return HttpResponse(json.dumps(payload), content_type="application/json")


def update_friend_request_accepted_notifications(request):
    payload = {}
    if request.method == "GET":
        if request.user.is_authenticated:
            try:
                FriendNotifications.objects.filter(recipient=request.user, accepted_request=True, engaged=False).update(engaged=True)
                payload['response'] = "success"
            except Exception as e:
                print("Unable to update accepted friend request notifications")
                print(e)
            return HttpResponse(json.dumps(payload), content_type="application/json")
