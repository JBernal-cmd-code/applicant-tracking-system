from django.urls import path

from hiring.views import dashboard, skills

app_name = "hiring"

urlpatterns = [
    path("", dashboard.dashboard, name="dashboard"),
    path("skills/", skills.skill_list, name="skill_list"),
    path("skills/new/", skills.skill_create, name="skill_create"),
    path("skills/<int:pk>/edit/", skills.skill_edit, name="skill_edit"),
]
