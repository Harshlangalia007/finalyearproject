from django.urls import path
from . import views

urlpatterns = [
    path('', views.meeting_list, name='meeting_list'),
]
