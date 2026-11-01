import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse

from hiring.forms import CandidateForm
from hiring.models import Candidate
from hiring.stages import Stage

pytestmark = pytest.mark.django_db


def test_archive_is_refused_while_candidate_has_active_applications(
    candidate, make_job, make_application, staff_user
):
    backend = make_application(
        candidate, make_job(title="Backend Developer"), stage=Stage.INTERVIEW
    )
    make_application(candidate, make_job(title="Data Analyst"), stage=Stage.REJECTED)
    qa = make_application(candidate, make_job(title="QA Engineer"))

    with pytest.raises(ValidationError) as excinfo:
        candidate.archive()

    message = excinfo.value.messages[0]
    assert "Backend Developer" in message
    assert "QA Engineer" in message
    assert "Data Analyst" not in message
    candidate.refresh_from_db()
    assert not candidate.archived

    # Once every application is finished, archiving goes through.
    backend.move_to(Stage.WITHDRAWN, staff_user)
    qa.move_to(Stage.REJECTED, staff_user)
    candidate.archive()

    candidate.refresh_from_db()
    assert candidate.archived


def listed(response):
    return {c.email for c in response.context["candidates"]}


def candidate_data(**overrides):
    data = {
        "first_name": "Grace",
        "last_name": "Hopper",
        "email": "grace@example.com",
        "phone": "",
        "source": Candidate.Source.REFERRAL,
        "source_details": "",
        "resume_url": "",
    }
    return data | overrides


def test_database_rejects_case_insensitive_duplicate_email(candidate, make_candidate):
    with pytest.raises(IntegrityError):
        make_candidate(email=candidate.email.upper())


def test_form_shows_duplicate_email_error_on_email_field(candidate):
    form = CandidateForm(data=candidate_data(email="ADA@Example.com"))

    assert not form.is_valid()
    assert form.errors == {"email": ["A candidate with this email already exists."]}


def test_source_filter_shows_only_that_source(staff_client, make_candidate):
    make_candidate(email="ref@example.com", source=Candidate.Source.REFERRAL)
    make_candidate(email="web@example.com", source=Candidate.Source.WEBSITE)

    response = staff_client.get(reverse("hiring:candidate_list"), {"source": "referral"})

    assert listed(response) == {"ref@example.com"}


def test_search_matches_first_name_last_name_or_email_ignoring_case(staff_client, make_candidate):
    make_candidate(first_name="Grace", last_name="Hopper", email="grace@example.com")
    make_candidate(first_name="Alan", last_name="Gracey", email="alan@example.com")
    make_candidate(first_name="Linus", last_name="Torvalds", email="lt.GRACE@example.org")
    make_candidate(first_name="Ada", last_name="Lovelace", email="ada@example.com")

    response = staff_client.get(reverse("hiring:candidate_list"), {"q": "gRaCe"})

    assert listed(response) == {"grace@example.com", "alan@example.com", "lt.GRACE@example.org"}


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({}, {"active@example.com"}),
        ({"status": "active"}, {"active@example.com"}),
        ({"status": "archived"}, {"archived@example.com"}),
        ({"status": "all"}, {"active@example.com", "archived@example.com"}),
    ],
)
def test_status_filter_defaults_to_active(staff_client, make_candidate, params, expected):
    make_candidate(email="active@example.com")
    make_candidate(email="archived@example.com", archived=True)

    response = staff_client.get(reverse("hiring:candidate_list"), params)

    assert listed(response) == expected


def test_form_allows_keeping_own_email_in_different_case(candidate):
    form = CandidateForm(data=candidate_data(email="ADA@example.com"), instance=candidate)

    assert form.is_valid()


def test_form_excludes_archived_flag():
    assert "archived" not in CandidateForm().fields


def test_form_requires_a_valid_source():
    form = CandidateForm(data=candidate_data(source="newspaper"))

    assert not form.is_valid()
    assert list(form.errors) == ["source"]


@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("hiring:candidate_list", []),
        ("hiring:candidate_create", []),
        ("hiring:candidate_detail", [1]),
        ("hiring:candidate_edit", [1]),
    ],
)
def test_candidate_pages_require_login(client, name, args):
    response = client.get(reverse(name, args=args))

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("login"))


def test_create_candidate_redirects_to_detail_with_toast(staff_client):
    response = staff_client.post(
        reverse("hiring:candidate_create"),
        candidate_data(source_details="Met at PyCon"),
        follow=True,
    )

    candidate = Candidate.objects.get(email="grace@example.com")
    assert response.request["PATH_INFO"] == reverse("hiring:candidate_detail", args=[candidate.pk])
    content = response.content.decode()
    assert "Candidate “Grace Hopper” added." in content
    assert "Met at PyCon" in content
    assert not candidate.archived


