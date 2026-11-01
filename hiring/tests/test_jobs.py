import pytest
from django.urls import reverse, reverse_lazy
from django.utils.formats import date_format
from django.utils.timezone import localtime

from hiring.forms import JobOpeningForm
from hiring.models import JobOpening, Skill

pytestmark = pytest.mark.django_db


def job_data(**overrides):
    data = {
        "title": "Frontend Developer",
        "department": "Engineering",
        "location": "Austin, TX",
        "employment_type": JobOpening.EmploymentType.FULL_TIME,
        "description": "Build the hiring UI.",
        "skills": [],
    }
    return data | overrides


def test_new_job_starts_open(staff_client):
    staff_client.post(reverse("hiring:job_create"), job_data())

    job = JobOpening.objects.get(title="Frontend Developer")
    assert job.status == JobOpening.Status.OPEN
    assert job.closed_at is None


def test_form_has_no_status_or_closed_at_field():
    form = JobOpeningForm()

    assert "status" not in form.fields
    assert "closed_at" not in form.fields


def test_form_offers_the_four_employment_types():
    form = JobOpeningForm()

    labels = [label for value, label in form.fields["employment_type"].choices if value]
    assert labels == ["Full-time", "Part-time", "Contract", "Internship"]


def test_form_requires_descriptive_fields_but_not_skills():
    form = JobOpeningForm(data={})

    assert not form.is_valid()
    assert set(form.errors) == {"title", "department", "location", "employment_type", "description"}


def test_form_ignores_posted_status():
    form = JobOpeningForm(data=job_data(status="closed"))

    job = form.save()

    assert job.status == JobOpening.Status.OPEN


@pytest.mark.parametrize(
    "url",
    [
        reverse_lazy("hiring:job_list"),
        reverse_lazy("hiring:job_create"),
        reverse_lazy("hiring:job_detail", args=[1]),
        reverse_lazy("hiring:job_edit", args=[1]),
    ],
)
def test_job_pages_require_login(client, url):
    response = client.get(url)

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("login"))


def test_create_job_with_skills_redirects_to_job_page_with_toast(staff_client):
    python = Skill.objects.create(name="Python")

    response = staff_client.post(
        reverse("hiring:job_create"), job_data(skills=[python.pk]), follow=True
    )

    job = JobOpening.objects.get(title="Frontend Developer")
    assert response.request["PATH_INFO"] == reverse("hiring:job_detail", args=[job.pk])
    assert list(job.skills.all()) == [python]
    assert "Job opening “Frontend Developer” added." in response.content.decode()


def test_create_with_missing_fields_shows_inline_errors(staff_client):
    response = staff_client.post(reverse("hiring:job_create"), job_data(title=""))

    assert response.status_code == 200
    assert "title" in response.context["form"].errors
    assert not JobOpening.objects.exists()


def test_edit_job_updates_details_and_skills(staff_client, make_job):
    python = Skill.objects.create(name="Python")
    sql = Skill.objects.create(name="SQL")
    job = make_job(skills=[python])

    response = staff_client.post(
        reverse("hiring:job_edit", args=[job.pk]),
        job_data(title="Senior Developer", skills=[sql.pk]),
    )

    assert response.status_code == 302
    job.refresh_from_db()
    assert job.title == "Senior Developer"
    assert list(job.skills.all()) == [sql]


def test_edit_missing_job_is_404(staff_client):
    response = staff_client.get(reverse("hiring:job_edit", args=[999]))

    assert response.status_code == 404


def test_job_page_shows_header_skills_edit_and_description(staff_client, make_job):
    python = Skill.objects.create(name="Python")
    job = make_job(
        title="Backend Developer",
        department="Platform",
        location="Denver, CO",
        employment_type=JobOpening.EmploymentType.CONTRACT,
        description="Own the hiring API.",
        skills=[python],
    )

    response = staff_client.get(reverse("hiring:job_detail", args=[job.pk]))

    content = response.content.decode()
    for text in ("Backend Developer", "Open", "Platform", "Denver, CO", "Contract", "Python"):
        assert text in content
    assert f'href="{reverse("hiring:job_edit", args=[job.pk])}"' in content
    assert "collapse" in content
    assert "Own the hiring API." in content


