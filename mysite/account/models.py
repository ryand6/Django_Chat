from django.db import models
from django.core.validators import MinLengthValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings

from taggit.managers import TaggableManager


class ChatAccountManager(BaseUserManager):

    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a username")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
        )
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True

        user.save(using=self._db)
        return user


def get_profile_image_path(self, filename):
    return f"profile_images/{self.pk}/profile_image.png"


def get_default_image_path():
    return "chat_images/placeholder.png"


class Account(AbstractBaseUser):
    email = models.EmailField(verbose_name="email", max_length=255, unique=True)
    username = models.CharField(max_length=25, unique=True)
    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    profile_image = models.ImageField(max_length=255, null=True, blank=True, upload_to=get_profile_image_path, default=get_default_image_path)
    hide_email = models.BooleanField(default=True)
    online_status = models.CharField(default="offline", max_length=15)

    objects = ChatAccountManager()

    # make user login with email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    def get_uploaded_image_filename(self):
        return str(self.profile_image)[str(self.profile_image).index(f'{self.pk}/') + len(str(self.pk)) + 1:]


class AccountInfo(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True, validators=[MinLengthValidator(2, "Name must be more than two characters.")])
    summary = models.TextField(max_length=200, null=True, blank=True)
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='info')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    tags = TaggableManager(blank=True)

    def __str__(self):
        if self.name is not None:
            return self.name
        elif self.summary is not None:
            return self.summary
        else:
            return "Unknown"

