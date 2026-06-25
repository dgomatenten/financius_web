"""
Phase 5 — migrate_from_sqlite management command tests.

Each test builds a minimal in-memory SQLite database (written to a temp file
so the command can open it via file path), calls the management command, then
asserts the Django ORM reflects the expected state.
"""
from __future__ import annotations

import sqlite3
import tempfile
import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from werkzeug.security import generate_password_hash

from accounts.hashers import WerkzeugPasswordHasher, wrap_werkzeug_hash
from accounts.models import RefreshToken
from ledger.models import Category, Receipt, ReceiptLineItem, Shop

User = get_user_model()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sqlite_db() -> Generator[Path, None, None]:
    """Yield a path to a temporary blank SQLite file. Deleted after the test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    db_path.unlink(missing_ok=True)


def _conn(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _create_users_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            password_hash TEXT,
            google_sub TEXT,
            is_active INTEGER DEFAULT 1,
            last_sync_at TEXT
        )
    """)
    conn.commit()


def _create_categories_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            external_id TEXT,
            name TEXT NOT NULL,
            parent_id TEXT,
            display_order INTEGER DEFAULT 0,
            is_engel INTEGER DEFAULT 0,
            needs_wants TEXT DEFAULT 'needs',
            is_housing INTEGER DEFAULT 0,
            is_fixed_expense INTEGER DEFAULT 0,
            is_deleted INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()


def _create_shops_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shops (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            external_id TEXT,
            name TEXT NOT NULL,
            address TEXT,
            normalized_name TEXT,
            default_category_id TEXT,
            merged_into_shop_id TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()


def _create_payment_cards_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payment_cards (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            external_id TEXT,
            nickname TEXT NOT NULL,
            card_type TEXT NOT NULL,
            network TEXT NOT NULL,
            color_hex TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()


def _create_receipts_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            external_id TEXT,
            shop_id TEXT,
            category_id TEXT,
            payment_card_id TEXT,
            receipt_date TEXT,
            currency TEXT DEFAULT 'USD',
            subtotal REAL DEFAULT 0,
            tax_amount REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            note TEXT,
            is_deleted INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()


def _create_receipt_line_items_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS receipt_line_items (
            id TEXT PRIMARY KEY,
            receipt_id TEXT NOT NULL,
            name TEXT NOT NULL,
            quantity REAL DEFAULT 1,
            unit_price REAL NOT NULL,
            line_total REAL
        )
    """)
    conn.commit()


def _create_refresh_tokens_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token_hash TEXT NOT NULL
        )
    """)
    conn.commit()


def _now() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S")


# ── User migration ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserMigration:
    def test_migrates_basic_user(self, sqlite_db: Path) -> None:
        conn = _conn(sqlite_db)
        _create_users_table(conn)
        uid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
            (uid, "alice@example.com", None, None, 1, None),
        )
        conn.commit()
        conn.close()

        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))

        user = User.objects.get(pk=uid)
        assert user.email == "alice@example.com"
        assert user.is_active is True

    def test_migrates_werkzeug_password(self, sqlite_db: Path) -> None:
        """Werkzeug-hashed passwords must be wrapped so Django can verify them."""
        conn = _conn(sqlite_db)
        _create_users_table(conn)
        uid = str(uuid.uuid4())
        plain = "s3cr3tP@ss"
        wz_hash = generate_password_hash(plain, method="pbkdf2:sha256")  # force pbkdf2 format
        conn.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
            (uid, "bob@example.com", wz_hash, None, 1, None),
        )
        conn.commit()
        conn.close()

        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))

        user = User.objects.get(pk=uid)
        # Django's check_password must succeed with the original plaintext
        assert user.check_password(plain)

    def test_migrates_google_sub(self, sqlite_db: Path) -> None:
        conn = _conn(sqlite_db)
        _create_users_table(conn)
        uid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
            (uid, "carol@example.com", None, "google-sub-123", 1, None),
        )
        conn.commit()
        conn.close()

        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))

        user = User.objects.get(pk=uid)
        assert user.google_sub == "google-sub-123"

    def test_idempotent_user_migration(self, sqlite_db: Path) -> None:
        """Running the command twice must not create duplicate users."""
        conn = _conn(sqlite_db)
        _create_users_table(conn)
        uid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
            (uid, "idempotent@example.com", None, None, 1, None),
        )
        conn.commit()
        conn.close()

        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))
        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))

        assert User.objects.filter(pk=uid).count() == 1

    def test_dry_run_does_not_persist_users(self, sqlite_db: Path) -> None:
        conn = _conn(sqlite_db)
        _create_users_table(conn)
        uid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
            (uid, "dry@example.com", None, None, 1, None),
        )
        conn.commit()
        conn.close()

        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db), dry_run=True)

        assert not User.objects.filter(pk=uid).exists()


