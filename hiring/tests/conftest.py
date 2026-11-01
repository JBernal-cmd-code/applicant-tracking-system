import pytest

STAFF_PASSWORD = "correct-horse-battery"


@pytest.fixture
def staff_user(django_user_model):
    return django_user_model.objects.create_user(username="staff", password=STAFF_PASSWORD)


@pytest.fixture
def staff_client(client, staff_user):
    client.force_login(staff_user)
    return client
