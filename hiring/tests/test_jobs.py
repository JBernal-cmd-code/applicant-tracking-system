import pytest
from django.urls import reverse, reverse_lazy

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


def test_list_shows_open_and_closed_jobs(staff_client, open_job, closed_job):
    response = staff_client.get(reverse("hiring:job_list"))

    assert set(response.context["jobs"]) == {open_job, closed_job}


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


def test_sidebar_lists_open_jobs_on_every_page(staff_client, open_job, closed_job):
    response = staff_client.get(reverse("hiring:skill_list"))

    content = response.content.decode()
    assert f'href="{reverse("hiring:job_detail", args=[open_job.pk])}"' in content
    assert open_job.title in content
    assert closed_job.title not in content
