from django.urls import path, include
from . import views
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

app_name = "common"

urlpatterns = [
    path("", views.Redirect, name="redirect"),
    path("login/", views.loginView, name="login"),
    path("logout/", views.logoutView, name="logout"),
    path("change-password/", views.changePassword, name="change_password"),
]