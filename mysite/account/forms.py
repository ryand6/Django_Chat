from django import forms
from django.contrib.auth.forms import UserCreationForm

from account.models import Account, AccountInfo
from home.views import sanitise_text


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
        if sanitise_text(username) != username:
            raise forms.ValidationError("Username contains profanity")
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
        fields = ('username',)

    def clean_username(self):
        username = self.cleaned_data['username']
        if sanitise_text(username) != username:
            raise forms.ValidationError("Username contains profanity")

        try:
            account = Account.objects.get(username=username)
        except Account.DoesNotExist:
            return username
        else:
            # if account exists but is current user, don't raise errors
            # means user doesn't have to edit field if they don't want to update username
            if account.id == self.user_id:
                return username
            else:
                raise forms.ValidationError(f'Account under username {username} already exists')

    def save(self, commit=True):
        account = super(AccountUpdateForm, self).save(commit=False)
        account.username = self.cleaned_data['username']
        if commit:
            account.save()
        return account


class AccountInfoUpdateForm(forms.ModelForm):

    class Meta:
        model = AccountInfo
        fields = ('name', 'summary', 'tags')

    def clean_name(self):
        name = self.cleaned_data['name']
        if name is None:
            return name
        if sanitise_text(name) != name:
            raise forms.ValidationError("Name contains profanity.")
        return name

    def clean_summary(self):
        summary = self.cleaned_data['summary']
        if summary is None:
            return summary
        if sanitise_text(summary) != summary:
            raise forms.ValidationError("Summary contains profanity.")
        return summary

    def clean_tags(self):
        tags = self.cleaned_data['tags']
        if tags is None:
            return tags
        for tag in tags:
            if sanitise_text(tag) != tag:
                raise forms.ValidationError(f"Tag '{tag}' contains profanity.")
        return tags

    def save(self, commit=True):
        info = super(AccountInfoUpdateForm, self).save(commit=False)
        if commit:
            info.save()
            # required to save tags
            self.save_m2m()
        return info