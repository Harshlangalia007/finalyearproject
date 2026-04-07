from django.contrib import admin
from django.urls import include, path

from .views import dashboard_page, landing_page

urlpatterns = [
    path("", landing_page, name="landing_page"),
    path("dashboard/", dashboard_page, name="dashboard_page"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("users/", include("apps.users.urls")),
    path("meetings/", include("apps.meetings.urls")),
    path("email/", include("apps.email_ai.urls")),
]
