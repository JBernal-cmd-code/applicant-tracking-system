import itertools

import pytest

from hiring.models import Candidate, JobOpening

STAFF_PASSWORD = "correct-horse-battery"


@pytest.fixture
def staff_user(django_user_model):
    return django_user_model.objects.create_user(username="staff", password=STAFF_PASSWORD)


@pytest.fixture
def staff_client(client, staff_user):
    client.force_login(staff_user)
    return client


@pytest.fixture
def make_candidate(db):
    counter = itertools.count(1)

    def make(**fields):
        n = next(counter)
        fields.setdefault("first_name", f"First{n}")
        fields.setdefault("last_name", f"Last{n}")
        fields.setdefault("email", f"candidate{n}@example.com")
        fields.setdefault("source", Candidate.Source.WEBSITE)
        return Candidate.objects.create(**fields)

    return make


@pytest.fixture
def candidate(make_candidate):
    return make_candidate(first_name="Ada", last_name="Lovelace", email="ada@example.com")


@pytest.fixture
def make_job(db):
    counter = itertools.count(1)

    def make(skills=(), **fields):
        n = next(counter)
        fields.setdefault("title", f"Job {n}")
        fields.setdefault("department", "Engineering")
        fields.setdefault("location", "Remote")
        fields.setdefault("employment_type", JobOpening.EmploymentType.FULL_TIME)
        fields.setdefault("description", f"Description for job {n}.")
        job = JobOpening.objects.create(**fields)
        job.skills.set(skills)
        return job

    return make


@pytest.fixture
def open_job(make_job):
    return make_job(title="Backend Developer")


@pytest.fixture
def closed_job(make_job):
    job = make_job(title="Data Analyst")
    job.close()
    return job
