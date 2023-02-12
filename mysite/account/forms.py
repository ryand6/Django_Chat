from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate

from account.models import Account, AccountInfo


class RegistrationForm(UserCreationForm):
    # add email address field (not present in UserCreationForm)
    email = forms.EmailField(max_length=255, help_text="Please add a valid email address")

    # link to Account model as no longer using django's standard User model
    class Meta:
        model = Account
        # fields required for registration
        fields = ('email', 'username', 'password1', 'password2')

    # clean email address field and convert email address used to register to lowercase - email address provided in signin also to be cast to lowercase
    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        # check if an account already exists with the email address provided and handle errors accordingly
        try:
            account = Account.objects.get(email=email)
        except Account.DoesNotExist:
            return email
        else:
            raise forms.ValidationError(f'Account under email address {email} already exists')

    def clean_username(self):
        username = self.cleaned_data['username']
        # check if an account already exists with the username provided and handle errors accordingly
        try:
            account = Account.objects.get(username=username)
        except Account.DoesNotExist:
            return username
        else:
            raise forms.ValidationError(f'Account under username {username} already exists')


class AccountUpdateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('id', None)
        super().__init__(*args, **kwargs)


    class Meta:
        model = Account
        fields = ('username', 'profile_image')

    # def clean_email(self):
    #     email = self.cleaned_data['email'].lower()
    #     try:
    #         account = Account.objects.get(email=email)
    #     except Account.DoesNotExist:
    #         return email
    #     else:
    #         raise forms.ValidationError(f'Account under email address {email} already exists')

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            account = Account.objects.get(username=username)
        except Account.DoesNotExist:
            return username
        else:
            if account.id == self.user_id:
                return username
            else:
                raise forms.ValidationError(f'Account under username {username} already exists')

    def save(self, commit=True):
        account = super(AccountUpdateForm, self).save(commit=False)
        account.username = self.cleaned_data['username']
        # account.email = self.cleaned_data['email']
        account.profile_image = self.cleaned_data['profile_image']
        if commit:
            account.save()
        return account


class AccountInfoUpdateForm(forms.ModelForm):

    class Meta:
        model = AccountInfo
        fields = ('name', 'summary', 'tags')

        def save(self, commit=True):
            info = super(AccountInfoUpdateForm, self).save(commit=False)
            if commit:
                info.save()
                self.save_m2m()
            return info

