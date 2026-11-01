from django.contrib import messages
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from hiring.forms import StageMoveForm
from hiring.models import Application
from hiring.stages import MoveKind, Stage, allowed_moves

# The panel's move buttons, grouped by purpose: (title, hint, kinds).
MOVE_GROUPS = [
    ("Move forward", "Skipping stages is allowed. Hired only from Offer.", {"next", "skip"}),
    ("Fix a mistake", "Step back exactly one stage.", {"back"}),
    ("Close out", "Either side can end the process.", {"reject", "withdraw"}),
]

MOVE_LABELS = {
    MoveKind.NEXT: "Advance to {}",
    MoveKind.SKIP: "Skip to {}",
    MoveKind.BACK: "← Back to {}",
    MoveKind.REJECT: "Reject",
    MoveKind.WITHDRAW: "Withdrew",
}


def move_groups(application):
    moves = allowed_moves(application.stage)
    groups = []
    for title, hint, kinds in MOVE_GROUPS:
        buttons = [
            {
                "stage": move.target.value,
                "kind": move.kind.value,
                "label": MOVE_LABELS[move.kind].format(move.target.label),
            }
            for move in moves
            if move.kind in kinds
        ]
        if buttons:
            groups.append({"title": title, "hint": hint, "buttons": buttons})
    return groups


def pipeline_context(job, selected_pk=None):
    """Applicants grouped by stage, plus the selected one if it belongs to this job."""
    applications = job.applications.select_related("candidate").with_stage_entered_at()
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
        "move_groups": move_groups(selected) if selected else [],
        "stage_changes": selected.stage_changes.select_related("changed_by") if selected else [],
    }


def application_panel(request, pk):
    application = get_object_or_404(Application, pk=pk)
    context = pipeline_context(application.job, application.pk)
    return render(request, "hiring/partials/applicant_panel_response.html", context)


@require_POST
def application_move(request, pk):
    application = get_object_or_404(Application.objects.select_related("candidate"), pk=pk)
    form = StageMoveForm(request.POST, application=application)
    if form.is_valid():
        from_label = application.get_stage_display()
        if application.move_to(form.cleaned_data["stage"], request.user):
            messages.success(
                request,
                f"{application.candidate} moved from {from_label} "
                f"to {application.get_stage_display()}.",
            )
    else:
        # Still a 200: the fresh panel, list and summary show the true current state.
        messages.error(request, form.errors["stage"][0])
    context = pipeline_context(application.job, application.pk)
    return render(request, "hiring/partials/application_move_response.html", context)
