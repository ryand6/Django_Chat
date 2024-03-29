import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views import View
from django.core.exceptions import PermissionDenied

from account.models import Account
from friends.models import FriendRequest, FriendList
from notifications.models import FriendNotifications
from privatechat.models import PrivateChat

logger = logging.getLogger('django')


class FriendListView(View):
    template_name = "friends/friend_list.html"

    def get(self, request, pk):
        user = request.user
        if request.user.is_authenticated:
            account = get_object_or_404(Account, id=pk)

            # if no friend list exists for account - create one so that their friend list page can still be accessed
            try:
                friend_list_obj = FriendList.objects.get(owner=account)
            except FriendList.DoesNotExist:
                friend_list_obj = FriendList(owner=account)

            friend_list = []
            for friend in friend_list_obj.friends.all():
                friend_list.append(friend)

            ctx = {'friend_list': friend_list, 'account': account, 'user': user}
            return render(request, self.template_name, ctx)
        else:
            return redirect("login")
            

class FriendRequestsView(View):
    template_name = "friends/friend_requests.html"

    def get(self, request, pk):
        user = request.user
        if request.user.is_authenticated:
            account = get_object_or_404(Account, id=pk)
            if account != user:
                raise PermissionDenied
            else:
                friend_requests = FriendRequest.objects.filter(receiver=account, is_active_request=True)
                ctx = {'friend_requests': friend_requests}
                return render(request, self.template_name, ctx)
        else:
            return redirect("login")


def is_friend_request_active(sender, receiver):
    try:
        return FriendRequest.objects.get(sender=sender, receiver=receiver, is_active_request=True)
    except FriendRequest.DoesNotExist as e:
        return False


def send_friend_request(request, *args, **kwargs):
    # using ajax request so that page isn't refreshed if friend request cannot be sent for some reason
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        user_id = request.POST.get("receiver_user_id")

        # if friend_list for user sending request doesn't currently exist, create one
        try:
            friend_list = FriendList.objects.get(owner=user)
        except FriendList.DoesNotExist:
            friend_list = FriendList(owner=user)

        if user_id:
            receiver = Account.objects.get(pk=user_id)
            try:
                friend_request = FriendRequest.objects.get(sender=user, receiver=receiver)
                # logic to cover any faults elsewhere where user is somehow able to attempt to send a second
                # friend request to account despite one already being active
                if friend_request.is_active_request:
                    raise Exception("There is already an active pending friend request for this account")
                friend_request.is_active_request = True
                friend_request.save()
                payload['response'] = 'success'
            except FriendRequest.DoesNotExist:
                friend_request = FriendRequest(sender=user, receiver=receiver)
                friend_request.save()
                payload['response'] = 'success'
            if payload['response'] == None:
                payload['response'] = 'Unexpected error occurred'
        else:
            payload['response'] = 'Unable to send friend request'
    else:
        return redirect("login")
    return HttpResponse(json.dumps(payload), content_type="application/json")
                

def accept_friend_request(request, *args, **kwargs):
    # a lot of the error handling below is in case logic elsewhere in site is broken
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        received_friend_request_id = request.POST.get("received_friend_request_id")
        if received_friend_request_id:
            try:
                received_friend_request = FriendRequest.objects.get(pk=received_friend_request_id)
                try:
                    friend_notification = FriendNotifications.objects.get(friend_request_id=received_friend_request_id)
                    friend_notification.engaged = True
                    friend_notification.save()
                except Exception as e:
                    logger.warning(f'user {user.id} - accept_friend_request view - no friend notification found - {str(e)}')
                if received_friend_request.receiver == user:
                    # handle if sender has cancelled friend request
                    if received_friend_request.is_active_request == False:
                        payload['response'] = "friend request is no longer active"
                    else:
                        try:
                            received_friend_request.accepted()
                        except Exception as e:
                            payload['response'] = "unable to accept request"
                        else:
                            payload['response'] = "success"
                else:
                    payload['response'] = "error - not your friend request to accept"
            except Exception as e:
                payload['response'] = f"unexpected error occurred: {str(e)}"
        else:
            payload['response'] = "request id not found"
    else:
        return redirect("login")
    return HttpResponse(json.dumps(payload), content_type="application/json")


def decline_friend_request(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        received_friend_request_id = request.POST.get("received_friend_request_id")
        if received_friend_request_id:
            try:
                received_friend_request = FriendRequest.objects.get(pk=received_friend_request_id)
                try:
                    friend_notification = FriendNotifications.objects.get(friend_request_id=received_friend_request_id)
                    friend_notification.engaged = True
                    friend_notification.save()
                except:
                    logger.warning(f'user {user.id} - decline_friend_request view - no friend notification found - {str(e)}')
                if received_friend_request.receiver == user:
                    if received_friend_request.is_active_request == False:
                        payload['response'] = "friend request is no longer active"
                    else:
                        try:
                            received_friend_request.declined()
                        except Exception as e:
                            payload['response'] = f"unable to decline request: {str(e)}"
                        else:
                            payload['response'] = "success"
                else:
                    payload['response'] = "error - not your friend request to decline"
            except Exception as e:
                payload['response'] = f"unexpected error occurred: {str(e)}"
        else:
            payload['response'] = "request id not found"
    else:
        return redirect("login")
    return HttpResponse(json.dumps(payload), content_type="application/json")


def cancel_friend_request(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        user_id = request.POST.get("receiver_user_id")
        sent_friend_request_id = request.POST.get("friend_request_id")
        if user_id:
            receiver = Account.objects.get(pk=user_id)
            try:
                friend_request = FriendRequest.objects.filter(sender=user, receiver=receiver, is_active_request=True)
            except:
                payload['response'] = "friend request doesn't exist"

            try:
                friend_notification = FriendNotifications.objects.get(friend_request_id=sent_friend_request_id)
                friend_notification.engaged = True
                friend_notification.save()
            except Exception as e:
                logger.warning(f'user {user.id} - cancel_friend_request view - no friend notification found - {str(e)}')
            
            # should only be one request as combination of sender and user is unique, but handle and log just in case
            if len(friend_request) > 1:
                logger.warning(f'cancel_friend_request view - more than one friend request found from user {user.id} to receiver {receiver.id}')
            for req in friend_request:
                req.cancelled()
            payload['response'] = "success"
        else:
            payload['response'] = "user id not provided"
    else:
        return redirect("login")
    return HttpResponse(json.dumps(payload), content_type="application/json")   


def unfriend(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            try:
                account = Account.objects.get(pk=user_id)
                friend_list = FriendList.objects.get(owner=user)
                friend_list.remove_friend(account)
                payload['response'] = "success"
                try:
                    users = sorted(list((account.email, user.email)))
                    title = " ".join(users) + " private chat"
                    privatechat = PrivateChat.objects.get(title=title)
                    privatechat.delete()
                except PrivateChat.DoesNotExist:
                    logger.warning(f'user {user.id} - unfriend view - no private chat found to delete for combination of users: user {user.id} and user {account.id}')
            except Exception as e:
                payload['response'] = f"something went wrong {str(e)}"
        else:
            payload['response'] = "user id not provided"
    else:
        return redirect("login")
    return HttpResponse(json.dumps(payload), content_type="application/json")
        