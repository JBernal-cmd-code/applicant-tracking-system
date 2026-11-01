from django.urls import path

from hiring.views import candidates, dashboard, jobs, skills

app_name = "hiring"

urlpatterns = [
    path("", dashboard.dashboard, name="dashboard"),
    path("candidates/", candidates.candidate_list, name="candidate_list"),
    path("candidates/new/", candidates.candidate_create, name="candidate_create"),
    path("candidates/<int:pk>/", candidates.candidate_detail, name="candidate_detail"),
    path("candidates/<int:pk>/edit/", candidates.candidate_edit, name="candidate_edit"),
    path("jobs/", jobs.job_list, name="job_list"),
    path("jobs/new/", jobs.job_create, name="job_create"),
    path("jobs/<int:pk>/", jobs.job_detail, name="job_detail"),
    path("jobs/<int:pk>/edit/", jobs.job_edit, name="job_edit"),
    path("jobs/<int:pk>/close/", jobs.job_close, name="job_close"),
    path("jobs/<int:pk>/reopen/", jobs.job_reopen, name="job_reopen"),
    path("skills/", skills.skill_list, name="skill_list"),
    path("skills/new/", skills.skill_create, name="skill_create"),
    path("skills/<int:pk>/edit/", skills.skill_edit, name="skill_edit"),
]
