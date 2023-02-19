import os
import cv2
import base64
import json
import requests

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.utils.safestring import mark_safe
from django.core.files.storage import default_storage, FileSystemStorage
from django.core import files

from account.forms import RegistrationForm, AccountUpdateForm, AccountInfoUpdateForm
from account.models import AccountInfo, Account
from friends.models import FriendList, FriendRequest
from friends.views import is_friend_request_active

from django.db.models import Q


TEMP_IMAGE_NAME = "temp_profile_image.png"


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

        # if friend list doesn't exist for user, create empty one 
        try:
            friend_list = FriendList.objects.get(owner=account)
        except FriendList.DoesNotExist:
            friend_list = FriendList(owner=account)
            friend_list.save()
        
        friends = friend_list.friends.all()

        user = request.user
        is_self = True
        is_friend = False
        received_friend_request = False
        sent_friend_request = False
        received_friend_request_id = None
        active_friend_requests = None

        ctx = {'info': info, 'account': account, 'friends': friends}

        if user.is_authenticated and user != account:
            is_self = False
            if friends.filter(pk=user.id):
                is_friend = True
            else:
                is_friend = False
                # check if account sent you a friend request
                if is_friend_request_active(sender=account, receiver=user):
                    received_friend_request = True
                    # get pk of friend request object so that friend request object can be altered by javascript in the template i.e. made inactive
                    received_friend_request_id = is_friend_request_active(sender=account, receiver=user).id
                # check is user sent account friend request
                elif is_friend_request_active(sender=user, receiver=account):
                    sent_friend_request = True
        elif not user.is_authenticated:
            is_self = False
        else:
            try:
                active_friend_requests = FriendRequest.objects.filter(receiver=user, is_active_request=True) 
            except:
                pass
        
        ctx['is_self'] = is_self
        ctx['is_friend'] = is_friend
        ctx['received_friend_request'] = received_friend_request
        ctx['sent_friend_request'] = sent_friend_request
        ctx['received_friend_request_id'] = received_friend_request_id
        ctx['active_friend_requests'] = active_friend_requests

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
            try:
                summary = mark_safe(info_form.initial['summary'].replace(' ', '&nbsp;'))
            except:
                summary = ""

            # show comma delimited list of users previously submitted interest tags
            try:
                info_form.initial['tags'] = ', '.join([tag.name for tag in info_form.initial['tags']])
                info_form.initial['tags'] = mark_safe(info_form.initial['tags'].replace(' ', '&nbsp;'))
            except:
                info_form.initial['tags'] = ""

            MAX_DATA_UPLOAD = settings.MAX_DATA_UPLOAD
            ctx = {'account_form': account_form, 'info_form': info_form, 'summary': summary, 'account_profile_image': account.profile_image.url, 'MAX_DATA_UPLOAD': MAX_DATA_UPLOAD}

            return render(request, self.template_name, ctx)


    def post(self, request, pk):
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

        account_form.save()

        success_url = reverse("account:profile", args={request.user.pk,})

        return redirect(success_url)


def save_temp_image(image_b64, user):
    try:
        if not os.path.exists(settings.TEMP):
            os.mkdir(settings.TEMP)
        # account for different os filepaths - '/' or '\'
        path = os.path.join(settings.TEMP, str(user.pk))
        if not os.path.exists(path):
            os.mkdir(path)
        # filepath for saving temp image
        url = os.path.join(path, TEMP_IMAGE_NAME)
        storage = FileSystemStorage(location=url)
        # https://stackoverflow.com/questions/2941995/python-ignore-incorrect-padding-error-when-base64-decoding
        # add maximum number of padding required to base64 string before decoding to prevent any incorrect padding
        # errors occurring if the base64 string is corrupted - if padding already exists, Python will safely discard
        # additional padding as validate defaults to False, preventing binascii.Error
        image = base64.b64decode(image_b64 + '==')
        with storage.open('', 'wb+') as destination:
            destination.write(image)
        return url
    except Exception as e:
        raise e
    return None


def crop_image(request, *args, **kwargs):
    payload = {}
    user = request.user
    if request.POST and user.is_authenticated:
        try:
            image_b64 = request.POST.get("image")
            url = save_temp_image(image_b64, user)
            # load image from filepath
            image = cv2.imread(url)
            
            # get x and y coords of bottom left corner of crop square
            x_coord = int(float(str(request.POST.get('x_coord'))))
            y_coord = int(float(str(request.POST.get('y_coord'))))

            # get width and height of crop square
            crop_width = int(float(str(request.POST.get('crop_width'))))
            crop_height = int(float(str(request.POST.get('crop_height'))))

            # if either x or y coords are near to edge of pic, sometimes might get passed as -1 
            # change to 0 to prevent errors
            if x_coord < 0:
                x_coord = 0
            if y_coord < 0:
                y_coord = 0
            
            crop_image = image[y_coord:y_coord + crop_height, x_coord:x_coord + crop_width]

            cv2.imwrite(url, crop_image)

            # delete previously stored image for user
            if user.profile_image:
                user.profile_image.delete()

            user.profile_image.save("profile_image.png", files.File(open(url, "rb")))
            user.save()

            payload['result'] = "success"
            payload['cropped_image'] = user.profile_image.url

            # remove temp file
            os.remove(url)

        except Exception as e:
            payload['result'] = "error"
            payload['exception'] = str(e)

    return HttpResponse(json.dumps(payload), content_type="application/json")