def test_create_duplicate_email_shows_inline_error(staff_client, candidate):
    response = staff_client.post(
        reverse("hiring:candidate_create"), candidate_data(email="Ada@Example.com")
    )

    assert response.status_code == 200
    assert "A candidate with this email already exists." in response.content.decode()
    assert Candidate.objects.count() == 1


def test_edit_candidate_updates_details(staff_client, candidate):
    response = staff_client.post(
        reverse("hiring:candidate_edit", args=[candidate.pk]),
        candidate_data(email=candidate.email, phone="555-0100"),
    )

    assert response.status_code == 302
    candidate.refresh_from_db()
    assert (candidate.first_name, candidate.phone) == ("Grace", "555-0100")


def test_edit_archived_candidate_keeps_archived_flag(staff_client, make_candidate):
    archived = make_candidate(email="old@example.com", archived=True)

    staff_client.post(
        reverse("hiring:candidate_edit", args=[archived.pk]), candidate_data(email=archived.email)
    )

    archived.refresh_from_db()
    assert archived.archived
    assert archived.first_name == "Grace"


def test_missing_candidate_is_404(staff_client):
    assert staff_client.get(reverse("hiring:candidate_detail", args=[999])).status_code == 404


def test_list_form_reflects_filters_from_url(staff_client):
    response = staff_client.get(
        reverse("hiring:candidate_list"), {"q": "hopper", "source": "referral", "status": "all"}
    )

    content = response.content.decode()
    assert 'value="hopper"' in content
    assert '<option value="referral" selected>' in content
    assert '<option value="all" selected>' in content


def test_sidebar_links_to_candidates(staff_client):
    response = staff_client.get(reverse("hiring:dashboard"))

    assert f'href="{reverse("hiring:candidate_list")}"' in response.content.decode()


def test_no_delete_action_for_candidates(staff_client, candidate):
    for url in (
        reverse("hiring:candidate_list"),
        reverse("hiring:candidate_detail", args=[candidate.pk]),
        reverse("hiring:candidate_edit", args=[candidate.pk]),
    ):
        assert "delete" not in staff_client.get(url).content.decode().lower()


def test_archive_from_detail_page_hides_candidate_from_default_list(staff_client, candidate):
    response = staff_client.post(
        reverse("hiring:candidate_archive", args=[candidate.pk]), headers={"HX-Request": "true"}
    )

    detail_url = reverse("hiring:candidate_detail", args=[candidate.pk])
    assert response["HX-Redirect"] == detail_url
    candidate.refresh_from_db()
    assert candidate.archived
    content = staff_client.get(detail_url).content.decode()
    assert "Candidate “Ada Lovelace” archived." in content
    assert reverse("hiring:candidate_unarchive", args=[candidate.pk]) in content
    assert listed(staff_client.get(reverse("hiring:candidate_list"))) == set()


def test_archive_button_asks_for_confirmation(staff_client, candidate):
    content = staff_client.get(
        reverse("hiring:candidate_detail", args=[candidate.pk])
    ).content.decode()

    assert f'hx-post="{reverse("hiring:candidate_archive", args=[candidate.pk])}"' in content
    assert "hx-confirm=" in content


def test_refused_archive_shows_error_toast_listing_active_applications(
    staff_client, candidate, open_job, make_application
):
    make_application(candidate, open_job, stage=Stage.SCREENING)

    response = staff_client.post(
        reverse("hiring:candidate_archive", args=[candidate.pk]), follow=True
    )

    candidate.refresh_from_db()
    assert not candidate.archived
    content = response.content.decode()
    assert "alert-error" in content
    assert "Backend Developer (Screening)" in content


def test_archiving_an_archived_candidate_changes_nothing(make_candidate):
    archived = make_candidate(archived=True)

    archived.archive()

    archived.refresh_from_db()
    assert archived.archived


def test_unarchive_restores_candidate_to_default_list(staff_client, make_candidate):
    archived = make_candidate(email="back@example.com", archived=True)

    response = staff_client.post(
        reverse("hiring:candidate_unarchive", args=[archived.pk]), follow=True
    )

    archived.refresh_from_db()
    assert not archived.archived
    assert "Candidate “First1 Last1” unarchived." in response.content.decode()
    assert listed(staff_client.get(reverse("hiring:candidate_list"))) == {"back@example.com"}


@pytest.mark.parametrize("name", ["hiring:candidate_archive", "hiring:candidate_unarchive"])
def test_archive_actions_require_post_and_login(client, staff_client, candidate, name):
    url = reverse(name, args=[candidate.pk])

    assert staff_client.get(url).status_code == 405
    client.logout()
    response = client.post(url)
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("login"))


def test_list_rows_link_to_detail_and_edit(staff_client, candidate):
    content = staff_client.get(reverse("hiring:candidate_list")).content.decode()

    assert f'href="{reverse("hiring:candidate_detail", args=[candidate.pk])}"' in content
    assert f'href="{reverse("hiring:candidate_edit", args=[candidate.pk])}"' in content
