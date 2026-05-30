"""
Envelope contract tests.

Each Flask baseline test establishes ground truth for the { data, error, meta }
envelope shape. The matching Django test verifies the ported endpoint returns
the same envelope structure so Android Retrofit clients are unaffected by the
migration.

Run: pytest tests/dj/contract/ -v
"""
import pytest

from tests.dj.contract.conftest import assert_envelope, assert_shapes_match


# ── Flask envelope baseline ──────────────────────────────────────────────────

class TestFlaskEnvelopeBaseline:
    """
    Verify Flask returns the standard envelope on every tested route.
    These must always pass — if they fail, something broke in Flask.
    """

    def test_health_envelope(self, flask_client) -> None:
        r = flask_client.get("/api/v1/health")
        assert r.status_code == 200
        assert_envelope(r.get_json())

    def test_auth_login_wrong_credentials_envelope(self, flask_client) -> None:
        r = flask_client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "wrong"},
        )
        body = r.get_json()
        assert_envelope(body)
        assert body["data"] is None
        assert body["error"] is not None

    def test_receipts_requires_auth_envelope(self, flask_client) -> None:
        r = flask_client.get("/api/v1/receipts")
        body = r.get_json()
        assert_envelope(body)
        assert body["error"] is not None

    def test_categories_requires_auth_envelope(self, flask_client) -> None:
        r = flask_client.get("/api/v1/master-data/categories")
        body = r.get_json()
        assert_envelope(body)
        assert body["error"] is not None

    def test_budgets_requires_auth_envelope(self, flask_client) -> None:
        r = flask_client.get("/api/v1/budgets")
        body = r.get_json()
        assert_envelope(body)
        assert body["error"] is not None


# ── Django contract tests ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDjangoEnvelopeContract:
    """
    Each test mirrors a Flask baseline above.
    Both stacks must return the same envelope shape so Android clients
    can switch URLs without any client-side changes.
    """

    def test_health_matches_flask(self, flask_client, django_client) -> None:
        flask_body = flask_client.get("/api/v1/health").get_json()
        django_resp = django_client.get("/api/v1/health/")
        django_body = django_resp.json()
        assert_envelope(django_body)
        assert flask_body["data"]["status"] == django_body["data"]["status"]

    def test_auth_login_wrong_credentials_matches_flask(self, flask_client, django_client) -> None:
        flask_body = flask_client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "wrong"},
        ).get_json()
        django_body = django_client.post(
            "/api/v1/auth/login",
            {"email": "nobody@example.com", "password": "wrong"},
            format="json",
        ).json()
        assert_envelope(django_body)
        assert_shapes_match(flask_body, django_body)
        assert django_body["data"] is None
        assert django_body["error"] is not None

    def test_receipts_auth_error_matches_flask(self, flask_client, django_client) -> None:
        flask_body = flask_client.get("/api/v1/receipts").get_json()
        django_body = django_client.get("/api/v1/receipts/").json()
        assert_envelope(django_body)
        assert_shapes_match(flask_body, django_body)
        assert django_body["error"] is not None

    def test_categories_auth_error_matches_flask(self, flask_client, django_client) -> None:
        flask_body = flask_client.get("/api/v1/master-data/categories").get_json()
        django_body = django_client.get("/api/v1/master-data/categories/").json()
        assert_envelope(django_body)
        assert_shapes_match(flask_body, django_body)
        assert django_body["error"] is not None

    def test_budgets_auth_error_matches_flask(self, flask_client, django_client) -> None:
        flask_body = flask_client.get("/api/v1/budgets").get_json()
        django_body = django_client.get("/api/v1/budgets/").json()
        assert_envelope(django_body)
        assert_shapes_match(flask_body, django_body)
        assert django_body["error"] is not None

    def test_auth_register_returns_envelope(self, django_client) -> None:
        body = django_client.post(
            "/api/v1/auth/register",
            {"email": "contract@example.com", "password": "pass1234"},
            format="json",
        ).json()
        assert_envelope(body)
        assert body["error"] is None
        assert "accessToken" in body["data"]
        assert "refreshToken" in body["data"]
        assert body["data"]["user"]["email"] == "contract@example.com"

    def test_sync_auth_error_returns_envelope(self, django_client) -> None:
        body = django_client.post("/api/v1/sync/", {}, format="json").json()
        assert_envelope(body)
        assert body["error"] is not None

    def test_master_data_shops_auth_error_returns_envelope(self, django_client) -> None:
        body = django_client.get("/api/v1/master-data/shops/").json()
        assert_envelope(body)
        assert body["error"] is not None

    def test_analytics_summary_auth_error_returns_envelope(self, django_client) -> None:
        body = django_client.get("/api/v1/analytics/summary/").json()
        assert_envelope(body)
        assert body["error"] is not None
