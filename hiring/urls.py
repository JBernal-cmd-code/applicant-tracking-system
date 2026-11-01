from django.urls import path

from hiring.views import dashboard

app_name = "hiring"

urlpatterns = [
    path("", dashboard.dashboard, name="dashboard"),
]
