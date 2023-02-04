from django.views import View
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse

from publicchat.models import PublicChat, PublicMessages


class PublicChatView(View):
    template_name = "publicchat/chat.html"

    def get(self, request):
        return render(request, self.template_name)