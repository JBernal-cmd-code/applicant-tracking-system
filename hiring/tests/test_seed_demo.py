import pytest
from django.core.management import CommandError, call_command

from hiring.models import Application, Candidate, JobOpening, Skill, StageChange
from hiring.stages import Stage

pytestmark = pytest.mark.django_db


def snapshot():
    """Everything the demo data defines, without pks or timestamps that differ between runs."""
    return {
        "skills": sorted(Skill.objects.values_list("name", flat=True)),
        "jobs": sorted(JobOpening.objects.values_list("title", "status")),
        "candidates": sorted(Candidate.objects.values_list("email", "source", "archived")),
        "applications": sorted(
            (
                a.candidate.email,
                a.job.title,
                a.stage,
                tuple((c.from_stage, c.to_stage) for c in a.stage_changes.order_by("pk")),
            )
            for a in Application.objects.select_related("candidate", "job")
        ),
        "changed_by": set(StageChange.objects.values_list("changed_by__username", flat=True)),
    }


def test_reset_twice_gives_the_same_result():
    call_command("seed_demo", "--reset")
    first = snapshot()

    call_command("seed_demo", "--reset")

    assert snapshot() == first
    assert first["applications"]


def test_reset_replaces_existing_data(make_candidate):
    make_candidate(email="not-demo@example.com")

    call_command("seed_demo", "--reset")

    assert not Candidate.objects.filter(email="not-demo@example.com").exists()


def test_refuses_to_seed_over_existing_data_without_reset(candidate):
    with pytest.raises(CommandError):
        call_command("seed_demo")


def test_covers_every_stage_a_closed_job_and_an_archived_candidate():
    call_command("seed_demo")

    assert set(Application.objects.values_list("stage", flat=True)) == set(Stage)
    assert JobOpening.objects.filter(status=JobOpening.Status.CLOSED).count() == 1
    assert Candidate.objects.filter(archived=True).count() == 1
    assert set(Candidate.objects.values_list("source", flat=True)) == set(Candidate.Source)
    assert 3 <= JobOpening.objects.count() <= 4
    assert Candidate.objects.count() >= 18


def test_history_forms_an_unbroken_chain_ending_at_the_current_stage():
    call_command("seed_demo")

    for application in Application.objects.all():
        stages = [Stage.APPLIED]
        for change in application.stage_changes.order_by("pk"):
            assert change.from_stage == stages[-1]
            stages.append(change.to_stage)
        assert stages[-1] == application.stage


def test_history_is_by_first_superuser_when_one_exists(django_user_model):
    django_user_model.objects.create_user(username="regular")
    admin = django_user_model.objects.create_superuser(username="boss", password="x")

    call_command("seed_demo")

    assert set(StageChange.objects.values_list("changed_by", flat=True)) == {admin.pk}


def test_history_is_by_demo_user_without_a_superuser(django_user_model):
    call_command("seed_demo")

    demo = django_user_model.objects.get(username="demo")
    assert not demo.has_usable_password()
    assert set(StageChange.objects.values_list("changed_by", flat=True)) == {demo.pk}
