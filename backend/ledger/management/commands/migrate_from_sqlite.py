"""
Management command: migrate_from_sqlite

Copies all rows from a Flask/SQLAlchemy SQLite database into the Django
target database (SQLite dev or PostgreSQL prod).

Flask schema difference: users.id is the user's email (VARCHAR), not a UUID.
All child tables reference users via user_id = email.  This command builds an
email → Django-UUID mapping during user migration and uses it to translate all
user_id FK values before inserting child rows.

Idempotent — safe to run multiple times.  Users are matched by email
(update_or_create), child rows via bulk_create(ignore_conflicts=True).

Usage:
    python3 manage.py migrate_from_sqlite --sqlite-path /path/to/financius.db
    python3 manage.py migrate_from_sqlite --sqlite-path /path/to/financius.db --dry-run
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.hashers import wrap_werkzeug_hash
from accounts.models import RefreshToken
from ledger.models import (
    AmortizationRule,
    Budget,
    Category,
    CategoryMapping,
    PairingToken,
    PaymentCard,
    Receipt,
    ReceiptLineItem,
    RecurringExpenseOccurrence,
    RecurringExpenseTemplate,
    Shop,
    SyncEvent,
)

User = get_user_model()

# email → Django UUID string  (built during _migrate_users, passed to child methods)
UserMap = dict[str, str]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dt(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    s = str(value)
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f+00:00",
        "%Y-%m-%dT%H:%M:%S+00:00",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def _bool(value: Any) -> bool:
    if value is None:
        return False
    return bool(value)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cur.fetchone() is not None


def _rows(conn: sqlite3.Connection, table: str) -> list[sqlite3.Row]:
    if not _table_exists(conn, table):
        return []
    cur = conn.execute(f"SELECT * FROM {table}")  # noqa: S608
    return cur.fetchall()


def _is_uuid_like(value: Any) -> bool:
    if value is None:
        return False
    try:
        uuid.UUID(str(value))
    except (TypeError, ValueError):
        return False
    return True


class _Rollback(Exception):
    pass


# ── Command ───────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Migrate data from a Flask/SQLite database into the Django database"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--sqlite-path", required=True, help="Path to the source SQLite database")
        parser.add_argument("--dry-run", action="store_true", help="Simulate migration without writing")
        parser.add_argument("--batch-size", type=int, default=500, help="Rows per bulk_create batch")

    def handle(self, *args: Any, **options: Any) -> None:
        sqlite_path = Path(options["sqlite_path"])
        if not sqlite_path.exists():
            raise CommandError(f"SQLite database not found: {sqlite_path}")

        dry_run: bool = options["dry_run"]
        batch_size: int = options["batch_size"]

        self.stdout.write(f"Source: {sqlite_path}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no writes will be committed"))

        conn = sqlite3.connect(str(sqlite_path))
        conn.row_factory = sqlite3.Row

        try:
            with transaction.atomic():
                user_map = self._migrate_users(conn, dry_run)
                self._migrate_categories(conn, dry_run, batch_size, user_map)
                self._migrate_shops(conn, dry_run, batch_size, user_map)
                self._migrate_payment_cards(conn, dry_run, batch_size, user_map)
                self._migrate_category_mappings(conn, dry_run, batch_size, user_map)
                self._migrate_receipts(conn, dry_run, batch_size, user_map)
                self._migrate_receipt_line_items(conn, dry_run, batch_size)
                self._migrate_refresh_tokens(conn, dry_run, batch_size, user_map)
                self._migrate_budgets(conn, dry_run, batch_size, user_map)
                self._migrate_pairing_tokens(conn, dry_run, batch_size, user_map)
                self._migrate_sync_events(conn, dry_run, batch_size, user_map)
                self._migrate_recurring_templates(conn, dry_run, batch_size, user_map)
                self._migrate_recurring_occurrences(conn, dry_run, batch_size)
                self._migrate_amortization_rules(conn, dry_run, batch_size, user_map)

                if dry_run:
                    raise _Rollback()

            self.stdout.write(self.style.SUCCESS("Migration complete."))

        except _Rollback:
            self.stdout.write(self.style.WARNING("Dry run complete — all changes rolled back."))
        finally:
            conn.close()

    # ── Per-table methods ─────────────────────────────────────────────────────

    def _migrate_users(self, conn: sqlite3.Connection, dry_run: bool) -> UserMap:
        """
        Returns email → Django-UUID mapping.

        Flask stores users.id as the email address (VARCHAR PK), not a UUID.
        We look up or create Django users by email and build the mapping needed
        to translate user_id FK values in all child tables.
        """
        rows = _rows(conn, "users")
        created = updated = 0
        user_map: UserMap = {}

        for r in rows:
            email = r["email"].strip().lower()
            password = wrap_werkzeug_hash(r["password_hash"])
            raw_id = str(r["id"]).strip() if r["id"] is not None else ""
            defaults = {
                "username": email,
                "password": password,
                "google_sub": r["google_sub"],
                "is_active": _bool(r["is_active"]),
                "last_sync_at": _dt(r["last_sync_at"]),
            }

            if _is_uuid_like(raw_id):
                user, was_created = User.objects.update_or_create(
                    pk=raw_id,
                    defaults={"email": email, **defaults},
                )
            else:
                user, was_created = User.objects.update_or_create(
                    email=email,
                    defaults=defaults,
                )

            # r["id"] == email in Flask; map it to the Django UUID
            user_map[r["id"]] = str(user.pk)
            if was_created:
                created += 1
            else:
                updated += 1

        self._log("users", len(rows), created, updated, 0)
        return user_map

    def _uid(self, user_map: UserMap, raw: str) -> str:
        """Translate a Flask user_id (email) to a Django UUID string."""
        return user_map.get(raw, raw)

    def _migrate_categories(self, conn: sqlite3.Connection, dry_run: bool, batch: int, user_map: UserMap) -> None:
        rows = _rows(conn, "categories")
        if not rows:
            self._log("categories", 0, 0, 0, 0)
            return

        # Pass 1: create all categories with parent=None to avoid self-ref FK violations
        objs = [
            Category(
                id=r["id"],
                user_id=self._uid(user_map, r["user_id"]),
                external_id=r["external_id"],
                name=r["name"],
                parent_id=None,
                display_order=_int(r["display_order"]),
                is_engel=_bool(r["is_engel"]),
                needs_wants=r["needs_wants"] or "needs",
                is_housing=_bool(r["is_housing"]),
                is_fixed_expense=_bool(r["is_fixed_expense"]),
                is_deleted=_bool(r["is_deleted"]) if "is_deleted" in r.keys() else False,
                created_at=_dt(r["created_at"]) if "created_at" in r.keys() else None,
                updated_at=_dt(r["updated_at"]) if "updated_at" in r.keys() else None,
            )
            for r in rows
        ]
        self._bulk(Category, objs, batch)

        # Pass 2: set parent_id where present
        updated = 0
        for r in rows:
            if r["parent_id"]:
                Category.objects.filter(pk=r["id"]).update(parent_id=r["parent_id"])
                updated += 1

        self._log("categories", len(rows), len(objs), updated, 0)

    def _migrate_shops(self, conn: sqlite3.Connection, dry_run: bool, batch: int, user_map: UserMap) -> None:
        rows = _rows(conn, "shops")
        if not rows:
            self._log("shops", 0, 0, 0, 0)
            return

        keys = set(rows[0].keys()) if rows else set()

        # Pass 1: create with merged_into_shop=None
        objs = [
            Shop(
                id=r["id"],
                user_id=self._uid(user_map, r["user_id"]),
                external_id=r["external_id"],
                name=r["name"],
                address=r["address"],
                normalized_name=r["normalized_name"] if "normalized_name" in keys else None,
                default_category_id=r["default_category_id"] if "default_category_id" in keys else None,
                merged_into_shop_id=None,
                is_active=_bool(r["is_active"]) if "is_active" in keys else True,
                created_at=_dt(r["created_at"]) if "created_at" in keys else None,
                updated_at=_dt(r["updated_at"]) if "updated_at" in keys else None,
            )
            for r in rows
        ]
        self._bulk(Shop, objs, batch)

        # Pass 2: set merged_into_shop_id
        updated = 0
        if "merged_into_shop_id" in keys:
            for r in rows:
                if r["merged_into_shop_id"]:
                    Shop.objects.filter(pk=r["id"]).update(merged_into_shop_id=r["merged_into_shop_id"])
                    updated += 1

        self._log("shops", len(rows), len(objs), updated, 0)

    def _migrate_payment_cards(self, conn: sqlite3.Connection, dry_run: bool, batch: int, user_map: UserMap) -> None:
        rows = _rows(conn, "payment_cards")
        keys = set(rows[0].keys()) if rows else set()
        objs = [
            PaymentCard(
                id=r["id"],
                user_id=self._uid(user_map, r["user_id"]),
                external_id=r["external_id"],
                nickname=r["nickname"],
                card_type=r["card_type"],
                network=r["network"],
                color_hex=r["color_hex"] if "color_hex" in keys else None,
                is_active=_bool(r["is_active"]),
                created_at=_dt(r["created_at"]) if "created_at" in keys else None,
                updated_at=_dt(r["updated_at"]) if "updated_at" in keys else None,
            )
            for r in rows
        ]
        self._bulk(PaymentCard, objs, batch)
        self._log("payment_cards", len(rows), len(objs), 0, 0)

    def _migrate_category_mappings(
        self, conn: sqlite3.Connection, dry_run: bool, batch: int, user_map: UserMap
    ) -> None:
        rows = _rows(conn, "category_mappings")
        keys = set(rows[0].keys()) if rows else set()
        objs = [
            CategoryMapping(
                id=r["id"],
                user_id=self._uid(user_map, r["user_id"]),
                shop_id=r["shop_id"],
                category_id=r["category_id"],
                confidence=_float(r["confidence"], 0.5),
                source=r["source"] if "source" in keys else "user",
                created_at=_dt(r["created_at"]) if "created_at" in keys else None,
                updated_at=_dt(r["updated_at"]) if "updated_at" in keys else None,
            )
            for r in rows
        ]
        self._bulk(CategoryMapping, objs, batch)
        self._log("category_mappings", len(rows), len(objs), 0, 0)

    def _migrate_receipts(self, conn: sqlite3.Connection, dry_run: bool, batch: int, user_map: UserMap) -> None:
        rows = _rows(conn, "receipts")
        if not rows:
            self._log("receipts", 0, 0, 0, 0)
            return
        keys = set(rows[0].keys())

        # Build sets of valid FK targets to avoid FK violations from orphaned references
        from ledger.models import Category as _Cat
        from ledger.models import PaymentCard as _Card
        from ledger.models import Shop as _Shop
        valid_shops = set(str(x) for x in _Shop.objects.values_list("id", flat=True))
        valid_cats = set(str(x) for x in _Cat.objects.values_list("id", flat=True))
        valid_cards = set(str(x) for x in _Card.objects.values_list("id", flat=True))

        def _fk(val: str | None, valid: set) -> str | None:
            return val if val and str(val) in valid else None

        objs = [
            Receipt(
                id=r["id"],
                user_id=self._uid(user_map, r["user_id"]),
                external_id=r["external_id"],
                shop_id=_fk(r["shop_id"], valid_shops),
                category_id=_fk(r["category_id"] if "category_id" in keys else None, valid_cats),
                payment_card_id=_fk(r["payment_card_id"] if "payment_card_id" in keys else None, valid_cards),
                receipt_date=_dt(r["receipt_date"]) or datetime.now(tz=UTC),
                currency=r["currency"],
                subtotal=_float(r["subtotal"]) if "subtotal" in keys else 0.0,
                tax_amount=_float(r["tax_amount"]) if "tax_amount" in keys else 0.0,
                total_amount=_float(r["total_amount"]),
                note=r["note"] if "note" in keys else None,
                is_deleted=_bool(r["is_deleted"]) if "is_deleted" in keys else False,
                created_at=_dt(r["created_at"]) if "created_at" in keys else None,
                updated_at=_dt(r["updated_at"]) if "updated_at" in keys else None,
            )
            for r in rows
        ]
        self._bulk(Receipt, objs, batch)
        self._log("receipts", len(rows), len(objs), 0, 0)

    def _migrate_receipt_line_items(self, conn: sqlite3.Connection, dry_run: bool, batch: int) -> None:
        rows = _rows(conn, "receipt_line_items")
        keys = set(rows[0].keys()) if rows else set()
        objs = [
            ReceiptLineItem(
                id=r["id"],
                receipt_id=r["receipt_id"],
                name=r["name"],
                quantity=_float(r["quantity"], 1.0),
                unit_price=_float(r["unit_price"]),
                line_total=(
                    _float(r["line_total"])
                    if "line_total" in keys
                    else _float(r["quantity"], 1.0) * _float(r["unit_price"])
                ),
            )
            for r in rows
        ]
        self._bulk(ReceiptLineItem, objs, batch)
        self._log("receipt_line_items", len(rows), len(objs), 0, 0)

    def _migrate_refresh_tokens(self, conn: sqlite3.Connection, dry_run: bool, batch: int, user_map: UserMap) -> None:
        rows = _rows(conn, "refresh_tokens")
        # Uniqueness is enforced by token_hash — skip rows already present.
        # Preserve UUID source ids when available; generate UUIDs only for non-UUID ids.
        existing_hashes = set(RefreshToken.objects.values_list("token_hash", flat=True))
        objs: list[RefreshToken] = []
        for r in rows:
            token_hash = r["token_hash"]
            if token_hash in existing_hashes:
                continue

            token_id = str(r["id"]).strip() if r["id"] is not None else ""
            if not _is_uuid_like(token_id):
                token_id = str(uuid.uuid4())

            objs.append(
                RefreshToken(
                    id=token_id,
                    user_id=self._uid(user_map, r["user_id"]),
                    token_hash=token_hash,
                )
            )

        self._bulk(RefreshToken, objs, batch)
        self._log("refresh_tokens", len(rows), len(objs), 0, len(rows) - len(objs))

    def _migrate_budgets(self, conn: sqlite3.Connection, dry_run: bool, batch: int, user_map: UserMap) -> None:
        rows = _rows(conn, "budgets")
        keys = set(rows[0].keys()) if rows else set()
        objs = [
            Budget(
                id=r["id"],
                user_id=self._uid(user_map, r["user_id"]),
                year_month=r["year_month"],
                category_id=r["category_id"] if "category_id" in keys else None,
                mode=r["mode"],
                amount=_float(r["amount"]),
                adjustment_pct=(
                    _int(r["adjustment_pct"])
                    if "adjustment_pct" in keys and r["adjustment_pct"] is not None
                    else None
                ),
                rollover_enabled=(
                    _bool(r["rollover_enabled"]) if "rollover_enabled" in keys else False
                ),
                rollover_balance=(
                    _float(r["rollover_balance"]) if "rollover_balance" in keys else 0.0
                ),
            )
            for r in rows
        ]
        self._bulk(Budget, objs, batch)
        self._log("budgets", len(rows), len(objs), 0, 0)

    def _migrate_pairing_tokens(self, conn: sqlite3.Connection, dry_run: bool, batch: int, user_map: UserMap) -> None:
        rows = _rows(conn, "pairing_tokens")
        keys = set(rows[0].keys()) if rows else set()
        objs = [
            PairingToken(
                id=r["id"],
                user_id=self._uid(user_map, r["user_id"]),
                token_hash=r["token_hash"],
                expires_at=_dt(r["expires_at"]) or datetime.now(tz=UTC),
                created_at=_dt(r["created_at"]) if "created_at" in keys else datetime.now(tz=UTC),
                consumed_at=_dt(r["consumed_at"]) if "consumed_at" in keys else None,
            )
            for r in rows
        ]
        self._bulk(PairingToken, objs, batch)
        self._log("pairing_tokens", len(rows), len(objs), 0, 0)

    def _migrate_sync_events(self, conn: sqlite3.Connection, dry_run: bool, batch: int, user_map: UserMap) -> None:
        rows = _rows(conn, "sync_events")
        keys = set(rows[0].keys()) if rows else set()
        objs = [
            SyncEvent(
                id=r["id"],
                user_id=self._uid(user_map, r["user_id"]),
                device_id=r["device_id"],
                sync_started_at=_dt(r["sync_started_at"]) or datetime.now(tz=UTC),
                sync_completed_at=_dt(r["sync_completed_at"]) if "sync_completed_at" in keys else None,
                status=r["status"] if "status" in keys else "success",
                receipts_count=_int(r["receipts_count"]) if "receipts_count" in keys else 0,
                line_items_count=_int(r["line_items_count"]) if "line_items_count" in keys else 0,
                categories_count=_int(r["categories_count"]) if "categories_count" in keys else 0,
                shops_count=_int(r["shops_count"]) if "shops_count" in keys else 0,
                cards_count=_int(r["cards_count"]) if "cards_count" in keys else 0,
                duplicates_count=_int(r["duplicates_count"]) if "duplicates_count" in keys else 0,
                error_message=r["error_message"] if "error_message" in keys else None,
            )
            for r in rows
        ]
        self._bulk(SyncEvent, objs, batch)
        self._log("sync_events", len(rows), len(objs), 0, 0)

    def _migrate_recurring_templates(
        self, conn: sqlite3.Connection, dry_run: bool, batch: int, user_map: UserMap
    ) -> None:
        rows = _rows(conn, "recurring_expense_templates")
        objs = [
            RecurringExpenseTemplate(
                id=r["id"],
                user_id=self._uid(user_map, r["user_id"]),
                name=r["name"],
                expected_amount=_float(r["expected_amount"]),
                frequency=r["frequency"],
                start_date=_dt(r["start_date"]) or datetime.now(tz=UTC),
            )
            for r in rows
        ]
        self._bulk(RecurringExpenseTemplate, objs, batch)
        self._log("recurring_expense_templates", len(rows), len(objs), 0, 0)

    def _migrate_recurring_occurrences(self, conn: sqlite3.Connection, dry_run: bool, batch: int) -> None:
        rows = _rows(conn, "recurring_expense_occurrences")
        keys = set(rows[0].keys()) if rows else set()
        objs = [
            RecurringExpenseOccurrence(
                id=r["id"],
                template_id=r["template_id"],
                due_date=_dt(r["due_date"]) or datetime.now(tz=UTC),
                status=r["status"] if "status" in keys else "upcoming",
            )
            for r in rows
        ]
        self._bulk(RecurringExpenseOccurrence, objs, batch)
        self._log("recurring_expense_occurrences", len(rows), len(objs), 0, 0)

    def _migrate_amortization_rules(
        self, conn: sqlite3.Connection, dry_run: bool, batch: int, user_map: UserMap
    ) -> None:
        rows = _rows(conn, "amortization_rules")
        keys = set(rows[0].keys()) if rows else set()
        objs = [
            AmortizationRule(
                id=r["id"],
                user_id=self._uid(user_map, r["user_id"]),
                title=r["title"],
                total_amount=_float(r["total_amount"]),
                months=_int(r["months"], 12),
                monthly_amount=_float(r["monthly_amount"]),
                status=r["status"] if "status" in keys else "active",
            )
            for r in rows
        ]
        self._bulk(AmortizationRule, objs, batch)
        self._log("amortization_rules", len(rows), len(objs), 0, 0)

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _bulk(self, model: Any, objs: list, batch: int) -> None:
        for i in range(0, len(objs), batch):
            model.objects.bulk_create(objs[i : i + batch], ignore_conflicts=True)

    def _log(self, table: str, total: int, inserted: int, updated: int, skipped: int) -> None:
        msg = f"  {table}: {total} rows — inserted={inserted} updated={updated} skipped={skipped}"
        self.stdout.write(msg)
