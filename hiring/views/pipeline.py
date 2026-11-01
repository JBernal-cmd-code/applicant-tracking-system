from django.shortcuts import get_object_or_404, render

from hiring.models import Application
from hiring.stages import Stage


def pipeline_context(job, selected_pk=None):
    """Applicants grouped by stage, plus the selected one if it belongs to this job."""
    applications = job.applications.select_related("candidate")
    stages = [{"value": stage.value, "label": stage.label, "applications": []} for stage in Stage]
    by_value = {stage["value"]: stage for stage in stages}
    selected = None
    for application in applications:
        by_value[application.stage]["applications"].append(application)
        # Compared as text so a junk or foreign ?application= value simply selects nothing.
        if str(application.pk) == str(selected_pk):
            selected = application
    return {
        "job": job,
        "stages": stages,
        "has_applications": bool(applications),
        "selected": selected,
    }


def application_panel(request, pk):
    application = get_object_or_404(Application, pk=pk)
    context = pipeline_context(application.job, application.pk)
    return render(request, "hiring/partials/applicant_panel_response.html", context)
