# Phase 3 — Port Endpoints

## Status
[x] Complete | Date: 2026-05-29

## Goal
Convert every Flask Blueprint under `/api/v1` to a DRF ViewSet, preserving exact
request/response shapes for Android Retrofit client compatibility.

## Endpoints to port

| Flask blueprint | DRF View(s) | File | Status |
|---|---|---|---|
| `auth.py` | `RegisterView`, `LoginView`, `GoogleLoginView`, `RefreshView`, `LogoutView` | `accounts/views.py` | Done |
| `receipts.py` | `ReceiptListView`, `ReceiptDetailView`, `ReceiptBulkView`, `ReceiptAmazonImportView` | `ledger/views.py` | Done |
| `sync.py` | `SyncView`, `SyncStatusView` | `ledger/views.py` | Done |
| `master_data.py` | `CategoryListView`, `CategoryDetailView`, `ShopListView`, `ShopMergeView`, `CardListView`, `CardDetailView`, `CategoryMappingListView`, `CategoryMappingDetailView` | `ledger/views.py` | Done |
| `budgets.py` | `BudgetListView`, `BudgetProgressView` | `ledger/views.py` | Done |
| `pairing.py` | `PairingQRView`, `PairingValidateView` | `ledger/views.py` | Done |
| `analytics.py` | `AnalyticsSummaryView`, `AnalyticsCategoryBreakdownView`, `AnalyticsCalendarView`, `AnalyticsYoYView`, `AnalyticsBLSView`, `AnalyticsInsightsView` | `ledger/views.py` | Done |
| `recurring.py` | `RecurringListView` | `ledger/views.py` | Done |
| `export.py` | `ExportView` | `ledger/views.py` | Done |
| `amortization.py` | `AmortizationListView`, `AmortizationDetailView` | `ledger/views.py` | Done |

## Contract rule
Every response MUST match `{ data, error, meta }`. Contract tests in
`backend/tests/django/contract/` run against both Flask and Django and diff the shapes.

## Auth implementation notes

- JWT auth uses same `JWT_SECRET` env var and PyJWT as Flask — tokens are interchangeable
- `JWTAuthentication` DRF class in `accounts/auth.py` decodes Bearer tokens for all protected endpoints
- Refresh endpoint preserves Flask's top-level alias fields (`access_token`, `refresh_token`, `expires_in`) for Android backward compatibility
- Google OAuth verified via `googleapis.com/tokeninfo` — same as Flask

## Sync implementation notes

- `_normalise_sync_payload` is a direct port of Flask `sync.py`'s `_normalise_payload`
- `_upsert_*` functions port `SyncRepository` to Django ORM (`get_or_create` + bulk update)
- Auto-creates stub shops/categories/cards when external_id references missing master data
- Wrapped in `transaction.atomic()` — entire sync either commits or rolls back

## Known limitations / Phase 4 work

| Endpoint | Flask behaviour | Django status |
|---|---|---|
| `POST /receipts/import/amazon` | Parses CSV, creates receipts | Returns stub (not yet ported) |
| `GET /analytics/benchmarks/bls` | BLS data comparison | Returns empty (data not available) |
| Budget `forecast`/`forecast_adjusted` modes | Full trailing-average | Ported |

## Checklist
- [x] All views created
- [x] URLs registered under `/api/v1/`
- [x] JWT authentication class (`accounts/auth.py`) wired into `REST_FRAMEWORK`
- [x] `python3 manage.py check` — 0 issues
- [x] All 21 API paths resolve correctly
- [x] 70 Django unit tests passing, 2 contract stubs skipped
- [x] Contract test stubs activated — 9 Django contract tests + 5 Flask baselines = 14 passing
- [x] `financius_web/exception_handler.py` — all DRF errors wrapped in `{ data, error, meta }` envelope