# ── Category migration ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCategoryMigration:
    def _setup_user(self, sqlite_db: Path) -> tuple[sqlite3.Connection, str]:
        conn = _conn(sqlite_db)
        _create_users_table(conn)
        _create_categories_table(conn)
        uid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
            (uid, "cat_user@example.com", None, None, 1, None),
        )
        conn.commit()
        return conn, uid

    def test_migrates_flat_categories(self, sqlite_db: Path) -> None:
        conn, uid = self._setup_user(sqlite_db)
        cat_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO categories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cat_id, uid, "ext-1", "Food", None, 0, 0, "needs", 0, 0, 0, _now(), _now()),
        )
        conn.commit()
        conn.close()

        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))

        cat = Category.objects.get(pk=cat_id)
        assert cat.name == "Food"
        assert cat.parent_id is None

    def test_migrates_parent_child_relationship(self, sqlite_db: Path) -> None:
        """Two-pass migration must wire up parent_id correctly."""
        conn, uid = self._setup_user(sqlite_db)
        parent_id = str(uuid.uuid4())
        child_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO categories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (parent_id, uid, "ext-p", "Food", None, 0, 0, "needs", 0, 0, 0, _now(), _now()),
        )
        conn.execute(
            "INSERT INTO categories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (child_id, uid, "ext-c", "Restaurants", parent_id, 1, 0, "wants", 0, 0, 0, _now(), _now()),
        )
        conn.commit()
        conn.close()

        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))

        parent = Category.objects.get(pk=parent_id)
        child = Category.objects.get(pk=child_id)
        assert child.parent_id == parent.id
        assert parent.parent_id is None

    def test_missing_categories_table_is_handled(self, sqlite_db: Path) -> None:
        """Command must not crash when categories table does not exist."""
        conn = _conn(sqlite_db)
        _create_users_table(conn)
        conn.commit()
        conn.close()

        # Should complete without exception
        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))


# ── Shop migration ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestShopMigration:
    def _setup(self, sqlite_db: Path) -> tuple[sqlite3.Connection, str]:
        conn = _conn(sqlite_db)
        _create_users_table(conn)
        _create_shops_table(conn)
        uid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
            (uid, "shop_user@example.com", None, None, 1, None),
        )
        conn.commit()
        return conn, uid

    def test_migrates_basic_shop(self, sqlite_db: Path) -> None:
        conn, uid = self._setup(sqlite_db)
        shop_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO shops VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (shop_id, uid, "ext-s1", "Whole Foods", "123 Main St", "whole foods", None, None, 1, _now(), _now()),
        )
        conn.commit()
        conn.close()

        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))

        shop = Shop.objects.get(pk=shop_id)
        assert shop.name == "Whole Foods"
        assert shop.merged_into_shop_id is None

    def test_migrates_merged_into_shop(self, sqlite_db: Path) -> None:
        """Two-pass migration must set merged_into_shop_id."""
        conn, uid = self._setup(sqlite_db)
        canonical_id = str(uuid.uuid4())
        merged_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO shops VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (canonical_id, uid, "ext-canon", "WF Market", None, None, None, None, 1, _now(), _now()),
        )
        conn.execute(
            "INSERT INTO shops VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (merged_id, uid, "ext-merged", "Whole Foods Old", None, None, None, canonical_id, 0, _now(), _now()),
        )
        conn.commit()
        conn.close()

        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))

        canonical = Shop.objects.get(pk=canonical_id)
        merged = Shop.objects.get(pk=merged_id)
        assert merged.merged_into_shop_id == canonical.id
        assert canonical.merged_into_shop_id is None


