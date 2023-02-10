from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin

from account.forms import RegistrationForm
from account.models import AccountInfo, Account


class RegisterView(View):

    def get(self, request):
        user = request.user
        if user.is_authenticated:
            return HttpResponse(f'You are already authenticated as {user.email}')

        return render(request, 'account/register.html')

    def post(self, request):
        form = RegistrationForm(request.POST)
        if not form.is_valid():
            ctx = {"form": form}
            return render(request, 'account/register.html', ctx)
        form.save()
        email = form.cleaned_data.get("email").lower()
        pw = form.cleaned_data.get("password1")
        account = authenticate(email=email, password=pw)
        login(request, account)
        redirect_url = reverse("home:all")
        return redirect(redirect_url)


class ProfileView(View):
    template_name = "account/account.html"

    def get(self, request, pk):
        account = get_object_or_404(Account, id=pk)
        info = None

        try:
            info = AccountInfo.objects.get(owner=pk)
        except:
            pass

        user = request.user

        is_self = True
        is_friend = False

        if user.is_authenticated and user != account:
            is_self = False
        elif not user.is_authenticated:
            is_self = False

        ctx = {'info': info, 'account': account, 'is_self': is_self, 'is_friend': is_friend}

        return render(request, self.template_name, ctx)