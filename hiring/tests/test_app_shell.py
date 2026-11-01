import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import reverse

from hiring.tests.conftest import STAFF_PASSWORD

pytestmark = pytest.mark.django_db


def test_sidebar_shows_main_links_and_current_user(staff_client, staff_user):
    response = staff_client.get(reverse("hiring:dashboard"))

    content = response.content.decode()
    for label in ("Dashboard", "Candidates", "Job openings", "Skills"):
        assert label in content
    assert staff_user.username in content
    assert f'action="{reverse("logout")}"' in content


def test_logout_get_is_refused(staff_client):
    response = staff_client.get(reverse("logout"))

    assert response.status_code == 405


def test_login_message_is_shown_as_toast(client, staff_user):
    response = client.post(
        reverse("login"),
        {"username": staff_user.username, "password": STAFF_PASSWORD},
        follow=True,
    )

    assert response.request["PATH_INFO"] == reverse("hiring:dashboard")
    assert b'id="toasts"' in response.content
    assert b"toast-message" in response.content
    assert b"Welcome back, staff." in response.content


def test_admin_manages_users_but_no_hiring_models():
    registered = admin.site._registry

    assert User in registered
    assert not [model for model in registered if model._meta.app_label == "hiring"]
