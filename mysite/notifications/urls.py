from django.urls import path, reverse_lazy
from . import views

app_name='notifications'
urlpatterns = [
    path('update_notifications/', views.update_message_notifications, name='update_notifications'),
    path('update_friend_notifications/', views.update_friend_notifications, name='update_friend_notifications'),
    path('update_accepted_friend_request_notifications/', views.update_friend_request_accepted_notifications, name='update_friend_notifications'),
]