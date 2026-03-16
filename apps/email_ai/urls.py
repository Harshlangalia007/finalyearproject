from django.urls import path
from . import views

urlpatterns = [
    path('', views.email_dashboard, name='email_dashboard'),
]
