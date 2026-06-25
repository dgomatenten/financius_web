"""
Contract test fixtures.

A "contract" is a named (method, path, body) tuple that must produce an identical
response shape from both the Flask stack and the Django stack.

During migration, contract tests run against Flask (to establish ground truth) and
will also run against Django as each endpoint is ported. Once all contracts pass
on Django, Flask can be retired.
"""
import os
from importlib.util import find_spec
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from flask.testing import FlaskClient


@pytest.fixture(scope="session")
def flask_client() -> "FlaskClient":
    if find_spec("app") is None:
        pytest.skip("Legacy Flask app module is unavailable in this workspace")

    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    from app import create_app as create_flask_app
    app = create_flask_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def assert_envelope(body: dict) -> None:
    """Assert the response uses the standard { data, error, meta } envelope."""
    assert "data" in body, f"missing 'data' key in response: {body}"
    assert "error" in body, f"missing 'error' key in response: {body}"
    assert "meta" in body, f"missing 'meta' key in response: {body}"


@pytest.fixture
def django_client(db):
    """Unauthenticated DRF test client for contract tests."""
    from rest_framework.test import APIClient
    return APIClient()


def assert_shapes_match(flask_body: dict, django_body: dict) -> None:
    """Assert that top-level keys and error/data presence match between stacks."""
    assert set(flask_body.keys()) == set(django_body.keys()), (
        f"key mismatch — flask: {set(flask_body.keys())}, django: {set(django_body.keys())}"
    )
    assert (flask_body["error"] is None) == (django_body["error"] is None), (
        "error presence mismatch between Flask and Django responses"
    )
