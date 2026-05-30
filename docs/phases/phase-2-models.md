# Phase 2 — Port Models

## Status
[x] Complete | Date: 2026-05-29

## Goal
Translate all SQLAlchemy models to Django ORM models, preserving table names so the
data migration script (Phase 5) can copy rows without renaming columns.

## Models ported

| SQLAlchemy model | Django app | Django model | Status |
|---|---|---|---|
| `User`, `RefreshToken` | `accounts` | `User(AbstractUser)`, `RefreshToken` | Done |
| `Category` | `ledger` | `Category` | Done |
| `Shop`, `PaymentCard`, `CategoryMapping` | `ledger` | `Shop`, `PaymentCard`, `CategoryMapping` | Done |
| `Receipt`, `ReceiptLineItem` | `ledger` | `Receipt`, `ReceiptLineItem` | Done |
| `Budget` | `ledger` | `Budget` | Done |
| `PairingToken`, `SyncEvent` | `ledger` | `PairingToken`, `SyncEvent` | Done |
| `RecurringExpenseTemplate`, `RecurringExpenseOccurrence` | `ledger` | same | Done |
| `AmortizationRule` | `ledger` | `AmortizationRule` | Done |

## Schema divergences

| Model | Field | Flask type | Django type | Reason |
|---|---|---|---|---|
| `User` | `id` | `String` PK (UUID stored as str) | `UUIDField` PK | Native UUID support in Django |
| `User` | `password_hash` | `String nullable` | `password` (AbstractUser built-in) | Django handles hashing |
| `RefreshToken` | `id` | `String` PK | `UUIDField` PK | Same as above |
| `RefreshToken` | `user_id` | bare `String` FK | `ForeignKey(User)` | Proper relational integrity |

## Decisions

1. **`User` extends `AbstractUser`** — Django handles password hashing, session auth, and
   admin. The alternative (`AbstractBaseUser`) requires reimplementing too much for no gain.

2. **`email` as `USERNAME_FIELD`** — matches the Flask auth flow where login is by email.
   `username` is kept as `REQUIRED_FIELDS` for Django admin compatibility.

3. **`db_table` set on every model** — matches the legacy SQLite table names exactly.
   This is required for the Phase 5 data migration script.

4. **`is_deleted` soft-delete on all models** — matches the Flask pattern. Hard deletes
   are never used so Android sync can detect removals.

5. **All models in `ledger` app** — grouping non-auth models into one app keeps the
   project flat and avoids over-engineering before the migration is proven.

## Schema divergences (additions)

| Model | Field | Flask | Django | Reason |
|---|---|---|---|---|
| `Category` | `parent_id` | bare `String` | `ForeignKey("self")` | Proper self-ref integrity |
| `Shop` | `default_category_id` | bare `String` | `ForeignKey(Category)` | Relational integrity |
| `Shop` | `merged_into_shop_id` | bare `String` | `ForeignKey("self")` | Relational integrity |
| `CategoryMapping` | `shop_id`, `category_id` | bare `String` | `ForeignKey(Shop/Category)` | Relational integrity |

**Note on `uq_category_name_scope`:** The constraint is `(user, parent, name)`. Two categories
with `parent=NULL` do not collide — this is standard SQL NULL behaviour, matching Flask/SQLite.

## Test coverage

- `backend/tests/dj/unit/test_user_model.py` — User + RefreshToken (10 tests)
- `backend/tests/dj/unit/test_ledger_models.py` — Category, Shop, PaymentCard, CategoryMapping (19 tests)
- `backend/tests/dj/unit/test_receipt_models.py` — Receipt, ReceiptLineItem (14 tests)
- `backend/tests/dj/unit/test_remaining_models.py` — Budget, PairingToken, SyncEvent, Recurring*, AmortizationRule (22 tests)

## Checklist
- [x] `User` + `RefreshToken` models created (`accounts` app)
- [x] `accounts/migrations/0001_initial.py` applied
- [x] `Category`, `Shop`, `PaymentCard`, `CategoryMapping` ported (`ledger` app)
- [x] `ledger/migrations/0001_initial.py` applied
- [x] `Receipt`, `ReceiptLineItem` ported (`ledger/migrations/0002_receipt_receiptlineitem_and_more.py`)
- [x] `Budget` ported
- [x] `PairingToken`, `SyncEvent` ported
- [x] `RecurringExpenseTemplate`, `RecurringExpenseOccurrence` ported
- [x] `AmortizationRule` ported
- [x] All unit tests passing (71 passed, 2 skipped)
