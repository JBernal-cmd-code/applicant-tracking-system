import re
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.urls import reverse
from django.utils import timezone

from hiring.forms import ApplicationForm
from hiring.models import Application, Candidate, StageChange
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
    application.stage_changes.update(changed_at=timezone.now() - timedelta(days=1))

    content = staff_client.get(
        reverse("hiring:candidate_detail", args=[candidate.pk])
    ).content.decode()

    assert f'href="{reverse("hiring:job_detail", args=[backend.pk])}?application=' in content
    assert "Data Analyst" in content
    assert "Final Review" in content
    assert "1 day<" in content


def test_panel_fragment_shows_contact_source_stage_and_notes(
    staff_client, open_job, make_candidate, make_application
):
    grace = make_candidate(
        first_name="Grace",
        last_name="Hopper",
        email="grace@example.com",
        phone="555-0100",
        source=Candidate.Source.REFERRAL,
        source_details="Referred by Sam",
    )
    application = make_application(
        grace, open_job, stage=Stage.INTERVIEW, notes="Strong COBOL background."
    )

    response = staff_client.get(reverse("hiring:application_panel", args=[application.pk]))

    content = response.content.decode()
    assert response.status_code == 200
    assert "<html" not in content
    for text in [
        'id="applicant-panel"',
        "Grace Hopper",
        "grace@example.com",
        "555-0100",
        "Referral",
        "Referred by Sam",
        "Interview",
        "Strong COBOL background.",
    ]:
        assert text in content


def test_job_page_with_application_parameter_renders_that_applicant_selected(
    staff_client, open_job, make_candidate, make_application
):
    make_application(make_candidate(first_name="Alan", last_name="Turing"), open_job)
    grace = make_application(
        make_candidate(first_name="Grace", last_name="Hopper"), open_job, notes="Selected one."
    )

    response = staff_client.get(
        reverse("hiring:job_detail", args=[open_job.pk]), {"application": grace.pk}
    )

    content = response.content.decode()
    assert response.context["selected"] == grace
    assert "Selected one." in content
    pipeline_list = content.split('id="pipeline-list"')[1].split('id="applicant-panel"')[0]
    assert pipeline_list.count("menu-active") == 1
    assert 'class="menu-active"' in pipeline_list.split("Grace Hopper")[0].rsplit("<li>", 1)[1]


def test_panel_response_swaps_list_out_of_band_with_applicant_highlighted(
    staff_client, open_job, make_candidate, make_application
):
    application = make_application(make_candidate(), open_job)

    content = staff_client.get(
        reverse("hiring:application_panel", args=[application.pk])
    ).content.decode()

    assert 'id="pipeline-list"' in content
    assert 'hx-swap-oob="true"' in content
    assert 'class="menu-active"' in content


def test_pipeline_list_loads_panel_with_htmx_and_pushes_url(
    staff_client, open_job, make_candidate, make_application
):
    application = make_application(make_candidate(), open_job)
    selected_url = (
        f"{reverse('hiring:job_detail', args=[open_job.pk])}?application={application.pk}"
    )

    content = staff_client.get(reverse("hiring:job_detail", args=[open_job.pk])).content.decode()

    assert f'hx-get="{reverse("hiring:application_panel", args=[application.pk])}"' in content
    assert f'hx-push-url="{selected_url}"' in content
    assert f'href="{selected_url}"' in content


def test_panel_for_missing_application_is_404(staff_client):
    response = staff_client.get(reverse("hiring:application_panel", args=[999999]))

    assert response.status_code == 404


def test_panel_requires_login(client, open_job, make_candidate, make_application):
    application = make_application(make_candidate(), open_job)

    response = client.get(reverse("hiring:application_panel", args=[application.pk]))

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("login"))


def test_candidate_page_links_each_application_to_selected_applicant(
    staff_client, candidate, open_job, make_application
):
    application = make_application(candidate, open_job)

    content = staff_client.get(
        reverse("hiring:candidate_detail", args=[candidate.pk])
    ).content.decode()

    selected_url = (
        f"{reverse('hiring:job_detail', args=[open_job.pk])}?application={application.pk}"
    )
    assert f'href="{selected_url}"' in content


