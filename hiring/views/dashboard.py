from django.shortcuts import render

from hiring.models import StageChange

RECENT_CHANGES_LIMIT = 25


def dashboard(request):
    stage_changes = StageChange.objects.select_related(
        "application__candidate", "application__job", "changed_by"
    )[:RECENT_CHANGES_LIMIT]
    return render(request, "hiring/dashboard.html", {"stage_changes": stage_changes})
