from django.urls import path, reverse_lazy
from . import views

app_name='account'
urlpatterns = [
    path('register/', views.RegisterView.as_view(), name="register"),
    path('<int:pk>/', views.ProfileView.as_view(), name="profile"),
    path('<int:pk>/edit/', views.EditProfileView.as_view(), name="edit"),
    path('search/', views.AccountSearch.as_view(), name="search"),
    path('<int:pk>/edit/crop_image/', views.crop_image, name="crop_image"),
    path('store_timezone_offset/', views.store_timezone_offset, name="store_timezone_offset"),
]