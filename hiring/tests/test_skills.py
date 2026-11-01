import pytest
from django.db import IntegrityError, connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse, reverse_lazy

from hiring.forms import SkillForm
from hiring.models import Skill

pytestmark = pytest.mark.django_db


def test_database_rejects_case_insensitive_duplicate_name():
    Skill.objects.create(name="Python")

    with pytest.raises(IntegrityError):
        Skill.objects.create(name="python")


def test_form_shows_duplicate_name_error_on_name_field():
    Skill.objects.create(name="Python")

    form = SkillForm(data={"name": "python"})

    assert not form.is_valid()
    assert form.errors == {"name": ["A skill with this name already exists."]}


def test_form_allows_changing_the_case_of_an_existing_skill():
    skill = Skill.objects.create(name="python")

    form = SkillForm(data={"name": "Python"}, instance=skill)

    assert form.is_valid()


@pytest.mark.parametrize(
    "url",
    [
        reverse_lazy("hiring:skill_list"),
        reverse_lazy("hiring:skill_create"),
        reverse_lazy("hiring:skill_edit", args=[1]),
    ],
)
def test_skill_pages_require_login(client, url):
    response = client.get(url)

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("login"))


def test_list_shows_skills_with_job_counts(staff_client):
    Skill.objects.create(name="SQL")
    Skill.objects.create(name="Python")

    response = staff_client.get(reverse("hiring:skill_list"))

    assert [(s.name, s.job_count) for s in response.context["skills"]] == [
        ("Python", 0),
        ("SQL", 0),
    ]


def test_list_query_count_does_not_grow_with_skills(staff_client):
    Skill.objects.create(name="Python")
    with CaptureQueriesContext(connection) as one_skill:
        staff_client.get(reverse("hiring:skill_list"))

    for name in ("SQL", "Django", "HTMX", "Docker"):
        Skill.objects.create(name=name)
    with CaptureQueriesContext(connection) as five_skills:
        staff_client.get(reverse("hiring:skill_list"))

    assert len(five_skills) == len(one_skill)


def test_create_skill_redirects_to_list_with_toast(staff_client):
    response = staff_client.post(reverse("hiring:skill_create"), {"name": "Django"}, follow=True)

    assert response.request["PATH_INFO"] == reverse("hiring:skill_list")
    assert Skill.objects.filter(name="Django").exists()
    assert "Skill “Django” added." in response.content.decode()


def test_create_duplicate_shows_inline_error(staff_client):
    Skill.objects.create(name="Python")

    response = staff_client.post(reverse("hiring:skill_create"), {"name": "python"})

    assert response.status_code == 200
    assert response.context["form"].errors == {"name": ["A skill with this name already exists."]}
    assert "A skill with this name already exists." in response.content.decode()
    assert Skill.objects.count() == 1


def test_edit_skill_renames_it(staff_client):
    skill = Skill.objects.create(name="Pyhton")

    response = staff_client.post(reverse("hiring:skill_edit", args=[skill.pk]), {"name": "Python"})

    assert response.status_code == 302
    skill.refresh_from_db()
    assert skill.name == "Python"


def test_edit_missing_skill_is_404(staff_client):
    response = staff_client.get(reverse("hiring:skill_edit", args=[999]))

    assert response.status_code == 404


def test_sidebar_links_to_skills(staff_client):
    response = staff_client.get(reverse("hiring:dashboard"))

    assert f'href="{reverse("hiring:skill_list")}"' in response.content.decode()


def test_no_delete_action_for_skills(staff_client):
    skill = Skill.objects.create(name="Python")

    for url in (reverse("hiring:skill_list"), reverse("hiring:skill_edit", args=[skill.pk])):
        assert "delete" not in staff_client.get(url).content.decode().lower()
