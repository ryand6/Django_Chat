from django.urls import path
from . import views

app_name='publicchat'
urlpatterns = [
    path('', views.PublicChatView.as_view(), name='all'),
    path('get_previous_messages/', views.get_previous_messages, name='get_previous_messages'),
]