import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views import View
from django.core.exceptions import PermissionDenied

from account.models import Account
from friends.models import FriendRequest, FriendList


class FriendListView(View):
    template_name = "friends/friend_list.html"

    def get(self, request, pk):
        user = request.user
        if user.is_authenticated:
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
            redirect("login")
            

class FriendRequestsView(View):
    template_name = "friends/friend_requests.html"

    def get(self, request, pk):
        user = request.user
        if user.is_authenticated:
            account = get_object_or_404(Account, id=pk)
            if account != user:
                raise PermissionDenied
            else:
                friend_requests = FriendRequest.objects.filter(receiver=account, is_active_request=True)
                ctx = {'friend_requests': friend_requests}
                return render(request, self.template_name, ctx)
        else:
            redirect("login")


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
        payload['response'] = 'You must be authenticated to send friend request'
    return HttpResponse(json.dumps(payload), content_type="application/json")
                

def accept_friend_request(request, *args, **kwargs):
    # a lot of the error handling below is in case logic elsewhere in site is broken
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        received_friend_request_id = request.POST.get("received_friend_request_id")
        print(received_friend_request_id)
        if received_friend_request_id:
            try:
                received_friend_request = FriendRequest.objects.get(pk=received_friend_request_id)
                if received_friend_request.receiver == user:
                    try:
                        received_friend_request.accepted()
                    except Exception as e:
                        print(str(e))
                        payload['response'] = "unable to accept request"
                    else:
                        payload['response'] = "success"
                else:
                    payload['response'] = "error - not your friend request to accept"
            except Exception as e:
                print(str(e))
                payload['response'] = "unexpected error occurred"
        else:
            payload['response'] = "request id not found"
    else:
        payload['response'] = "must be authenticated to accept request"
    return HttpResponse(json.dumps(payload), content_type="application/json")


def decline_friend_request(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        received_friend_request_id = request.POST.get("received_friend_request_id")
        print(received_friend_request_id)
        if received_friend_request_id:
            try:
                received_friend_request = FriendRequest.objects.get(pk=received_friend_request_id)
                if received_friend_request.receiver == user:
                    try:
                        received_friend_request.declined()
                    except Exception as e:
                        print(str(e))
                        payload['response'] = "unable to decline request"
                    else:
                        payload['response'] = "success"
                else:
                    payload['response'] = "error - not your friend request to decline"
            except Exception as e:
                print(str(e))
                payload['response'] = "unexpected error occurred"
        else:
            payload['response'] = "request id not found"
    else:
        payload['response'] = "must be authenticated to decline request"
    return HttpResponse(json.dumps(payload), content_type="application/json")


def cancel_friend_request(request, *args, **kwargs):
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            receiver = Account.objects.get(pk=user_id)
            try:
                friend_request = FriendRequest.objects.filter(sender=user, receiver=receiver, is_active_request=True)
            except:
                payload['response'] = "friend request doesn't exist"
            
            # should only be one request as combination of sender and user is unique, but handle just in case
            # and print that this occurred
            if len(friend_request) > 1:
                print("More than one friend request found")
            for req in friend_request:
                req.cancelled()
            payload['response'] = "success"
        else:
            payload['response'] = "user id not provided"
    else:
        payload['response'] = "must be authenticated to cancel a friend request"
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
            except Exception as e:
                print(str(e))
                payload['response'] = "something went wrong"
        else:
            payload['response'] = "user id not provided"
    else:
        payload['response'] = "must be authenticated to remove friend"
    return HttpResponse(json.dumps(payload), content_type="application/json")
        