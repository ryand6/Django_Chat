from django.views import View
from django.http import HttpResponse
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
            recent_messages = PublicMessages.objects.filter(room=chatroom).order_by('-created_at')[:40]
            recent_messages = recent_messages[::-1]
        except:
            print('error - no chat messages found')
            recent_messages = None

        ctx = {'username': username, 'recent_messages': recent_messages} 

        return render(request, self.template_name, ctx)