def test_renamed_skill_shows_on_job_page(staff_client, make_job):
    skill = Skill.objects.create(name="Pyhton")
    job = make_job(skills=[skill])

    staff_client.post(reverse("hiring:skill_edit", args=[skill.pk]), {"name": "Python"})
    response = staff_client.get(reverse("hiring:job_detail", args=[job.pk]))

    content = response.content.decode()
    assert "Python" in content
    assert "Pyhton" not in content


def test_missing_job_page_is_404(staff_client):
    response = staff_client.get(reverse("hiring:job_detail", args=[999]))

    assert response.status_code == 404


def listed(response):
    return {job.title for job in response.context["jobs"]}


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({}, {"Backend Developer"}),
        ({"status": "open"}, {"Backend Developer"}),
        ({"status": "closed"}, {"Data Analyst"}),
        ({"status": "all"}, {"Backend Developer", "Data Analyst"}),
    ],
)
def test_status_filter_defaults_to_open(staff_client, open_job, closed_job, params, expected):
    response = staff_client.get(reverse("hiring:job_list"), params)

    assert listed(response) == expected


def test_search_matches_title_or_department_ignoring_case(staff_client, make_job):
    make_job(title="Data Engineer", department="Platform")
    make_job(title="Recruiter", department="People DATA Team")
    make_job(title="Designer", department="Product")

    response = staff_client.get(reverse("hiring:job_list"), {"q": "data"})

    assert listed(response) == {"Data Engineer", "Recruiter"}


def test_job_list_form_reflects_filters_from_url(staff_client):
    response = staff_client.get(reverse("hiring:job_list"), {"q": "analyst", "status": "all"})

    content = response.content.decode()
    assert 'value="analyst"' in content
    assert '<option value="all" selected>' in content


def test_sidebar_links_to_job_list(staff_client):
    response = staff_client.get(reverse("hiring:dashboard"))

    assert f'href="{reverse("hiring:job_list")}"' in response.content.decode()


def test_no_delete_action_for_jobs(staff_client, open_job):
    for url in (
        reverse("hiring:job_list"),
        reverse("hiring:job_detail", args=[open_job.pk]),
        reverse("hiring:job_edit", args=[open_job.pk]),
    ):
        assert "delete" not in staff_client.get(url).content.decode().lower()


def test_close_marks_job_closed_once_and_keeps_first_closed_at(open_job):
    open_job.close()
    open_job.refresh_from_db()
    first_closed_at = open_job.closed_at

    assert open_job.status == JobOpening.Status.CLOSED
    assert first_closed_at is not None

    open_job.close()
    open_job.refresh_from_db()

    assert open_job.status == JobOpening.Status.CLOSED
    assert open_job.closed_at == first_closed_at


def test_reopen_marks_job_open_and_clears_closed_at(closed_job):
    closed_job.reopen()
    closed_job.refresh_from_db()

    assert closed_job.status == JobOpening.Status.OPEN
    assert closed_job.closed_at is None

    closed_job.reopen()
    closed_job.refresh_from_db()

    assert closed_job.status == JobOpening.Status.OPEN
    assert closed_job.closed_at is None


@pytest.mark.parametrize("name", ["hiring:job_close", "hiring:job_reopen"])
def test_close_and_reopen_require_login(client, open_job, name):
    response = client.post(reverse(name, args=[open_job.pk]))

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("login"))
    open_job.refresh_from_db()
    assert open_job.status == JobOpening.Status.OPEN


@pytest.mark.parametrize("name", ["hiring:job_close", "hiring:job_reopen"])
def test_close_and_reopen_refuse_get(staff_client, open_job, name):
    assert staff_client.get(reverse(name, args=[open_job.pk])).status_code == 405


