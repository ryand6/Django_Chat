import datetime
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse

from publicchat.models import PublicChat, PublicMessages


class PublicChatView(View):
    template_name = "publicchat/chat.html"

    def get(self, request):
        username = request.user.username
        try:
            chatroom = PublicChat.objects.all().first()
            recent_messages = PublicMessages.objects.filter(room=chatroom).order_by('-id')[:40]
            recent_messages = recent_messages[::-1]
        except:
            print('error - no chat messages found')
            recent_messages = None

        ctx = {'username': username, 'recent_messages': recent_messages} 

        return render(request, self.template_name, ctx)
    

def get_previous_messages(request):
    if request.method == "GET":
        message_id = request.GET.get('message_id')
        chatroom = PublicChat.objects.all().first()

        oldest_message = PublicMessages.objects.get(id=message_id)
        previous_messages = PublicMessages.objects.filter(room=chatroom, id__lt=oldest_message.id).order_by('-id')[:40]
        response_data = {'messages': []}
        for message in previous_messages:
            message_data = {'id': message.id, 'message': message.message, 'timestamp': message.created_at.isoformat(), 'username': message.user.username, 'profile_pic': message.user.profile_image.url}
            response_data['messages'].append(message_data)
        return JsonResponse(response_data)