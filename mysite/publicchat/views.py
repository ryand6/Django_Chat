import logging

from django.views import View
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from publicchat.models import PublicChat, PublicMessages
from account.models import Account


logger = logging.getLogger('django')


class PublicChatView(View):
    template_name = "publicchat/chat.html"

    def get(self, request):
        userid = request.user.id
        username = request.user.username
        try:
            chatroom = PublicChat.objects.all().first()
            if chatroom is None:
                chatroom = PublicChat(title="public_chat")
                chatroom.save()
            # if database is empty/reset and no one has been added to the public chatroom users list - add the
            # superuser to the users list so that when new users register (the point where users are added to public chatroom)
            # it won't throw an exception as the instance of the chatroom has been initialised and has atleast 1x user
            # note, might need to change db model to accept the users list as null, otherwise necessary step to create a superuser
            # and have them click on the public chatroom before any new users register
            if not chatroom.users.all():
                accounts = Account.objects.all()
                for account in accounts:
                    chatroom.users.add(account)
            chat_users = chatroom.users.all()
            # get user's local timezone based on their timezone offset when compared to UTC
            timezone_offset = request.session.get('tz_offset', None)
            if timezone_offset is not None:
                timezone_offset = int(timezone_offset) * -1
                user_timezone = timezone.get_fixed_timezone(timezone_offset)
            else:
                user_timezone = 0
            recent_messages = PublicMessages.objects.filter(room=chatroom).order_by('-id')[:40]
            recent_messages = recent_messages[::-1]
        except Exception as e:
            logger.warning('PublicChatView - no messages found for public chat room')
            recent_messages = None
            chat_users = None
            user_timezone = 0
        ctx = {'userid': userid, 'username': username, 'recent_messages': recent_messages, 'chat_users': chat_users, 'user_timezone': user_timezone} 
        return render(request, self.template_name, ctx)
    

def get_previous_messages(request):
    if request.method == "GET":
        message_id = request.GET.get('message_id')
        chatroom = PublicChat.objects.all().first()
        oldest_message = PublicMessages.objects.get(id=message_id)
        previous_messages = PublicMessages.objects.filter(room=chatroom, id__lt=oldest_message.id).order_by('-id')[:40]
        response_data = {'messages': []}
        for message in previous_messages:
            message_data = {'id': message.id, 'userid': message.user.id, 'message': message.message, 'timestamp': message.created_at.isoformat(), 'username': message.user.username, 'profile_pic': message.user.profile_image.url}
            response_data['messages'].append(message_data)
        return JsonResponse(response_data)
    