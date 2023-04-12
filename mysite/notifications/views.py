import json
from django.shortcuts import render
from django.http import HttpResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from notifications.models import MessageNotifications, FriendNotifications
from account.models import Account


def update_message_notifications(request):
    payload = {}
    if request.method == "GET":
        if request.user.is_authenticated:
            payload['unread_notifications'] = MessageNotifications.objects.filter(recipient=request.user, read=False).count()
            return HttpResponse(json.dumps(payload), content_type="application/json")


def update_friend_notifications(request):
    payload = {}
    if request.method == "GET":
        if request.user.is_authenticated:
            payload['unread_friend_notifications'] = FriendNotifications.objects.filter(recipient=request.user, engaged=False).count()
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
        

def set_user_status_offline(request):
    payload = {}
    if request.method == "POST":
        if request.user.is_authenticated:
            try:
                user = Account.objects.get(pk=request.user.id)
                user.online_status = "offline"
                user.save()
                payload['response'] = "success"
            except Exception as e:
                print("Unable to update user's status as offline")
                print(e)
            return HttpResponse(json.dumps(payload), content_type="application/json")
        

def set_user_status_away(request):
    payload = {}
    if request.method == "POST":
        if request.user.is_authenticated:
            if request.POST.get('status') == "away":
                try:
                    # Send message to appropriate channel group
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        "online_status",
                        {
                            "type": "send_userid",
                            "user_id": request.user.id,
                            "status": "away"
                        }
                    )

                    payload['response'] = "success"
                except Exception as e:
                    print("Unable to update user's status as away")
                    print(e)
                return HttpResponse(json.dumps(payload), content_type="application/json")
            

def set_user_status_online(request):
    payload = {}
    if request.method == "POST":
        if request.user.is_authenticated:
            if request.POST.get('status') == "online":
                try:
                    # Send message to appropriate channel group
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        "online_status",
                        {
                            "type": "send_userid",
                            "user_id": request.user.id,
                            "status": "connected"
                        }
                    )

                    payload['response'] = "success"
                except Exception as e:
                    print("Unable to update user's status as online")
                    print(e)
                return HttpResponse(json.dumps(payload), content_type="application/json")
