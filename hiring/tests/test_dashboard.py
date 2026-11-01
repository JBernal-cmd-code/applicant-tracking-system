import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from hiring.models import StageChange
from hiring.stages import Stage

pytestmark = pytest.mark.django_db


def test_dashboard_shows_25_most_recent_stage_changes_newest_first(
    staff_client, staff_user, candidate, open_job, make_application
):
    application = make_application(candidate, open_job)
    for i in range(26):
        application.move_to(Stage.SCREENING if i % 2 == 0 else Stage.APPLIED, staff_user)

    response = staff_client.get(reverse("hiring:dashboard"))

    newest_25 = list(StageChange.objects.order_by("-pk").values_list("pk", flat=True)[:25])
    assert [change.pk for change in response.context["stage_changes"]] == newest_25


def test_dashboard_entry_shows_details_and_links_to_selected_applicant(
    staff_client, staff_user, candidate, open_job, make_application
):
    application = make_application(candidate, open_job, stage=Stage.FINAL_REVIEW)

    content = staff_client.get(reverse("hiring:dashboard")).content.decode()

    detail_url = reverse("hiring:job_detail", args=[open_job.pk])
    assert f'href="{detail_url}?application={application.pk}"' in content
    for text in ("Ada Lovelace", "Backend Developer", "Applied", "Final Review", "staff", "ago"):
        assert text in content


def test_dashboard_without_changes_shows_empty_state(staff_client):
    response = staff_client.get(reverse("hiring:dashboard"))

    assert b"No stage changes yet." in response.content


def test_dashboard_query_count_does_not_grow_with_rows(
    staff_client, make_candidate, make_job, make_application
):
    make_application(make_candidate(), make_job(), stage=Stage.SCREENING)
    with CaptureQueriesContext(connection) as one_row:
        staff_client.get(reverse("hiring:dashboard"))

    for _ in range(5):
        make_application(make_candidate(), make_job(), stage=Stage.INTERVIEW)
    with CaptureQueriesContext(connection) as many_rows:
        staff_client.get(reverse("hiring:dashboard"))

    assert len(many_rows) == len(one_row)
