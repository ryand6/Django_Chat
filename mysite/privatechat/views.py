from django.views import View
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse


class PrivateChatView(View):
    template_name = "privatechat/chat.html"

    def get(self, request):
        return render(request, self.template_name)