from django.urls import path
from . import views

app_name='notifications'
urlpatterns = [
    path('update_notifications/', views.update_message_notifications, name='update_notifications'),
    path('update_friend_notifications/', views.update_friend_notifications, name='update_friend_notifications'),
    path('update_accepted_friend_request_notifications/', views.update_friend_request_accepted_notifications, name='update_friend_notifications'),
    path('set_user_status_offline/', views.set_user_status_offline, name='set_user_status_offline'),
    path('set_user_status_away/', views.set_user_status_away, name='set_user_status_away'),
    path('set_user_status_online/', views.set_user_status_online, name='set_user_status_online'),
]