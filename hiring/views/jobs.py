from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from hiring.forms import JobOpeningForm
from hiring.models import JobOpening


def job_list(request):
    # Search and Open / Closed / All filters arrive in Phase 5.
    jobs = JobOpening.objects.prefetch_related("skills")
    return render(request, "hiring/job_list.html", {"jobs": jobs})


def job_detail(request, pk):
    job = get_object_or_404(JobOpening.objects.prefetch_related("skills"), pk=pk)
    return render(request, "hiring/job_detail.html", {"job": job})


def job_create(request):
    form = JobOpeningForm(request.POST or None)
    if form.is_valid():
        job = form.save()
        messages.success(request, f"Job opening “{job}” added.")
        return redirect("hiring:job_detail", pk=job.pk)
    return render(request, "hiring/job_form.html", {"form": form})


def job_edit(request, pk):
    job = get_object_or_404(JobOpening, pk=pk)
    form = JobOpeningForm(request.POST or None, instance=job)
    if form.is_valid():
        form.save()
        messages.success(request, f"Job opening “{job}” saved.")
        return redirect("hiring:job_detail", pk=job.pk)
    return render(request, "hiring/job_form.html", {"form": form, "job": job})
