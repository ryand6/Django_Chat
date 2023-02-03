from django.urls import path, reverse_lazy
from . import views

app_name='chat'
urlpatterns = [
    path('', views.MainView.as_view(), name='all'),

]