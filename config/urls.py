from django.contrib import admin
from django.urls import include, path

from .views import landing_page

urlpatterns = [
    path("", landing_page, name="landing_page"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("users/", include("apps.users.urls")),
    path("meetings/", include("apps.meetings.urls")),
    path("email/", include("apps.email_ai.urls")),
]
