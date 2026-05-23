# Data Model: Financius Web

## Overview
Primary storage is relational via SQLAlchemy ORM. Model definitions are constrained to
SQLite-compatible primitives that are also PostgreSQL-friendly. All core entities are
user-scoped unless explicitly global.

## Entities

### User
- Fields:
  - id (UUID/string primary key)
  - email (unique, required)
  - password_hash (nullable for Google-only accounts)
  - google_sub (nullable, unique)
  - created_at, updated_at
  - last_sync_at (nullable)
  - is_active (bool, default true)
- Validation:
  - email must be normalized and unique
  - at least one credential path present: password_hash or google_sub
- Relationships:
  - 1:N with receipts, categories, shops, cards, budgets, recurring expenses,
    amortization rules, sync events, category mappings

### Category
- Fields:
  - id
  - user_id (FK users.id)
  - name (required)
  - parent_id (nullable FK categories.id)
  - display_order (int, default 0)
  - is_engel (bool)
  - needs_wants (enum: needs|wants)
  - is_housing (bool)
  - is_fixed_expense (bool)
  - is_deleted (bool, soft-delete)
  - created_at, updated_at
- Validation:
  - name unique within same parent for one user
  - parent_id cannot create cycles
- Relationships:
  - self-referencing tree
  - 1:N with receipts, budgets, recurring expenses, category mappings

### Shop
- Fields:
  - id
  - user_id
  - name (required)
  - normalized_name (for dedupe)
  - address (nullable)
  - default_category_id (nullable FK categories.id)
  - merged_into_shop_id (nullable FK shops.id)
  - is_active (bool)
  - created_at, updated_at
- Validation:
  - normalized_name required for merge suggestions
- Relationships:
  - 1:N with receipts and category mappings

### PaymentCard
- Fields:
  - id
  - user_id
  - nickname
  - card_type (enum: credit|debit|prepaid|digital_wallet)
  - network (enum/string: visa|mastercard|amex|etc)
  - color_hex (string)
  - is_active (bool)
  - created_at, updated_at
- Validation:
  - color_hex must match hex format

### CategoryMapping
- Fields:
  - id
  - user_id
  - shop_id (FK)
  - category_id (FK)
  - confidence (decimal 0..1)
  - source (enum: ai|user)
  - created_at, updated_at
- Validation:
  - unique (user_id, shop_id)

### Receipt
- Fields:
  - id
  - user_id
  - external_id (string from Android, unique per user)
  - shop_id (nullable FK)
  - category_id (nullable FK)
  - payment_card_id (nullable FK)
  - receipt_date (datetime)
  - currency (enum/string)
  - subtotal, tax_amount, total_amount (decimal)
  - note (nullable)
  - source (enum: android_sync|web_import)
  - created_at, updated_at, deleted_at (nullable soft-delete)
- Validation:
  - total_amount >= 0
  - currency in supported list (USD/JPY/EUR/GBP/KRW/CNY/CAD/AUD)
- Relationships:
  - 1:N with receipt line items
  - optional 1:1 or 1:N from amortization rules

### ReceiptLineItem
- Fields:
  - id
  - receipt_id (FK receipts.id)
  - name
  - quantity (decimal)
  - unit_price (decimal)
  - line_total (decimal)
  - created_at, updated_at
- Validation:
  - quantity > 0
  - line_total >= 0

### Budget
- Fields:
  - id
  - user_id
  - year_month (YYYY-MM)
  - category_id (nullable; null means total budget)
  - mode (enum: manual|forecast|forecast_adjusted)
  - amount (decimal)
  - adjustment_pct (nullable int, 80..120)
  - rollover_enabled (bool)
  - rollover_balance (decimal)
  - created_at, updated_at
- Validation:
  - amount >= 0
  - adjustment_pct required only for forecast_adjusted
- Relationships:
  - category optional FK

### RecurringExpenseTemplate
- Fields:
  - id
  - user_id
  - name
  - category_id (FK)
  - expected_amount (decimal)
  - frequency (enum: weekly|monthly|yearly)
  - start_date
  - is_active (bool)
  - created_at, updated_at
- Validation:
  - expected_amount > 0

### RecurringExpenseOccurrence
- Fields:
  - id
  - template_id (FK)
  - due_date
  - status (enum: upcoming|fulfilled|missed)
  - matched_receipt_id (nullable FK receipts.id)
  - created_at, updated_at
- Validation:
  - one occurrence per template per period

### AmortizationRule
- Fields:
  - id
  - user_id
  - receipt_id (nullable FK receipts.id)
  - title
  - total_amount (decimal)
  - months (int)
  - start_year_month (YYYY-MM)
  - monthly_amount (decimal)
  - status (enum: active|completed)
  - created_at, updated_at
- Validation:
  - months >= 2
  - total_amount > 0

### SyncEvent
- Fields:
  - id
  - user_id
  - device_id
  - sync_started_at
  - sync_completed_at
  - status (enum: success|partial|failed)
  - receipts_count
  - line_items_count
  - categories_count
  - shops_count
  - cards_count
  - error_message (nullable)
- Validation:
  - sync_completed_at >= sync_started_at

### RefreshToken
- Fields:
  - id
  - user_id
  - token_hash
  - issued_at
  - expires_at
  - revoked_at (nullable)
  - replaced_by_token_id (nullable self FK)
- Validation:
  - only active tokens accepted for refresh flow

## Cross-Entity Rules
- User isolation: all queries filtered by user_id boundary.
- Category deletion requires reassignment of dependent receipts/budgets/mappings.
- Shop merge updates dependent receipts and mappings transactionally.
- Sync upsert key: (user_id, external_id) for receipts.
- Analytics read models aggregate from receipts + line items + budgets + recurring + amortization.

## State Transitions
- PaymentCard: active -> inactive (no reactivation restrictions).
- RecurringExpenseOccurrence: upcoming -> fulfilled|missed.
- AmortizationRule: active -> completed (automatic when period ends).
- SyncEvent: started -> success|partial|failed.
