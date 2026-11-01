from django.contrib import admin
from django.urls import include, path

from hiring.views.accounts import StaffLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", StaffLoginView.as_view(), name="login"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("hiring.urls")),
]