# ── Receipt migration ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReceiptMigration:
    def _setup(self, sqlite_db: Path) -> tuple[sqlite3.Connection, str, str, str]:
        conn = _conn(sqlite_db)
        _create_users_table(conn)
        _create_shops_table(conn)
        _create_payment_cards_table(conn)
        _create_receipts_table(conn)

        uid = str(uuid.uuid4())
        shop_id = str(uuid.uuid4())
        card_id = str(uuid.uuid4())

        conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", (uid, "r@example.com", None, None, 1, None))
        conn.execute(
            "INSERT INTO shops VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (shop_id, uid, None, "Target", None, None, None, None, 1, _now(), _now()),
        )
        conn.execute(
            "INSERT INTO payment_cards VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (card_id, uid, None, "Visa Platinum", "credit", "visa", "#003087", 1, _now(), _now()),
        )
        conn.commit()
        return conn, uid, shop_id, card_id

    def test_migrates_receipt_with_fk_references(self, sqlite_db: Path) -> None:
        conn, uid, shop_id, card_id = self._setup(sqlite_db)
        receipt_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO receipts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (receipt_id, uid, "ext-r1", shop_id, None, card_id,
             "2024-03-15 12:00:00", "USD", 45.0, 3.6, 48.6, "Weekly shop", 0, _now(), _now()),
        )
        conn.commit()
        conn.close()

        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))

        receipt = Receipt.objects.get(pk=receipt_id)
        assert receipt.shop_id == uuid.UUID(shop_id)
        assert receipt.payment_card_id == uuid.UUID(card_id)
        assert abs(receipt.total_amount - 48.6) < 0.001
        assert receipt.currency == "USD"

    def test_migrates_receipt_line_items(self, sqlite_db: Path) -> None:
        conn, uid, shop_id, card_id = self._setup(sqlite_db)
        _create_receipt_line_items_table(conn)
        receipt_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO receipts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (receipt_id, uid, None, shop_id, None, None,
             "2024-03-15 12:00:00", "USD", 10.0, 0.0, 10.0, None, 0, _now(), _now()),
        )
        item_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO receipt_line_items VALUES (?, ?, ?, ?, ?, ?)",
            (item_id, receipt_id, "Organic Milk", 2.0, 3.99, 7.98),
        )
        conn.commit()
        conn.close()

        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))

        item = ReceiptLineItem.objects.get(pk=item_id)
        assert item.receipt_id == uuid.UUID(receipt_id)
        assert item.name == "Organic Milk"
        assert item.quantity == 2.0
        assert abs(item.line_total - 7.98) < 0.001

    def test_idempotent_receipt_migration(self, sqlite_db: Path) -> None:
        conn, uid, shop_id, card_id = self._setup(sqlite_db)
        receipt_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO receipts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (receipt_id, uid, None, shop_id, None, None,
             "2024-01-01 00:00:00", "USD", 5.0, 0.0, 5.0, None, 0, _now(), _now()),
        )
        conn.commit()
        conn.close()

        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))
        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))

        assert Receipt.objects.filter(pk=receipt_id).count() == 1

    def test_dry_run_does_not_persist_receipts(self, sqlite_db: Path) -> None:
        conn, uid, shop_id, card_id = self._setup(sqlite_db)
        receipt_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO receipts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (receipt_id, uid, None, shop_id, None, None,
             "2024-01-01 00:00:00", "USD", 5.0, 0.0, 5.0, None, 0, _now(), _now()),
        )
        conn.commit()
        conn.close()

        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db), dry_run=True)

        assert not Receipt.objects.filter(pk=receipt_id).exists()


# ── Hasher unit tests ─────────────────────────────────────────────────────────

class TestWerkzeugPasswordHasher:
    def test_wrap_werkzeug_hash_prefixes_correctly(self) -> None:
        wz = "pbkdf2:sha256:600000$abc$def"
        wrapped = wrap_werkzeug_hash(wz)
        assert wrapped.startswith("werkzeug_pbkdf2_sha256$")
        assert wrapped.endswith(wz)

    def test_wrap_none_returns_unusable(self) -> None:
        assert wrap_werkzeug_hash(None) == "!"

    def test_wrap_empty_string_returns_unusable(self) -> None:
        assert wrap_werkzeug_hash("") == "!"

    def test_hasher_verify_accepts_correct_password(self) -> None:
        plain = "mypassword123"
        wz_hash = generate_password_hash(plain, method="pbkdf2:sha256")
        wrapped = wrap_werkzeug_hash(wz_hash)
        hasher = WerkzeugPasswordHasher()
        assert hasher.verify(plain, wrapped) is True

    def test_hasher_verify_rejects_wrong_password(self) -> None:
        plain = "mypassword123"
        wz_hash = generate_password_hash(plain, method="pbkdf2:sha256")
        wrapped = wrap_werkzeug_hash(wz_hash)
        hasher = WerkzeugPasswordHasher()
        assert hasher.verify("wrongpassword", wrapped) is False

    def test_hasher_must_update_always_true(self) -> None:
        hasher = WerkzeugPasswordHasher()
        assert hasher.must_update("werkzeug_pbkdf2_sha256$pbkdf2:sha256:600000$s$h") is True


# ── Refresh token migration ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestRefreshTokenMigration:
    def test_migrates_refresh_tokens(self, sqlite_db: Path) -> None:
        conn = _conn(sqlite_db)
        _create_users_table(conn)
        _create_refresh_tokens_table(conn)
        uid = str(uuid.uuid4())
        tok_id = str(uuid.uuid4())
        conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", (uid, "tok@example.com", None, None, 1, None))
        conn.execute("INSERT INTO refresh_tokens VALUES (?, ?, ?)", (tok_id, uid, "hashed-token-value"))
        conn.commit()
        conn.close()

        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))

        assert RefreshToken.objects.filter(pk=tok_id, user_id=uid, token_hash="hashed-token-value").exists()


# ── Edge cases ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEdgeCases:
    def test_nonexistent_sqlite_path_raises(self) -> None:
        from django.core.management.base import CommandError
        with pytest.raises((CommandError, SystemExit)):
            call_command("migrate_from_sqlite", sqlite_path="/tmp/does_not_exist_xyz.db")

    def test_empty_database_completes_cleanly(self, sqlite_db: Path) -> None:
        """A SQLite file with no tables must not raise."""
        call_command("migrate_from_sqlite", sqlite_path=str(sqlite_db))
