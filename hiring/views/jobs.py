from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRedirect

from hiring.forms import ApplicationForm, JobFilterForm, JobOpeningForm
from hiring.models import JobOpening
from hiring.views.pipeline import pipeline_context


def job_list(request):
    filter_form = JobFilterForm(request.GET)
    jobs = filter_form.filter(JobOpening.objects.prefetch_related("skills"))
    return render(request, "hiring/job_list.html", {"jobs": jobs, "filter_form": filter_form})


def job_detail(request, pk):
    job = get_object_or_404(JobOpening.objects.prefetch_related("skills"), pk=pk)
    context = pipeline_context(job, request.GET.get("application"))
    return render(request, "hiring/job_detail.html", context)


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


def application_create(request, pk):
    job = get_object_or_404(JobOpening, pk=pk)
    if job.status == JobOpening.Status.CLOSED:
        messages.error(request, f"Job opening “{job}” is closed to new applications.")
        return redirect("hiring:job_detail", pk=job.pk)
    form = ApplicationForm(request.POST or None, job=job)
    if form.is_valid():
        application = form.save()
        messages.success(request, f"Application from “{application.candidate}” added.")
        return redirect("hiring:job_detail", pk=job.pk)
    return render(request, "hiring/application_form.html", {"form": form, "job": job})


@require_POST
def job_close(request, pk):
    job = get_object_or_404(JobOpening, pk=pk)
    job.close()
    messages.success(request, f"Job opening “{job}” closed.")
    return _back_to_job(request, job)


@require_POST
def job_reopen(request, pk):
    job = get_object_or_404(JobOpening, pk=pk)
    job.reopen()
    messages.success(request, f"Job opening “{job}” reopened.")
    return _back_to_job(request, job)


def _back_to_job(request, job):
    # Close is posted by HTMX (for its confirm prompt), so a full-page reload
    # is requested instead of swapping the redirected page into the button.
    url = reverse("hiring:job_detail", args=[job.pk])
    if request.htmx:
        return HttpResponseClientRedirect(url)
    return redirect(url)
