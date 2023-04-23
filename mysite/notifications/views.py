import json
import logging

from django.http import HttpResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from notifications.models import MessageNotifications, FriendNotifications


logger = logging.getLogger('django')


def update_message_notifications(request):
    payload = {}
    if request.method == "GET" and request.user.is_authenticated:
        payload['unread_notifications'] = MessageNotifications.objects.filter(recipient=request.user, read=False).count()
        return HttpResponse(json.dumps(payload), content_type="application/json")
    else:
        return HttpResponse('')

def update_friend_notifications(request):
    payload = {}
    if request.method == "GET" and request.user.is_authenticated:
        payload['unread_friend_notifications'] = FriendNotifications.objects.filter(recipient=request.user, engaged=False).count()
        return HttpResponse(json.dumps(payload), content_type="application/json")
    else:
        return HttpResponse('')

def update_friend_request_accepted_notifications(request):
    payload = {}
    if request.method == "GET" and request.user.is_authenticated:
        try:
            FriendNotifications.objects.filter(recipient=request.user, accepted_request=True, engaged=False).update(engaged=True)
            payload['response'] = "success"
        except Exception as e:
            logging.error(f'user {request.user.id} - update_friend_request_accepted_notifications view - failed to update notification as being engaged - {str(e)}')
        return HttpResponse(json.dumps(payload), content_type="application/json")
    else:
        return HttpResponse('')       

def set_user_status_offline(request):
    payload = {}
    if request.method == "POST" and request.user.is_authenticated:
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "online_status",
                {
                    "type": "send.userid",
                    "user_id": request.user.id,
                    "status": "offline"
                }
            )
            payload['response'] = "success"
        except Exception as e:
            logging.error(f'user {request.user.id} - set_user_status_offline view - unable to update users status as offline - {str(e)}')
        return HttpResponse(json.dumps(payload), content_type="application/json")
    else:
        return HttpResponse('')
        

def set_user_status_away(request):
    payload = {}
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get('status') == "away":
            try:
                # Send message to appropriate channel group
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "online_status",
                    {
                        "type": "send.userid",
                        "user_id": request.user.id,
                        "status": "away"
                    }
                )
                payload['response'] = "success"
            except Exception as e:
                logging.error(f'user {request.user.id} - set_user_status_away view - unable to update users status as away - {str(e)}')
            return HttpResponse(json.dumps(payload), content_type="application/json")
        else:
            logging.error('set_user_status_online view - incorrect status passed')
            return HttpResponse('')
    else:
        return HttpResponse('')
            

def set_user_status_online(request):
    payload = {}
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get('status') == "online":
            try:
                # Send message to appropriate channel group
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "online_status",
                    {
                        "type": "send.userid",
                        "user_id": request.user.id,
                        "status": "connected"
                    }
                )
                payload['response'] = "success"
            except Exception as e:
                logging.error(f'user {request.user.id} - set_user_status_online view - unable to update users status as online - {str(e)}')
            return HttpResponse(json.dumps(payload), content_type="application/json")
        else:
            logging.error('set_user_status_online view - incorrect status passed')
            return HttpResponse('')
    else:
        return HttpResponse('')