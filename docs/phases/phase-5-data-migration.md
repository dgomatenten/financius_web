# Phase 5 — Data Migration

## Status
[x] Complete | Date: 2026-05-29

## Goal
Copy all rows from the legacy Flask/SQLAlchemy/SQLite database into the Django
target database (SQLite dev or PostgreSQL prod) in a single idempotent management
command, and handle password hash format incompatibilities transparently.

## Components

| Component | Location | What it does |
|---|---|---|
| `WerkzeugPasswordHasher` | `accounts/hashers.py` | DRF hasher for werkzeug-format passwords migrated from Flask; auto-upgrades to native PBKDF2 on first login |
| `wrap_werkzeug_hash()` | `accounts/hashers.py` | Wraps a raw werkzeug hash with an algorithm prefix so `identify_hasher()` routes to the correct hasher |
| `migrate_from_sqlite` | `ledger/management/commands/migrate_from_sqlite.py` | Management command — migrates 14 tables in FK dependency order; idempotent; supports `--dry-run` |

## Tables migrated (in order)

1. `users` — `update_or_create` per row; passwords wrapped via `wrap_werkzeug_hash()`
2. `categories` — two-pass: create all with `parent=None`, then back-fill `parent_id`
3. `shops` — two-pass: create all with `merged_into_shop=None`, then back-fill
4. `payment_cards`
5. `category_mappings`
6. `receipts`
7. `receipt_line_items`
8. `refresh_tokens`
9. `budgets`
10. `pairing_tokens`
11. `sync_events`
12. `recurring_expense_templates`
13. `recurring_expense_occurrences`
14. `amortization_rules`

## Decisions

1. **`bulk_create(ignore_conflicts=True)` for idempotency** — All tables except
   `users` use `bulk_create` with `ignore_conflicts=True`. Re-running the command
   skips rows that already exist (matched on PK) without raising. `users` uses
   `update_or_create` to allow email/google_sub updates across runs.

2. **Two-pass migration for self-referential FKs** — `categories.parent_id` and
   `shops.merged_into_shop_id` point back to rows in the same table. Pass 1 creates
   all rows with the self-ref FK set to `None`, avoiding FK violations when the
   parent row hasn't been inserted yet. Pass 2 back-fills the FK with targeted
   `filter().update()` calls.

3. **`--dry-run` via `_Rollback` inside `transaction.atomic()`** — The entire
   migration runs inside a single transaction. When `--dry-run` is set, a sentinel
   `_Rollback` exception is raised at the end, which rolls back the transaction.
   Using an exception rather than a flag avoids needing to thread the flag through
   every helper method.

4. **Werkzeug password format incompatibility** — Werkzeug stores passwords as
   `pbkdf2:sha256:<iters>$<salt>$<hash>`. Django's `identify_hasher()` parses
   algorithm from the first `$`-separated segment, which in werkzeug's format is
   `pbkdf2:sha256:<iters>` — different for every password (iter count varies).
   Solution: `wrap_werkzeug_hash()` prepends a fixed `werkzeug_pbkdf2_sha256$`
   prefix, and `WerkzeugPasswordHasher` uses that as its `.algorithm` attribute,
   making `identify_hasher()` reliably select it. `must_update=True` ensures users
   are silently migrated to native Django PBKDF2 on first login.

5. **Missing columns via `"col" in r.keys()` guard** — The Flask database was
   extended incrementally; some older rows are missing columns that were added
   later. All optional columns are guarded with an `in r.keys()` check before
   access so the command tolerates schema divergence between DB versions.

6. **Missing tables return empty list** — `_rows()` calls `_table_exists()` first
   and returns `[]` for tables that don't exist, so the command works on partial
   databases (e.g. a database that predates the `recurring_expense_templates` table).

## Schema divergences vs Flask SQLite

| Django field | SQLite column | Notes |
|---|---|---|
| `User.password` | `users.password_hash` | Wrapped with algorithm prefix via `wrap_werkzeug_hash()` |
| `User.username` | (none) | Set to `email` during migration (Django requires unique username) |
| `Category.needs_wants` | `categories.needs_wants` | Defaults to `"needs"` if null |
| `Shop.is_active` | `shops.is_active` | Defaults to `True` if column missing |

## Usage

```bash
# Migrate from the live SQLite database
python3 manage.py migrate_from_sqlite --sqlite-path /path/to/financius.db

# Dry run — inspect counts without writing
python3 manage.py migrate_from_sqlite --sqlite-path /path/to/financius.db --dry-run

# Smaller batch size for low-memory environments
python3 manage.py migrate_from_sqlite --sqlite-path /path/to/financius.db --batch-size 100
```

## Test coverage

- `backend/tests/dj/unit/test_migrate_from_sqlite.py` — 23 tests

| Class | Tests |
|---|---|
| `TestUserMigration` | basic user, werkzeug password, google_sub, idempotency, dry-run |
| `TestCategoryMigration` | flat categories, parent-child wiring, missing table |
| `TestShopMigration` | basic shop, merged_into_shop two-pass |
| `TestReceiptMigration` | FK references, line items, idempotency, dry-run |
| `TestWerkzeugPasswordHasher` | wrap prefix, None/empty → unusable, verify correct, verify wrong, must_update |
| `TestRefreshTokenMigration` | token migrated with correct user FK |
| `TestEdgeCases` | nonexistent path raises, empty DB completes cleanly |

## Checklist
- [x] `WerkzeugPasswordHasher` implemented in `accounts/hashers.py`
- [x] `PASSWORD_HASHERS` updated in `settings.py`
- [x] Management command `migrate_from_sqlite` implemented (14 tables)
- [x] Two-pass migration for self-referential FKs (categories, shops)
- [x] Dry-run rolls back atomically via `_Rollback` + `transaction.atomic()`
- [x] Idempotent — safe to re-run; duplicate rows skipped via `ignore_conflicts=True`
- [x] 23 migration tests passing
- [x] 131 total tests passing (23 new + 108 prior)
