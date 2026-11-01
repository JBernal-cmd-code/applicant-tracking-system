from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRedirect

from hiring.forms import CandidateFilterForm, CandidateForm
from hiring.models import Candidate


def candidate_list(request):
    filter_form = CandidateFilterForm(request.GET)
    candidates = filter_form.filter(Candidate.objects.all())
    return render(
        request,
        "hiring/candidate_list.html",
        {"candidates": candidates, "filter_form": filter_form},
    )


def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    applications = candidate.applications.select_related("job").with_stage_entered_at()
    return render(
        request,
        "hiring/candidate_detail.html",
        {"candidate": candidate, "applications": applications},
    )


def candidate_create(request):
    form = CandidateForm(request.POST or None)
    if form.is_valid():
        candidate = form.save()
        messages.success(request, f"Candidate “{candidate}” added.")
        return redirect("hiring:candidate_detail", pk=candidate.pk)
    return render(request, "hiring/candidate_form.html", {"form": form})


def candidate_edit(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    form = CandidateForm(request.POST or None, instance=candidate)
    if form.is_valid():
        form.save()
        messages.success(request, f"Candidate “{candidate}” saved.")
        return redirect("hiring:candidate_detail", pk=candidate.pk)
    return render(request, "hiring/candidate_form.html", {"form": form, "candidate": candidate})


@require_POST
def candidate_archive(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    try:
        candidate.archive()
    except ValidationError as error:
        messages.error(request, error.messages[0])
    else:
        messages.success(request, f"Candidate “{candidate}” archived.")
    return _back_to_candidate(request, candidate)


@require_POST
def candidate_unarchive(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    candidate.unarchive()
    messages.success(request, f"Candidate “{candidate}” unarchived.")
    return _back_to_candidate(request, candidate)


def _back_to_candidate(request, candidate):
    # Archive is posted by HTMX (for its confirm prompt); see jobs._back_to_job.
    url = reverse("hiring:candidate_detail", args=[candidate.pk])
    if request.htmx:
        return HttpResponseClientRedirect(url)
    return redirect(url)
