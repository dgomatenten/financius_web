import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db) -> User:
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpassword123",
    )


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def auth_client(api_client, user) -> tuple:
    api_client.force_authenticate(user=user)
    return api_client, user
