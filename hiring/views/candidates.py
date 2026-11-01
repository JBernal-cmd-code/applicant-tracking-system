from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

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
    return render(request, "hiring/candidate_detail.html", {"candidate": candidate})


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
