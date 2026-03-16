from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("users/", include("apps.users.urls")),
    path("meetings/", include("apps.meetings.urls")),
    path("email/", include("apps.email_ai.urls")),
]
