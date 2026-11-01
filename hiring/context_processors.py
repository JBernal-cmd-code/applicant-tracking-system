from hiring.models import JobOpening


def open_jobs(request):
    # A lazy queryset: it only hits the database on pages that render the sidebar.
    return {"sidebar_open_jobs": JobOpening.objects.filter(status=JobOpening.Status.OPEN)}
