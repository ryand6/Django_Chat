from django.urls import path, reverse_lazy
from . import views

app_name='privatechat'
urlpatterns = [
    path('<int:user_id>/all_chats/', views.PrivateChatAllChatsView.as_view(), name='all'),
    path('<int:room_id>/chat/', views.PrivateChatView.as_view(), name='chat'),
    path('update_chat_log/', views.update_chat_log, name='update_chat_log'),
    path('create_chat/', views.create_chat, name='create_chat'),
    path('get_previous_messages_private/', views.get_previous_messages_private, name='get_previous_messages_private'),
]