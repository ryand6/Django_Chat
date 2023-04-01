import json
import pytz

from django.views import View
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.db.models import Subquery, OuterRef, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.core.exceptions import PermissionDenied
from django.db.utils import IntegrityError
from django.db.models.functions import Coalesce

from privatechat.models import PrivateChat, PrivateMessages
from account.models import Account
from notifications.models import MessageNotifications


class PrivateChatAllChatsView(View):
    template_name = "privatechat/all_chats.html"

    def get(self, request, user_id):
        user = request.user
        if not user.is_authenticated:
            return redirect("login")
        account = get_object_or_404(Account, pk=user_id)
        if account.pk != request.user.pk:
            raise PermissionDenied
        else:
            try:
                # filter private chat to return query set where current user is a member of each private chatroom
                private_chats = PrivateChat.objects.filter(users__in=[user]).order_by('pk')

                # subquery of the last message sent in each of the list of private chats the user is part of
                last_messages = PrivateMessages.objects.filter(
                    room_id=OuterRef('pk')
                ).order_by('-created_at').values('message')[:1]

                # sub query of the last date a message was sent in each of the private chats the user is part of
                last_dates = PrivateMessages.objects.filter(
                    room_id=OuterRef('pk')
                ).order_by('-created_at').values('created_at')[:1]

                # sub query of the last user for each last message sent's id
                last_users = PrivateMessages.objects.filter(
                    room_id=OuterRef('pk')
                ).order_by('-created_at').values('user_id')[:1]

                # sub query of the count of unread message notifications for each private chatroom
                unread_counts = MessageNotifications.objects.filter(
                    recipient=user,
                    read=False,
                    room_id=OuterRef('pk')
                ).values('room').annotate(count=Count('room')).values('count')

                # make the last message accessible in the main queryset for each chatroom
                chats_with_last_messages = private_chats.annotate(
                    last_message=Subquery(last_messages)
                )

                # make the last date a message was sent accessible in the main queryset for each chatroom
                chats_with_last_messages = chats_with_last_messages.annotate(
                    last_date=Subquery(last_dates)
                )

                # make the last user's id accessable in the main queryset for each chatroom
                chats_with_last_messages = chats_with_last_messages.annotate(
                    last_user=Subquery(last_users)
                )

                # add the count of unread message notifications for each chatroom to the main queryset
                chats_with_last_messages = chats_with_last_messages.annotate(
                    unread_count=Coalesce(Subquery(unread_counts), 0)
                )

                # # order final queryset by last date desc so that any time the page is refreshed, the most recent message
                # appears first
                chats_with_last_messages = chats_with_last_messages.order_by('-last_date')

            except Exception as e:
                print("no private chats found")
                print(e)
                chats_with_last_messages = []
        
        ctx = {'chats': chats_with_last_messages, 'userid': user.id}
        return render(request, self.template_name, ctx)


class PrivateChatView(View):
    template_name = "privatechat/private_chat.html"

    def get(self, request, room_id):
        if not request.user.is_authenticated:
            return redirect("login")
        userid = request.user.id
        user = request.user
        username = request.user.username
        chatroom = get_object_or_404(PrivateChat, pk=room_id)
        chat_users = chatroom.users.all()
        # if user is not part of private chat, prevent access
        if request.user not in chat_users:
            raise PermissionDenied
        print(chat_users)

        timezone_offset = request.session.get('tz_offset', None)
        print(timezone_offset)
        if timezone_offset is not None:
            timezone_offset = int(timezone_offset) * -1
            user_timezone = timezone.get_fixed_timezone(timezone_offset)
            print(user_timezone)
        else:
            user_timezone = 0

        recent_messages = PrivateMessages.objects.filter(room=chatroom).order_by('-id')[:40]
        recent_messages = recent_messages[::-1]

        try:
            MessageNotifications.objects.filter(room=chatroom, recipient=request.user).update(read=True)
        except:
            print("no notifications to update")

        try:
            # filter private chat to return query set where current user is a member of each private chatroom
            private_chats = PrivateChat.objects.filter(users__in=[user]).order_by('pk')

            # subquery of the last message sent in each of the list of private chats the user is part of
            last_messages = PrivateMessages.objects.filter(
                room_id=OuterRef('pk')
            ).order_by('-created_at').values('message')[:1]

            # sub query of the last date a message was sent in each of the private chats the user is part of
            last_dates = PrivateMessages.objects.filter(
                room_id=OuterRef('pk')
            ).order_by('-created_at').values('created_at')[:1]

            # sub query of the last user for each last message sent's id
            last_users = PrivateMessages.objects.filter(
                room_id=OuterRef('pk')
            ).order_by('-created_at').values('user_id')[:1]

            # sub query of the count of unread message notifications for each private chatroom
            unread_counts = MessageNotifications.objects.filter(
                recipient=user,
                read=False,
                room_id=OuterRef('pk')
            ).values('room').annotate(count=Count('room')).values('count')

            # make the last message accessible in the main queryset for each chatroom
            chats_with_last_messages = private_chats.annotate(
                last_message=Subquery(last_messages)
            )

            # make the last date a message was sent accessible in the main queryset for each chatroom
            chats_with_last_messages = chats_with_last_messages.annotate(
                last_date=Subquery(last_dates)
            )

            # make the last user's id accessable in the main queryset for each chatroom
            chats_with_last_messages = chats_with_last_messages.annotate(
                last_user=Subquery(last_users)
            )

            # add the count of unread message notifications for each chatroom to the main queryset
            chats_with_last_messages = chats_with_last_messages.annotate(
                unread_count=Coalesce(Subquery(unread_counts), 0)
            )

            # # order final queryset by last date desc so that any time the page is refreshed, the most recent message
            # appears first
            chats_with_last_messages = chats_with_last_messages.order_by('-last_date')

        except Exception as e:
            print("no private chats found")
            print(e)
            chats_with_last_messages = []

        ctx = {'room_id': room_id, 'userid': userid, 'username': username, 'recent_messages': recent_messages, 'chat_users': chat_users, 'chats': chats_with_last_messages, 'user_timezone': user_timezone} 

        return render(request, self.template_name, ctx)