def test_close_view_closes_job_and_shows_toast(staff_client, open_job):
    response = staff_client.post(reverse("hiring:job_close", args=[open_job.pk]), follow=True)

    open_job.refresh_from_db()
    assert open_job.status == JobOpening.Status.CLOSED
    assert response.request["PATH_INFO"] == reverse("hiring:job_detail", args=[open_job.pk])
    assert "Job opening “Backend Developer” closed." in response.content.decode()


def test_htmx_close_asks_client_to_reload_job_page(staff_client, open_job):
    response = staff_client.post(
        reverse("hiring:job_close", args=[open_job.pk]), headers={"HX-Request": "true"}
    )

    assert response["HX-Redirect"] == reverse("hiring:job_detail", args=[open_job.pk])
    open_job.refresh_from_db()
    assert open_job.status == JobOpening.Status.CLOSED


def test_reopen_view_reopens_job_and_shows_toast(staff_client, closed_job):
    response = staff_client.post(reverse("hiring:job_reopen", args=[closed_job.pk]), follow=True)

    closed_job.refresh_from_db()
    assert closed_job.status == JobOpening.Status.OPEN
    assert "Job opening “Data Analyst” reopened." in response.content.decode()


def test_open_job_header_offers_confirmed_close(staff_client, open_job):
    content = staff_client.get(reverse("hiring:job_detail", args=[open_job.pk])).content.decode()

    assert f'hx-post="{reverse("hiring:job_close", args=[open_job.pk])}"' in content
    assert "hx-confirm=" in content
    assert reverse("hiring:job_reopen", args=[open_job.pk]) not in content
    assert "Closed on" not in content


def test_closed_job_header_shows_closed_date_and_reopen(staff_client, closed_job):
    content = staff_client.get(reverse("hiring:job_detail", args=[closed_job.pk])).content.decode()

    assert f"Closed on {date_format(localtime(closed_job.closed_at), 'M j, Y')}" in content
    assert f'action="{reverse("hiring:job_reopen", args=[closed_job.pk])}"' in content
    assert reverse("hiring:job_close", args=[closed_job.pk]) not in content


def test_job_list_rows_offer_close_or_reopen(staff_client, open_job, closed_job):
    content = staff_client.get(reverse("hiring:job_list"), {"status": "all"}).content.decode()

    assert f'hx-post="{reverse("hiring:job_close", args=[open_job.pk])}"' in content
    assert f'action="{reverse("hiring:job_reopen", args=[closed_job.pk])}"' in content
    assert reverse("hiring:job_reopen", args=[open_job.pk]) not in content
    assert reverse("hiring:job_close", args=[closed_job.pk]) not in content


def test_job_list_close_button_asks_for_confirmation(staff_client, open_job):
    content = staff_client.get(reverse("hiring:job_list")).content.decode()

    assert "hx-confirm=" in content


def test_edit_form_points_to_close_button_on_job_page(staff_client, open_job):
    content = staff_client.get(reverse("hiring:job_edit", args=[open_job.pk])).content.decode()

    assert "use the Close button on the" in content
    assert f'href="{reverse("hiring:job_detail", args=[open_job.pk])}"' in content


def test_closing_a_job_drops_it_from_the_sidebar(staff_client, open_job):
    staff_client.post(reverse("hiring:job_close", args=[open_job.pk]))

    content = staff_client.get(reverse("hiring:skill_list")).content.decode()
    assert f'href="{reverse("hiring:job_detail", args=[open_job.pk])}"' not in content


def test_sidebar_lists_open_jobs_on_every_page(staff_client, open_job, closed_job):
    response = staff_client.get(reverse("hiring:skill_list"))

    content = response.content.decode()
    assert f'href="{reverse("hiring:job_detail", args=[open_job.pk])}"' in content
    assert open_job.title in content
    assert closed_job.title not in content
