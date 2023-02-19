from django.urls import path, reverse_lazy
from . import views

app_name='friends'
urlpatterns = [
    path('friend_request/', views.send_friend_request, name="friend_request"),
    path('<int:pk>/friends_requests/', views.FriendRequestsView.as_view(), name="friend_requests"),
    path('<int:pk>/friend_list/', views.FriendListView.as_view(), name="friend_list"),
    path('friend_request_accept/', views.accept_friend_request, name="accept_friend_request"),
    path('friend_request_decline/', views.decline_friend_request, name="decline_friend_request"),
    path('friend_request_cancel/', views.cancel_friend_request, name="cancel_friend_request"),
    path('friend_remove/', views.unfriend, name="remove_friend"),
]