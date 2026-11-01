from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.urls import reverse
from django.utils import timezone

from hiring.forms import ApplicationForm
from hiring.models import Application
from hiring.stages import Stage

pytestmark = pytest.mark.django_db


def test_model_validation_refuses_application_to_closed_job(candidate, closed_job):
    application = Application(candidate=candidate, job=closed_job)

    with pytest.raises(ValidationError, match="This job is closed"):
        application.full_clean()


def test_form_offers_only_active_candidates_who_have_not_applied_to_this_job(
    make_candidate, make_job, make_application
):
    job = make_job()
    other_job = make_job()
    eligible = make_candidate(first_name="Eligible")
    applied_elsewhere = make_candidate(first_name="Elsewhere")
    make_application(applied_elsewhere, other_job)
    already_applied = make_candidate(first_name="Applied")
    make_application(already_applied, job)
    make_candidate(first_name="Archived", archived=True)

    form = ApplicationForm(job=job)

    assert set(form.fields["candidate"].queryset) == {eligible, applied_elsewhere}


def test_stale_duplicate_submission_is_refused_with_candidate_error(
    staff_client, candidate, open_job, make_application
):
    # The form was loaded before a colleague added this candidate to the job.
    make_application(candidate, open_job)

    response = staff_client.post(
        reverse("hiring:application_create", args=[open_job.pk]),
        {"candidate": candidate.pk, "notes": ""},
    )

    assert response.status_code == 200
    assert response.context["form"].errors == {
        "candidate": ["This candidate is archived or has already applied to this job."]
    }
    assert Application.objects.count() == 1


def test_database_rejects_second_application_for_same_candidate_and_job(
    candidate, open_job, make_application
):
    make_application(candidate, open_job)

    with pytest.raises(IntegrityError):
        make_application(candidate, open_job)


def test_applications_protect_candidate_and_job_from_deletion(
    candidate, open_job, make_application
):
    make_application(candidate, open_job)

    with pytest.raises(ProtectedError):
        candidate.delete()
    with pytest.raises(ProtectedError):
        open_job.delete()


def test_model_validation_allows_existing_application_after_job_closes(
    candidate, open_job, make_application
):
    application = make_application(candidate, open_job)
    open_job.close()
    application.refresh_from_db()

    application.full_clean()


def test_add_application_creates_it_in_applied_with_toast(staff_client, candidate, open_job):
    response = staff_client.post(
        reverse("hiring:application_create", args=[open_job.pk]),
        {"candidate": candidate.pk, "notes": "Referred by Sam.", "stage": Stage.OFFER},
        follow=True,
    )

    application = Application.objects.get()
    assert (application.candidate, application.job) == (candidate, open_job)
    assert application.stage == Stage.APPLIED
    assert application.notes == "Referred by Sam."
    assert response.request["PATH_INFO"] == reverse("hiring:job_detail", args=[open_job.pk])
    assert "Application from “Ada Lovelace” added." in response.content.decode()


def test_add_application_form_page_lists_eligible_candidates(staff_client, candidate, open_job):
    response = staff_client.get(reverse("hiring:application_create", args=[open_job.pk]))

    assert response.status_code == 200
    assert f'<option value="{candidate.pk}"' in response.content.decode()


@pytest.mark.parametrize("method", ["get", "post"])
def test_add_application_to_closed_job_is_refused(staff_client, candidate, closed_job, method):
    url = reverse("hiring:application_create", args=[closed_job.pk])

    response = getattr(staff_client, method)(url, {"candidate": candidate.pk}, follow=True)

    assert not Application.objects.exists()
    assert response.request["PATH_INFO"] == reverse("hiring:job_detail", args=[closed_job.pk])
    assert "is closed to new applications" in response.content.decode()


def test_add_application_button_shows_only_on_open_jobs(staff_client, open_job, closed_job):
    def page(job):
        return staff_client.get(reverse("hiring:job_detail", args=[job.pk])).content.decode()

    assert reverse("hiring:application_create", args=[open_job.pk]) in page(open_job)
    assert reverse("hiring:application_create", args=[closed_job.pk]) not in page(closed_job)


def test_application_pages_require_login(client, open_job):
    response = client.get(reverse("hiring:application_create", args=[open_job.pk]))

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("login"))


def summary_counts(response):
    return {stage["value"]: len(stage["applications"]) for stage in response.context["stages"]}


def test_summary_bar_counts_all_eight_stages_including_zeros(
    staff_client, open_job, make_job, make_candidate, make_application
):
    make_application(make_candidate(), open_job)
    make_application(make_candidate(), open_job)
    make_application(make_candidate(), open_job, stage=Stage.INTERVIEW)
    make_application(make_candidate(), open_job, stage=Stage.REJECTED)
    make_application(make_candidate(), make_job())

    response = staff_client.get(reverse("hiring:job_detail", args=[open_job.pk]))

    assert summary_counts(response) == {
        "applied": 2,
        "screening": 0,
        "interview": 1,
        "final_review": 0,
        "offer": 0,
        "hired": 0,
        "rejected": 1,
        "withdrawn": 0,
    }
    content = response.content.decode()
    for label in Stage.labels:
        assert label in content


def test_applicants_are_grouped_by_stage_with_days_in_stage(
    staff_client, open_job, make_candidate, make_application
):
    grace = make_application(make_candidate(first_name="Grace", last_name="Hopper"), open_job)
    Application.objects.filter(pk=grace.pk).update(created_at=timezone.now() - timedelta(days=3))
    make_application(
        make_candidate(first_name="Alan", last_name="Turing"), open_job, stage=Stage.OFFER
    )

    response = staff_client.get(reverse("hiring:job_detail", args=[open_job.pk]))

    groups = {
        stage["label"]: [str(a.candidate) for a in stage["applications"]]
        for stage in response.context["stages"]
        if stage["applications"]
    }
    assert groups == {"Applied": ["Grace Hopper"], "Offer": ["Alan Turing"]}
    content = response.content.decode()
    assert "3 days" in content
    assert "today" in content


def test_job_page_without_applications_says_so(staff_client, open_job):
    content = staff_client.get(reverse("hiring:job_detail", args=[open_job.pk])).content.decode()

    assert "No applications yet." in content


def test_closing_a_job_leaves_application_stages_unchanged(
    staff_client, open_job, make_candidate, make_application
):
    applied = make_application(make_candidate(), open_job)
    offer = make_application(make_candidate(), open_job, stage=Stage.OFFER)

    staff_client.post(reverse("hiring:job_close", args=[open_job.pk]))

    applied.refresh_from_db()
    offer.refresh_from_db()
    assert (applied.stage, offer.stage) == (Stage.APPLIED, Stage.OFFER)


def test_candidate_page_lists_applications_with_job_stage_and_days(
    staff_client, candidate, make_job, make_application
):
    backend = make_job(title="Backend Developer")
    analyst = make_job(title="Data Analyst")
    make_application(candidate, backend)
    application = make_application(candidate, analyst, stage=Stage.FINAL_REVIEW)
    Application.objects.filter(pk=application.pk).update(
        created_at=timezone.now() - timedelta(days=1)
    )

    content = staff_client.get(
        reverse("hiring:candidate_detail", args=[candidate.pk])
    ).content.decode()

    assert f'href="{reverse("hiring:job_detail", args=[backend.pk])}"' in content
    assert "Data Analyst" in content
    assert "Final Review" in content
    assert "1 day<" in content


def test_candidate_page_without_applications_says_so(staff_client, candidate):
    content = staff_client.get(
        reverse("hiring:candidate_detail", args=[candidate.pk])
    ).content.decode()

    assert "No applications yet." in content