@pytest.mark.parametrize("value", ["other-job", "abc", "999999", ""])
def test_job_page_ignores_application_parameter_not_on_this_job(
    staff_client, open_job, make_job, make_candidate, make_application, value
):
    make_application(make_candidate(), open_job)
    foreign = make_application(make_candidate(), make_job(), notes="Foreign notes.")
    if value == "other-job":
        value = foreign.pk

    response = staff_client.get(
        reverse("hiring:job_detail", args=[open_job.pk]), {"application": value}
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert response.context["selected"] is None
    assert "Foreign notes." not in content
    assert "Select an applicant to see their details." in content


def test_move_to_records_one_stage_change_and_refuses_disallowed_moves(
    candidate, open_job, make_application, staff_user
):
    application = make_application(candidate, open_job)

    application.move_to(Stage.INTERVIEW, staff_user)
    application.move_to(Stage.INTERVIEW, staff_user)  # same stage: nothing happens

    application.refresh_from_db()
    assert application.stage == Stage.INTERVIEW
    change = StageChange.objects.get()
    assert (change.application, change.from_stage, change.to_stage, change.changed_by) == (
        application,
        Stage.APPLIED,
        Stage.INTERVIEW,
        staff_user,
    )
    assert timezone.now() - change.changed_at < timedelta(minutes=1)

    with pytest.raises(ValidationError):
        application.move_to(Stage.HIRED, staff_user)  # Hired only from Offer

    application.refresh_from_db()
    assert application.stage == Stage.INTERVIEW
    assert StageChange.objects.count() == 1


@pytest.mark.parametrize("closed_as", [Stage.REJECTED, Stage.WITHDRAWN])
def test_reopen_returns_application_to_the_stage_it_held_before(
    candidate, open_job, make_application, staff_user, closed_as
):
    application = make_application(candidate, open_job, stage=Stage.FINAL_REVIEW)
    application.move_to(closed_as, staff_user)

    with pytest.raises(ValidationError):
        application.move_to(Stage.APPLIED, staff_user)  # only the previous stage is allowed
    application.move_to(Stage.FINAL_REVIEW, staff_user)

    application.refresh_from_db()
    assert application.stage == Stage.FINAL_REVIEW
    latest = application.stage_changes.first()
    assert (latest.from_stage, latest.to_stage, latest.changed_by) == (
        closed_as,
        Stage.FINAL_REVIEW,
        staff_user,
    )


def test_reopen_is_refused_while_candidate_is_archived(
    candidate, open_job, make_application, staff_user
):
    application = make_application(candidate, open_job, stage=Stage.SCREENING)
    application.move_to(Stage.WITHDRAWN, staff_user)
    candidate.archive()

    with pytest.raises(ValidationError, match="Unarchive"):
        application.move_to(Stage.SCREENING, staff_user)

    application.refresh_from_db()
    assert application.stage == Stage.WITHDRAWN
    assert application.stage_changes.count() == 2


def test_model_validation_refuses_application_from_archived_candidate(make_candidate, open_job):
    application = Application(candidate=make_candidate(archived=True), job=open_job)

    with pytest.raises(ValidationError, match="This candidate is archived"):
        application.full_clean()


def test_stale_submission_for_since_archived_candidate_is_refused(
    staff_client, candidate, open_job
):
    candidate.archive()

    response = staff_client.post(
        reverse("hiring:application_create", args=[open_job.pk]),
        {"candidate": candidate.pk, "notes": ""},
    )

    assert response.status_code == 200
    assert "candidate" in response.context["form"].errors
    assert not Application.objects.exists()


def test_rejected_panel_shows_only_reopen_and_reopening_restores_stage(
    staff_client, staff_user, candidate, open_job, make_application
):
    application = make_application(candidate, open_job, stage=Stage.INTERVIEW)
    application.move_to(Stage.REJECTED, staff_user)

    response = staff_client.get(reverse("hiring:application_panel", args=[application.pk]))

    groups = {
        group["title"]: [button["label"] for button in group["buttons"]]
        for group in response.context["move_groups"]
    }
    assert groups == {"Reopen": ["Reopen to Interview"]}
    move_url = reverse("hiring:application_move", args=[application.pk])
    assert response.content.decode().count(f'hx-post="{move_url}"') == 1
    reached = [step["label"] for step in application.progress_steps if step["reached"]]
    assert reached == ["Applied", "Screening", "Interview"]

    response = move(staff_client, application, Stage.INTERVIEW)

    application.refresh_from_db()
    assert application.stage == Stage.INTERVIEW
    assert "Ada Lovelace moved from Rejected to Interview." in response.content.decode()


def test_archived_candidate_panel_shows_badge_and_unarchive_note_instead_of_reopen(
    staff_client, staff_user, candidate, open_job, make_application
):
    application = make_application(candidate, open_job, stage=Stage.SCREENING)
    application.move_to(Stage.WITHDRAWN, staff_user)
    candidate.archive()

    response = staff_client.get(
        reverse("hiring:job_detail", args=[open_job.pk]), {"application": application.pk}
    )

    assert response.context["move_groups"] == []
    panel = response.content.decode().split('id="applicant-panel"')[1]
    assert "Archived</span>" in panel
    assert "Unarchive the candidate" in panel
    assert "hx-post" not in panel


def test_stale_reopen_for_archived_candidate_is_refused_with_error_toast(
    staff_client, staff_user, candidate, open_job, make_application
):
    application = make_application(candidate, open_job, stage=Stage.SCREENING)
    application.move_to(Stage.REJECTED, staff_user)
    # The page still shows Reopen, but a colleague has since archived the candidate.
    candidate.archive()

    response = move(staff_client, application, Stage.SCREENING)

    application.refresh_from_db()
    assert response.status_code == 200
    assert application.stage == Stage.REJECTED
    toasts = response.content.decode().split('id="toasts"')[1]
    assert "alert-error" in toasts
    assert "Unarchive Ada Lovelace before reopening" in toasts


def oob_ids(content):
    """The ids of elements marked for an out-of-band swap."""
    return set(re.findall(r'<[^>]*\bid="([^"]+)"[^>]*\bhx-swap-oob="true"', content))


def test_stale_move_returns_fresh_panel_list_summary_and_error_toast(
    staff_client, staff_user, candidate, open_job, make_application
):
    application = make_application(candidate, open_job)
    # The page still shows Applied, but a colleague has since rejected the applicant.
    application.move_to(Stage.REJECTED, staff_user)

    response = staff_client.post(
        reverse("hiring:application_move", args=[application.pk]),
        {"stage": Stage.INTERVIEW},
        headers={"HX-Request": "true"},
    )

    application.refresh_from_db()
    assert response.status_code == 200
    assert application.stage == Stage.REJECTED
    assert StageChange.objects.count() == 1
    content = response.content.decode()
    assert content.lstrip().startswith('<div id="applicant-panel"')
    assert {"pipeline-list", "pipeline-summary", "toasts"} <= oob_ids(content)
    assert summary_counts(response)["rejected"] == 1
    toasts = content.split('id="toasts"')[1]
    assert "alert-error" in toasts
    assert "Ada Lovelace to Interview" in toasts


def move(client, application, stage):
    return client.post(
        reverse("hiring:application_move", args=[application.pk]),
        {"stage": stage},
        headers={"HX-Request": "true"},
    )


def test_move_updates_panel_list_and_summary_with_success_toast(
    staff_client, candidate, open_job, make_application
):
    application = make_application(candidate, open_job)

    response = move(staff_client, application, Stage.SCREENING)

    application.refresh_from_db()
    assert application.stage == Stage.SCREENING
    content = response.content.decode()
    assert content.lstrip().startswith('<div id="applicant-panel"')
    assert {"pipeline-list", "pipeline-summary", "toasts"} <= oob_ids(content)
    assert summary_counts(response)["applied"] == 0
    assert summary_counts(response)["screening"] == 1
    toasts = content.split('id="toasts"')[1]
    assert "alert-success" in toasts
    assert "Ada Lovelace moved from Applied to Screening." in toasts


def test_same_stage_move_re_renders_without_toast_or_history(
    staff_client, candidate, open_job, make_application
):
    application = make_application(candidate, open_job)

    response = move(staff_client, application, Stage.APPLIED)

    assert response.status_code == 200
    assert not StageChange.objects.exists()
    assert "toast-message" not in response.content.decode()


def test_unknown_stage_is_refused_with_error_toast(
    staff_client, candidate, open_job, make_application
):
    application = make_application(candidate, open_job)

    response = move(staff_client, application, "promoted")

    application.refresh_from_db()
    assert application.stage == Stage.APPLIED
    assert "That isn" in response.content.decode().split('id="toasts"')[1]


def test_moves_work_on_closed_jobs(staff_client, candidate, open_job, make_application):
    application = make_application(candidate, open_job, stage=Stage.OFFER)
    open_job.close()

    move(staff_client, application, Stage.HIRED)

    application.refresh_from_db()
    assert application.stage == Stage.HIRED


def test_panel_shows_only_allowed_moves_in_three_groups(
    staff_client, candidate, open_job, make_application
):
    application = make_application(candidate, open_job, stage=Stage.INTERVIEW)

    response = staff_client.get(reverse("hiring:application_panel", args=[application.pk]))

    groups = {
        group["title"]: [button["label"] for button in group["buttons"]]
        for group in response.context["move_groups"]
    }
    assert groups == {
        "Move forward": ["Advance to Final Review", "Skip to Offer"],
        "Fix a mistake": ["← Back to Screening"],
        "Close out": ["Reject", "Withdrew"],
    }
    content = response.content.decode()
    move_url = reverse("hiring:application_move", args=[application.pk])
    assert content.count(f'hx-post="{move_url}"') == 5
    assert "Hired only from Offer." in content


def test_hired_panel_offers_no_moves(staff_client, candidate, open_job, make_application):
    application = make_application(candidate, open_job, stage=Stage.HIRED)

    response = staff_client.get(reverse("hiring:application_panel", args=[application.pk]))

    assert response.context["move_groups"] == []
    content = response.content.decode()
    assert "hx-post" not in content
    assert "No moves available." in content


def test_days_in_stage_count_from_latest_stage_change(
    staff_client, candidate, open_job, make_application
):
    application = make_application(candidate, open_job, stage=Stage.SCREENING)
    Application.objects.filter(pk=application.pk).update(
        created_at=timezone.now() - timedelta(days=10)
    )
    application.stage_changes.update(changed_at=timezone.now() - timedelta(days=4))

    response = staff_client.get(reverse("hiring:job_detail", args=[open_job.pk]))

    [listed] = [a for stage in response.context["stages"] for a in stage["applications"]]
    assert listed.days_in_stage == 4
    application.refresh_from_db()
    assert application.days_in_stage == 4  # same answer without the list's annotation


def test_history_timeline_shows_each_change_with_who_made_it(
    staff_client, staff_user, candidate, open_job, make_application
):
    application = make_application(candidate, open_job, stage=Stage.SCREENING)
    application.move_to(Stage.INTERVIEW, staff_user)

    response = staff_client.get(reverse("hiring:application_panel", args=[application.pk]))

    assert [(c.from_stage, c.to_stage) for c in response.context["stage_changes"]] == [
        (Stage.SCREENING, Stage.INTERVIEW),
        (Stage.APPLIED, Stage.SCREENING),
    ]
    assert response.content.decode().count(f"{staff_user.username} · ") == 2


def test_stage_changes_protect_their_author_from_deletion(
    staff_user, candidate, open_job, make_application
):
    make_application(candidate, open_job, stage=Stage.SCREENING)

    with pytest.raises(ProtectedError):
        staff_user.delete()


def test_move_requires_post(staff_client, candidate, open_job, make_application):
    application = make_application(candidate, open_job)

    response = staff_client.get(reverse("hiring:application_move", args=[application.pk]))

    assert response.status_code == 405


def test_move_requires_login(client, candidate, open_job, make_application):
    application = make_application(candidate, open_job)

    response = move(client, application, Stage.SCREENING)

    application.refresh_from_db()
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("login"))
    assert application.stage == Stage.APPLIED


def test_candidate_page_without_applications_says_so(staff_client, candidate):
    content = staff_client.get(
        reverse("hiring:candidate_detail", args=[candidate.pk])
    ).content.decode()

    assert "No applications yet." in content