def update_chat_log(request):
    payload = {}

    if request.method == "GET":
        room_id = request.GET.get("room_id")
        print("Room ID: ", str(room_id))
        private_chat = PrivateChat.objects.get(id=room_id)
        unread_count = MessageNotifications.objects.filter(recipient=request.user, room=private_chat, read=False).count()
        # uses default django ORM name to view to get all private messages associated with private chat
        # as the PrivateChat model is a foreign key field of PrivateMessages - gets the last sent message in chat
        last_message = private_chat.privatemessages_set.order_by('-created_at').first()
        private_chat.last_message = last_message.message if last_message else None
        private_chat.last_date = last_message.created_at if last_message else None
        private_chat.last_message_user = last_message.user.id if last_message else None
        private_chat.unread_count = unread_count if unread_count else 0
        print("UNREAD COUNT")
        print(private_chat.unread_count)

        chat_users = []
        private_chat_users = private_chat.users.all()
        for user in private_chat_users:
            if user != request.user:
                chat_users.append(user.username)
                if len(private_chat_users) == 2:
                    chat_image = user.profile_image.url

        chat_name = ", ".join(chat_users)

        payload['chat_id'] = private_chat.id
        payload['chat_name'] = chat_name
        payload['chat_image'] = chat_image
        payload['last_message'] = private_chat.last_message
        payload['last_date'] = private_chat.last_date.isoformat()
        payload['last_message_user'] = private_chat.last_message_user
        payload['unread_count'] = private_chat.unread_count

        return HttpResponse(json.dumps(payload), content_type="application/json")


def create_chat(request):
    payload = {}

    if request.method == 'POST':
        friend_id = request.POST.get("friend_id")
        friend = Account.objects.get(pk=friend_id)
        # sort email addresses so that room title is the same regardless of which user in the pair sends
        # the message - using email addresses as they're unique and can't be changed for that account
        users = sorted([request.user.email, friend.email])
        title = users[0] + " " + users[1] + " private chat"
        try:
            chat = PrivateChat.objects.create(title=title)
            # chat.users.set([request.user, friend])
            chat.users.add(request.user)
            chat.save()
            chat.users.add(friend)
            chat.save()
            # time.sleep(5)
            print("COME ON...")
            print(request.user)
            print(chat.users.all())
            print(chat.title)

        # if chat already exists, retrieve the chat - integrity error arises when room title already exists
        # as the title field is unique
        except IntegrityError:
            chat = PrivateChat.objects.get(title=title)

        chat = PrivateChat.objects.get(title=title)
        print("USERS!")
        print(chat.title)
        print(chat.users.all())
        payload['room_id'] = chat.id
        payload['response'] = "success"
        return HttpResponse(json.dumps(payload), content_type="application/json")


def get_previous_messages_private(request):
    if request.method == "GET":
        message_id = request.GET.get('message_id')
        room_id = request.GET.get('room_id')
        chatroom = PrivateChat.objects.get(id=room_id)
        oldest_message = PrivateMessages.objects.get(id=message_id)
        previous_messages = PrivateMessages.objects.filter(room=chatroom, id__lt=oldest_message.id).order_by('-id')[:40]
        response_data = {'messages': []}
        for message in previous_messages:
            message_data = {'id': message.id, 'userid': message.user.id, 'message': message.message, 'timestamp': user_time.isoformat(), 'username': message.user.username, 'profile_pic': message.user.profile_image.url}
            response_data['messages'].append(message_data)
        return JsonResponse(response_data)
    

def update_chatroom_unread_messages(request):
    payload = {}
    if request.method == "POST":
        recipient_id = request.POST.get('recipient_id')
        room_id = request.POST.get('room_id')
        recipient = Account.objects.get(id=recipient_id)
        room = PrivateChat.objects.get(id=room_id)
        try:
            MessageNotifications.objects.filter(recipient=recipient, room=room, read=False).update(read=True)
        except:
            payload['response'] = "no notifications to update"
        payload['response'] = "success"
        return HttpResponse(json.dumps(payload), content_type="application/json")
