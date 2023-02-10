from django.urls import path, reverse_lazy
from . import views

app_name='account'
urlpatterns = [
    path('register/', views.RegisterView.as_view(), name="register"),
    path('<int:pk>/', views.ProfileView.as_view(), name="profile"),
]