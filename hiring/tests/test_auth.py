import pytest
from django.urls import reverse

from hiring.tests.conftest import STAFF_PASSWORD

pytestmark = pytest.mark.django_db


def test_anonymous_dashboard_redirects_to_login(client):
    response = client.get(reverse("hiring:dashboard"))

    assert response.status_code == 302
    assert response["Location"] == f"{reverse('login')}?next=/"


def test_login_lands_on_dashboard(client, staff_user):
    response = client.post(
        reverse("login"),
        {"username": staff_user.username, "password": STAFF_PASSWORD},
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("hiring:dashboard")


def test_logout_post_ends_session(staff_client):
    staff_client.post(reverse("logout"))

    response = staff_client.get(reverse("hiring:dashboard"))

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("login"))
