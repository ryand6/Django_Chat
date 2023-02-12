from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.utils.safestring import mark_safe

from account.forms import RegistrationForm, AccountUpdateForm, AccountInfoUpdateForm
from account.models import AccountInfo, Account

from django.db.models import Q


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


class AccountSearch(View):
    template_name = "account/search.html"

    def get(self, request):
        search_query = request.GET.get("search", False)
        if search_query:
            info_check = AccountInfo.objects.all()
            if not info_check:
                results = Account.objects.filter(username__icontains=search_query)
            else:
                res1 = Account.objects.filter(Q(username__icontains=search_query))
                res2 = AccountInfo.objects.filter(Q(name__icontains=search_query) | Q(tags__name__in=[search_query]))

                results = list(res1) + list(res2)

                final_results = list()
                seen_keys = set()
                for res in results:
                    if isinstance(res, Account):
                        if res.id not in seen_keys:
                            seen_keys.add(res.id)
                            final_results.append(res)
                    elif isinstance(res, AccountInfo):
                        if res.owner.id not in seen_keys:
                            seen_keys.add(res.owner.id)
                            # replace the result with the account that matches this and add it to the results
                            # as all searches are done on primary keys, therefore the primary key of an account info
                            # result would return the wrong search result
                            account_res = Account.objects.get(id=res.owner.id)
                            final_results.append(account_res)
                results = final_results

            accounts = []
            for account in results:
                accounts.append((account, False))
        else:
            accounts = []

        ctx = {'accounts': accounts}
        return render(request, self.template_name, ctx)


class EditProfileView(View):
    template_name = 'account/update.html'


    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect("login")
        account = get_object_or_404(Account, pk=pk)
        if account.pk != request.user.pk:
            raise PermissionDenied
        else:
            try:
                info = AccountInfo.objects.get(owner=request.user.pk)
            except:
                info = None

            account_form = AccountUpdateForm(instance=request.user)
            info_form = AccountInfoUpdateForm(instance=info)

            # show users previously submitted summary so they can choose not to edit
            summary = mark_safe(info_form.initial['summary'].replace(' ', '&nbsp;'))
            if not summary:
                summary = "Summary"

            # show comma delimited list of users previously submitted interest tags
            info_form.initial['tags'] = ', '.join([tag.name for tag in info_form.initial['tags']])
            info_form.initial['tags'] = mark_safe(info_form.initial['tags'].replace(' ', '&nbsp;'))

            MAX_DATA_UPLOAD = settings.MAX_DATA_UPLOAD
            ctx = {'account_form': account_form, 'info_form': info_form, 'summary': summary, 'MAX_DATA_UPLOAD': MAX_DATA_UPLOAD}

            return render(request, self.template_name, ctx)



    def post(self, request, pk=None):
        account_form = AccountUpdateForm(request.POST, request.FILES, instance=request.user, id=request.user.id)

        if not account_form.is_valid():
            ctx = {'account_form': account_form}
            return render(request, self.template_name, ctx)

        try:
            info = AccountInfo.objects.get(owner=request.user)
        except:
            info = None

        info_form = AccountInfoUpdateForm(request.POST, instance=info)

        if not info_form.is_valid():
            ctx = {'info_form': info_form, 'account_form': account_form}
            return render(request, self.template_name, ctx)

        info = info_form.save(commit=False)
        info.owner = request.user
        info.save()
        info_form.save_m2m()

        account.profile_image.delete()
        account_form.save()

        success_url = reverse("account:profile", args={request.user.pk,})

        return redirect(success_url)

