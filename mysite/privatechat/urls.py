from django.urls import path, reverse_lazy
from . import views

app_name='privatechat'
urlpatterns = [
    path('', views.PrivateChatView.as_view(), name='all'),
]