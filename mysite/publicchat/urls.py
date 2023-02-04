from django.urls import path, reverse_lazy
from . import views

app_name='publicchat'
urlpatterns = [
    path('', views.PublicChatView.as_view(), name='all'),
]