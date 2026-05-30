# Django Migration Plan

## Current State (as of 2026-05-29)

The backend is **100% Flask** — no Django code exists yet. The goal declared in
`CLAUDE.md` ("new code MUST target Django ORM models") is aspirational but not yet started.

### Stack

| Layer | Current |
|---|---|
| Framework | Flask 3.0.3 |
| ORM | SQLAlchemy 2.0.30 |
| Database | SQLite locally (`data/financius.db`, 2.7 MB); PostgreSQL via `DATABASE_URL` in prod |
| Migrations | Alembic — 1 migration exists (`0002_performance_indexes.py`) |
| Auth | PyJWT + Authlib (Google OAuth) |
| Entrypoint | `gunicorn "src.app:create_app()"` (prod), Flask dev server (local) |
| Container | Single-stage `infra/docker/backend.Dockerfile`; no Postgres in compose |

### Models (SQLAlchemy)

All live in `backend/src/models/`:

| Model | File |
|---|---|
| `User`, `RefreshToken` | `user.py` |
| `Receipt`, `ReceiptLineItem` | `receipt.py` |
| `Category` | `category.py` |
| `Shop`, `PaymentCard`, `CategoryMapping` | `master_data.py` |
| `Budget` | `budget.py` |
| `PairingToken` | `pairing_token.py` |
| `SyncEvent` | `sync_event.py` |
| `RecurringExpenseTemplate`, `RecurringExpenseOccurrence` | `recurring.py` |
| `AmortizationRule` | `amortization.py` |

### API Routes (Flask Blueprints under `/api/v1`)

| Blueprint | Routes |
|---|---|
| `auth.py` | POST `/register`, `/login`, `/google`, `/refresh`, `/logout` |
| `receipts.py` | CRUD `/receipts`, line items |
| `sync.py` | POST `/sync` (371 lines — largest endpoint) |
| `master_data.py` | CRUD categories, shops, cards |
| `budgets.py` | CRUD budgets |
| `pairing.py` | POST `/pairing/initiate`, `/pairing/verify` |
| `analytics.py` | GET analytics endpoints |
| `recurring.py` | GET/POST recurring expenses |
| `export.py` | POST `/export` |
| `amortization.py` | GET/POST amortization rules |

### Service & Repository Layers

- **20+ service modules** in `backend/src/services/` (auth, receipts, sync, budgets, analytics, pairing, recurring, amortization, etc.)
- **5 repository modules** in `backend/src/repositories/` (user, receipt, pairing, sync, analytics)
- Clean layered architecture — services can largely be reused post-migration

### Live Schema Patching

`app.py` contains `_ensure_sync_events_schema()` which patches old SQLite DBs at startup
(adds missing columns via `PRAGMA table_info()`). This is tech debt to eliminate during migration.

---

## Target State

| Layer | Target |
|---|---|
| Framework | Django + Django REST Framework |
| ORM | Django ORM (`models.Model`) |
| Database | PostgreSQL |
| Migrations | Django `makemigrations` / `migrate` |
| Auth | DRF token auth or SimpleJWT (preserve JWT contract for Android) |
| Entrypoint | `gunicorn financius_web.wsgi` |
| Container | Backend + PostgreSQL service in compose |

---

## Migration Scope

### Phase 1 — Django Project Scaffold
- `django-admin startproject financius_web backend/`
- Add `djangorestframework`, `psycopg2-binary` to `requirements.txt`
- Wire `settings.py` to read existing env vars (`DATABASE_URL`, `SECRET_KEY`, etc.)
- Stand up Django with empty DB alongside Flask (dual-entrypoint)

### Phase 2 — Port Models
Translate each SQLAlchemy model to a Django `models.Model`, preserving column names
so the PostgreSQL schema matches the existing SQLite layout. Run `makemigrations`.

Priority order (dependencies first):
1. `User` (no FK deps)
2. `Category`, `Shop`, `PaymentCard`
3. `CategoryMapping`
4. `Receipt`, `ReceiptLineItem`
5. `Budget`
6. `PairingToken`, `SyncEvent`, `RefreshToken`
7. `RecurringExpenseTemplate`, `RecurringExpenseOccurrence`
8. `AmortizationRule`

### Phase 3 — Port API Endpoints
Convert each Flask Blueprint to a DRF `ViewSet` or `APIView`, preserving the
`{ data, error, meta }` envelope that Android Retrofit clients depend on.

### Phase 4 — Port Auth
Preserve JWT contract (same token format) so Android clients need no changes.
Use `djangorestframework-simplejwt` and map Google OAuth via existing `Authlib` flow.

### Phase 5 — Data Migration
Write a one-shot script to copy data from SQLite to PostgreSQL via the Django ORM.

### Phase 6 — Cut Over
- Update `Dockerfile` entrypoint to Django WSGI
- Add Postgres service to `docker-compose.yml`
- Remove Flask entrypoint and Alembic config
- Delete `_ensure_sync_events_schema()` tech-debt patch

---

## Key Constraints

- Android Retrofit clients must see **identical** `/api/v1` endpoints and response shapes
- All config via env vars — no hardcoded DB/credential values
- `SECRET_KEY` and `JWT_SECRET` env vars must map to Django `SECRET_KEY` and SimpleJWT config
- `DATABASE_URL` must be parseable by `dj-database-url` for Render/Railway/Fly compatibility

---

## Files to Keep / Delete

| File/Dir | Action |
|---|---|
| `backend/src/models/` | Replace with Django app models |
| `backend/src/api/v1/*.py` | Replace with DRF views |
| `backend/src/app.py` | Delete (Flask factory) |
| `backend/src/config/database.py` | Delete (SQLAlchemy session/engine) |
| `backend/alembic/` | Delete post-migration |
| `backend/src/services/` | Keep and adapt (minimal ORM dependency) |
| `backend/src/repositories/` | Replace with Django ORM queries |
| `backend/src/utils/` | Keep (logging, exceptions) |
| `backend/src/templates/` | Keep (adapt to Django template engine) |
| `backend/src/static/` | Keep (served by Django `staticfiles`) |
