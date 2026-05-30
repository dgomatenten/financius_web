from datetime import datetime, timedelta, timezone

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from ledger.models import (
    AmortizationRule,
    Budget,
    Category,
    PairingToken,
    RecurringExpenseOccurrence,
    RecurringExpenseTemplate,
    SyncEvent,
)

User = get_user_model()

NOW = datetime(2024, 6, 1, tzinfo=timezone.utc)


# ── Budget ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBudgetModel:
    def test_create_budget(self, user: User) -> None:
        b = Budget.objects.create(user=user, year_month="2024-06", mode="fixed", amount=500)
        assert b.pk is not None
        assert b.rollover_enabled is False
        assert b.category is None

    def test_budget_with_category(self, user: User) -> None:
        cat = Category.objects.create(user=user, name="Food")
        b = Budget.objects.create(user=user, year_month="2024-06", mode="fixed", amount=300, category=cat)
        assert b.category == cat

    def test_unique_constraint(self, user: User) -> None:
        # Constraint is (user, year_month, category) — NULL category won't collide (SQL NULL != NULL).
        cat = Category.objects.create(user=user, name="Food")
        Budget.objects.create(user=user, year_month="2024-06", mode="fixed", amount=500, category=cat)
        with pytest.raises(IntegrityError):
            Budget.objects.create(user=user, year_month="2024-06", mode="fixed", amount=200, category=cat)

    def test_db_table(self) -> None:
        assert Budget._meta.db_table == "budgets"

    def test_str(self, user: User) -> None:
        b = Budget.objects.create(user=user, year_month="2024-06", mode="fixed", amount=500)
        assert "2024-06" in str(b)


# ── PairingToken ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPairingTokenModel:
    def test_create_token(self, user: User) -> None:
        pt = PairingToken.objects.create(
            user=user, token_hash="abc123", expires_at=NOW + timedelta(minutes=5)
        )
        assert pt.pk is not None
        assert pt.consumed_at is None

    def test_token_hash_unique(self, user: User) -> None:
        PairingToken.objects.create(user=user, token_hash="hash1", expires_at=NOW + timedelta(minutes=5))
        with pytest.raises(IntegrityError):
            PairingToken.objects.create(user=user, token_hash="hash1", expires_at=NOW + timedelta(minutes=5))

    def test_consumed_at_nullable(self, user: User) -> None:
        pt = PairingToken.objects.create(user=user, token_hash="h2", expires_at=NOW)
        pt.consumed_at = NOW
        pt.save()
        assert PairingToken.objects.get(pk=pt.pk).consumed_at == NOW

    def test_cascade_on_user_delete(self, user: User) -> None:
        PairingToken.objects.create(user=user, token_hash="h3", expires_at=NOW)
        user.delete()
        assert PairingToken.objects.count() == 0

    def test_db_table(self) -> None:
        assert PairingToken._meta.db_table == "pairing_tokens"


# ── SyncEvent ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSyncEventModel:
    def test_create_sync_event(self, user: User) -> None:
        ev = SyncEvent.objects.create(
            user=user, device_id="android-abc", sync_started_at=NOW
        )
        assert ev.pk is not None
        assert ev.status == "success"
        assert ev.receipts_count == 0
        assert ev.error_message is None

    def test_count_fields(self, user: User) -> None:
        ev = SyncEvent.objects.create(
            user=user, device_id="dev-1", sync_started_at=NOW,
            receipts_count=5, categories_count=2, shops_count=1
        )
        assert ev.receipts_count == 5
        assert ev.categories_count == 2

    def test_error_status(self, user: User) -> None:
        ev = SyncEvent.objects.create(
            user=user, device_id="dev-1", sync_started_at=NOW,
            status="error", error_message="Payload too large"
        )
        assert ev.status == "error"
        assert ev.error_message == "Payload too large"

    def test_db_table(self) -> None:
        assert SyncEvent._meta.db_table == "sync_events"


# ── RecurringExpenseTemplate + Occurrence ─────────────────────────────────────

@pytest.mark.django_db
class TestRecurringModels:
    def test_create_template(self, user: User) -> None:
        t = RecurringExpenseTemplate.objects.create(
            user=user, name="Rent", expected_amount=1500, frequency="monthly", start_date=NOW
        )
        assert t.pk is not None
        assert t.frequency == "monthly"

    def test_create_occurrence(self, user: User) -> None:
        t = RecurringExpenseTemplate.objects.create(
            user=user, name="Rent", expected_amount=1500, frequency="monthly", start_date=NOW
        )
        occ = RecurringExpenseOccurrence.objects.create(
            template=t, due_date=NOW + timedelta(days=30), status="upcoming"
        )
        assert occ.pk is not None
        assert occ.status == "upcoming"
        assert t.occurrences.first() == occ

    def test_cascade_on_template_delete(self, user: User) -> None:
        t = RecurringExpenseTemplate.objects.create(
            user=user, name="Rent", expected_amount=1500, frequency="monthly", start_date=NOW
        )
        RecurringExpenseOccurrence.objects.create(template=t, due_date=NOW, status="upcoming")
        t.delete()
        assert RecurringExpenseOccurrence.objects.count() == 0

    def test_db_tables(self) -> None:
        assert RecurringExpenseTemplate._meta.db_table == "recurring_expense_templates"
        assert RecurringExpenseOccurrence._meta.db_table == "recurring_expense_occurrences"

    def test_str(self, user: User) -> None:
        t = RecurringExpenseTemplate.objects.create(
            user=user, name="Rent", expected_amount=1500, frequency="monthly", start_date=NOW
        )
        assert "Rent" in str(t)


# ── AmortizationRule ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAmortizationRuleModel:
    def test_create_rule(self, user: User) -> None:
        rule = AmortizationRule.objects.create(
            user=user, title="Laptop", total_amount=1200, months=12, monthly_amount=100
        )
        assert rule.pk is not None
        assert rule.status == "active"
        assert rule.monthly_amount == 100

    def test_db_table(self) -> None:
        assert AmortizationRule._meta.db_table == "amortization_rules"

    def test_str(self, user: User) -> None:
        rule = AmortizationRule.objects.create(
            user=user, title="Laptop", total_amount=1200, months=12, monthly_amount=100
        )
        assert "Laptop" in str(rule)
