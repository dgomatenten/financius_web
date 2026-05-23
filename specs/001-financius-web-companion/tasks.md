# Tasks: Financius Web - Data Management and Analytics Hub

**Input**: Design documents from `/specs/001-financius-web-companion/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: No explicit TDD/test-first requirement was requested in the specification. Validation and performance checks are included where they are required by measurable success criteria.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: [ID] [P?] [Story] Description

- [P] = Can run in parallel (different files, no dependency on incomplete tasks)
- [Story] = User story label (US1..US9)
- Every task includes an explicit target file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the Flask single-service project and its containerized runtime

- [x] T001 Update backend dependencies for Flask single-service delivery in backend/requirements.txt
- [x] T002 [P] Align backend container image build/runtime for Flask UI + API in infra/docker/backend.Dockerfile
- [x] T003 [P] Align backend-only Docker Compose topology in infra/compose/docker-compose.yml
- [x] T004 [P] Define Flask-only environment defaults in .env.example
- [x] T005 [P] Create Flask UI directory structure in backend/src/templates/ and backend/src/static/
- [x] T006 Configure local launcher scripts for Flask-only startup in scripts/run_services.sh and scripts/launch.sh

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core architecture and cross-cutting platform concerns required before all user stories

**Critical**: No user story work starts until this phase is complete

- [x] T007 Implement Flask app factory, template serving, and bootstrap wiring in backend/src/app.py
- [x] T008 [P] Implement centralized environment configuration loader in backend/src/config/settings.py
- [x] T009 [P] Implement SQLAlchemy engine/session setup in backend/src/config/database.py
- [x] T010 [P] Register ORM model exports for app startup and Alembic discovery in backend/src/models/__init__.py
- [x] T011 Implement API envelope helpers for `{ data, error, meta }` responses in backend/src/api/envelope.py
- [x] T012 Implement global exception mapping and structured error responses in backend/src/api/error_handler.py
- [x] T013 [P] Implement request correlation and structured logging utilities in backend/src/utils/logging.py
- [x] T014 [P] Implement JWT extraction and route auth helpers in backend/src/utils/auth.py
- [x] T015 Implement API v1 blueprint registration and route mounting in backend/src/api/v1/__init__.py
- [x] T016 [P] Add Alembic baseline and migration configuration in backend/alembic.ini and backend/alembic/env.py
- [x] T017 [P] Create shared Flask page shell and base assets in backend/src/templates/base.html and backend/src/static/css/app.css
- [x] T018 [P] Add backend quality tooling and pytest configuration in backend/pyproject.toml

**Checkpoint**: Foundation complete; user story implementation can now begin

---

## Phase 3: User Story 1 - Authenticated Access (Priority: P1)

**Goal**: Users can register and log in with email/password or Google and receive isolated refreshable sessions

**Independent Test**: Register a new account, log in, log out, log back in, and confirm one user cannot access another user's data

- [x] T019 [P] [US1] Implement User and RefreshToken ORM models in backend/src/models/user.py
- [x] T020 [P] [US1] Implement user lookup and persistence repository in backend/src/repositories/user_repository.py
- [x] T021 [P] [US1] Implement password hashing, JWT issuance, and refresh helpers in backend/src/services/auth_tokens.py
- [x] T022 [US1] Implement email/password auth and refresh rotation logic in backend/src/services/auth_service.py
- [x] T023 [US1] Implement Google OAuth verification and account-linking flow in backend/src/services/google_oauth_service.py
- [x] T024 [US1] Implement register/login/google/refresh routes in backend/src/api/v1/auth.py
- [x] T025 [US1] Implement Flask auth templates in backend/src/templates/auth/login.html and backend/src/templates/auth/register.html
- [x] T026 [US1] Implement client-side auth/session helpers in backend/src/static/js/auth.js and backend/src/static/js/session.js
- [x] T027 [US1] Implement authenticated landing/dashboard template in backend/src/templates/dashboard.html

**Checkpoint**: Auth-only vertical slice usable end-to-end

---

## Phase 4: User Story 2 - Android Data Sync (Priority: P2)

**Goal**: Android clients can sync data idempotently and web users can view sync status and pairing data

**Independent Test**: Submit a sample sync payload, verify persisted data and last-sync timestamp, then verify QR pairing payload generation

- [x] T028 [P] [US2] Implement SyncEvent and PairingToken ORM models in backend/src/models/sync_event.py and backend/src/models/pairing_token.py
- [x] T029 [P] [US2] Implement user-scoped sync upsert repository in backend/src/repositories/sync_repository.py
- [x] T030 [P] [US2] Implement pairing token repository in backend/src/repositories/pairing_repository.py
- [x] T031 [US2] Implement idempotent sync orchestration service in backend/src/services/sync_service.py
- [x] T032 [US2] Implement QR pairing token generation and validation service in backend/src/services/pairing_service.py
- [x] T033 [US2] Implement sync and pairing API routes in backend/src/api/v1/sync.py and backend/src/api/v1/pairing.py
- [x] T034 [US2] Implement sync status and pairing templates in backend/src/templates/sync/status.html and backend/src/templates/sync/pairing.html
- [x] T035 [US2] Implement sync status and pairing client scripts in backend/src/static/js/sync.js and backend/src/static/js/pairing.js

**Checkpoint**: Android-to-backend sync and pairing flow functional

---

## Phase 5: User Story 3 - Receipt & Transaction Management (Priority: P3)

**Goal**: Users can browse, filter, edit, bulk update, delete, and import receipts

**Independent Test**: With synced data present, search/filter receipts, edit one receipt, run a bulk action, and import Amazon CSV data

- [x] T036 [P] [US3] Implement Receipt and ReceiptLineItem ORM models in backend/src/models/receipt.py
- [x] T037 [P] [US3] Implement receipt pagination/search/filter repository in backend/src/repositories/receipt_repository.py
- [x] T038 [US3] Implement receipt read/update business logic in backend/src/services/receipt_service.py
- [x] T039 [US3] Implement receipt bulk operation service in backend/src/services/receipt_bulk_service.py
- [x] T040 [US3] Implement Amazon CSV parsing and receipt import service in backend/src/services/amazon_import_service.py
- [x] T041 [US3] Implement receipt list/detail/edit/bulk/import routes in backend/src/api/v1/receipts.py
- [x] T042 [US3] Implement receipt list and detail templates in backend/src/templates/receipts/list.html and backend/src/templates/receipts/detail.html
- [x] T043 [US3] Implement receipt filtering, bulk actions, and import scripts in backend/src/static/js/receipts.js and backend/src/static/js/receipt-import.js

**Checkpoint**: Receipt management slice independently usable

---

## Phase 6: User Story 4 - Master Data Management (Priority: P4)

**Goal**: Users can manage category hierarchy, shops, payment cards, and auto-category mappings

**Independent Test**: Create/edit/reorder categories, merge shops, manage cards, and correct one category mapping

- [x] T044 [P] [US4] Implement Category ORM model and hierarchy constraints in backend/src/models/category.py
- [x] T045 [P] [US4] Implement Shop, PaymentCard, and CategoryMapping ORM models in backend/src/models/master_data.py
- [x] T046 [US4] Implement category hierarchy and reassignment rules in backend/src/services/category_service.py
- [x] T047 [US4] Implement shop CRUD and merge logic in backend/src/services/shop_service.py
- [x] T048 [US4] Implement payment card CRUD and deactivation logic in backend/src/services/card_service.py
- [x] T049 [US4] Implement category mapping review and correction logic in backend/src/services/category_mapping_service.py
- [x] T050 [US4] Implement categories, shops, cards, and mappings routes in backend/src/api/v1/master_data.py
- [x] T051 [US4] Implement master-data templates and scripts in backend/src/templates/master_data/categories.html, backend/src/templates/master_data/shops.html, backend/src/templates/master_data/cards.html, and backend/src/static/js/master-data.js

**Checkpoint**: Master-data workflows independently usable

---

## Phase 7: User Story 5 - Budget Management (Priority: P5)

**Goal**: Users can configure total and per-category budgets with forecast and rollover support

**Independent Test**: Create manual and forecast-adjusted budgets with rollover enabled and verify progress values

- [x] T052 [P] [US5] Implement Budget ORM model in backend/src/models/budget.py
- [x] T053 [US5] Implement budget forecasting and rollover calculation logic in backend/src/services/budget_service.py
- [x] T054 [US5] Implement monthly budget progress aggregation in backend/src/services/budget_progress_service.py
- [x] T055 [US5] Implement budget list/upsert/progress routes in backend/src/api/v1/budgets.py
- [x] T056 [US5] Implement budget settings and overview templates in backend/src/templates/budgets/settings.html and backend/src/templates/budgets/overview.html
- [x] T057 [US5] Implement budget interaction scripts in backend/src/static/js/budgets.js

**Checkpoint**: Budget workflows independently usable

---

## Phase 8: User Story 6 - Analytics Dashboard (Priority: P6)

**Goal**: Users can view summary, category, calendar, year-over-year, benchmark, and insight analytics

**Independent Test**: Load the analytics dashboard, change period/currency filters, drill into a category, and confirm benchmarks/insights update

- [x] T058 [P] [US6] Implement analytics read-model repository in backend/src/repositories/analytics_repository.py
- [x] T059 [US6] Implement analytics summary, category, calendar, and year-over-year services in backend/src/services/analytics_service.py
- [x] T060 [P] [US6] Implement BLS benchmark service in backend/src/services/bls_benchmark_service.py
- [x] T061 [P] [US6] Implement 13-metric insights service in backend/src/services/insights_service.py
- [x] T062 [US6] Implement analytics routes in backend/src/api/v1/analytics.py
- [x] T063 [US6] Implement analytics dashboard template in backend/src/templates/analytics/dashboard.html
- [x] T064 [US6] Implement analytics filtering and chart interaction scripts in backend/src/static/js/analytics.js

**Checkpoint**: Analytics slice independently usable

---

## Phase 9: User Story 7 - Recurring Expenses (Priority: P7)

**Goal**: Users can manage recurring templates and track upcoming versus fulfilled occurrences

**Independent Test**: Create a recurring template, verify an upcoming occurrence appears, then match a synced receipt and verify fulfillment

- [ ] T065 [P] [US7] Implement recurring template and occurrence ORM models in backend/src/models/recurring.py
- [ ] T066 [US7] Implement recurring schedule and fulfillment matching logic in backend/src/services/recurring_service.py
- [ ] T067 [US7] Implement recurring routes in backend/src/api/v1/recurring.py
- [ ] T068 [US7] Implement recurring templates and status UI in backend/src/templates/recurring/index.html and backend/src/static/js/recurring.js

**Checkpoint**: Recurring expense slice independently usable

---

## Phase 10: User Story 8 - Amortization Rules (Priority: P8)

**Goal**: Users can create amortization rules and compare amortized versus cash spending

**Independent Test**: Create a linked amortization rule and verify its monthly projection appears alongside cash spending

- [ ] T069 [P] [US8] Implement amortization rule ORM model in backend/src/models/amortization.py
- [ ] T070 [US8] Implement amortization schedule generation and lifecycle logic in backend/src/services/amortization_service.py
- [ ] T071 [US8] Implement amortization routes in backend/src/api/v1/amortization.py
- [ ] T072 [US8] Implement amortization UI in backend/src/templates/amortization/index.html and backend/src/static/js/amortization.js

**Checkpoint**: Amortization slice independently usable

---

## Phase 11: User Story 9 - Data Export (Priority: P9)

**Goal**: Users can export filtered receipt data as JSON or CSV and get clear empty-result feedback

**Independent Test**: Export filtered JSON and CSV datasets and verify format, filters, and empty-result handling

- [ ] T073 [US9] Implement export query and serialization service in backend/src/services/export_service.py
- [ ] T074 [US9] Implement export routes and streamed responses in backend/src/api/v1/export.py
- [ ] T075 [US9] Implement export UI in backend/src/templates/export/index.html and backend/src/static/js/export.js

**Checkpoint**: Export slice independently usable

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Hardening, validation, and cross-story refinements

- [ ] T076 [P] Implement shared navigation, layout polish, and desktop-width safeguards across backend/src/templates/base.html and backend/src/static/css/app.css
- [ ] T077 [P] Add API error-code catalog and user-facing error copy in backend/src/api/error_codes.py and backend/src/static/js/session.js
- [ ] T078 [P] Add performance indexes and migration refinements in backend/alembic/versions/0002_performance_indexes.py
- [ ] T079 Add edge-case handling for concurrent sync, expired pairing, category reassignment, first-month forecast, and duplicate import in backend/src/services/sync_service.py, backend/src/services/pairing_service.py, backend/src/services/category_service.py, backend/src/services/budget_service.py, and backend/src/services/amazon_import_service.py
- [ ] T080 [P] Add contract and integration coverage for documented endpoint groups in backend/tests/contract/ and backend/tests/integration/
- [ ] T081 [P] Add measurable validation for SC-002 through SC-006 in backend/tests/integration/test_performance.py and specs/001-financius-web-companion/quickstart.md
- [ ] T082 Run Flask-only quickstart validation and record results in specs/001-financius-web-companion/quickstart.md
- [ ] T083 Final contract-to-implementation alignment pass against specs/001-financius-web-companion/contracts/openapi.yaml and backend/src/api/v1/

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1): no dependencies, can start immediately
- Foundational (Phase 2): depends on Setup completion and blocks all user stories
- User Stories (Phase 3 onward): all depend on Foundational completion
- Polish (Phase 12): depends on all targeted user stories being complete

### User Story Dependencies

- US1 (Auth): starts first after Foundational and is the MVP gate
- US2 (Sync): depends on US1 auth/session baseline
- US3 (Receipts): depends on US2 synced data and base entities
- US4 (Master Data): can start after US2 and should stay independently testable
- US5 (Budgets): depends on receipt/category availability from US3 and US4
- US6 (Analytics): depends on US3, US5, US7, and US8 data for full fidelity
- US7 (Recurring): depends on US3 and US4 entities
- US8 (Amortization): depends on US3 receipt data
- US9 (Export): depends on US3 receipt data and stable filters from adjacent stories

### Within Each User Story

- Models before repositories/services
- Repositories before orchestration services
- Services before API endpoints
- API endpoints before Flask UI integration
- Story validation before moving to the next priority story

### Parallel Opportunities

- Setup: T002, T003, T004, and T005 can run in parallel after T001 starts
- Foundational: T008, T009, T010, T013, T014, T016, T017, and T018 can run in parallel
- US1: T019, T020, and T021 can run in parallel before T022
- US2: T028, T029, and T030 can run in parallel before T031
- US3: T036 and T037 can run in parallel before T038
- US4: T044 and T045 can run in parallel before T046
- US5: T052 can run before T053 and T054
- US6: T060 and T061 can run in parallel once T058 is in place
- US7: T065 can run before T066
- US8: T069 can run before T070
- US9: T073 can run before T074 and T075
- Polish: T076, T077, T078, T080, and T081 can run in parallel after feature completion

---

## Parallel Example by User Story

### US1
- T019, T020, and T021 in parallel, then T022 and T023

### US2
- T028, T029, and T030 in parallel, then T031 and T032

### US3
- T036 and T037 in parallel, then T038, T039, and T040

### US4
- T044 and T045 in parallel, then T046 through T049

### US5
- T053 and T054 can run in parallel once T052 is complete

### US6
- T060 and T061 can run in parallel once T058 starts

### US7
- T067 and T068 can run in parallel after T066 is stable

### US8
- T071 and T072 can run in parallel after T070 is stable

### US9
- T074 and T075 can run in parallel after T073 is complete

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and validate auth flow, isolation, and refresh behavior before expanding scope

### Incremental Delivery

1. Add US2 so Android data reaches the web app
2. Add US3 and US4 for core data operations and reference management
3. Add US5 and US6 for budgeting and analytics depth
4. Add US7 and US8 for recurring and amortization behavior
5. Add US9 for export and data portability
6. Finish with Phase 12 validation against quickstart and success criteria

### Team Parallel Strategy

1. Team A: backend models, repositories, and services for current story
2. Team B: API routes and contract alignment for current story
3. Team C: Flask templates and static JavaScript/CSS for current story
4. Integrate and validate at each story checkpoint

---

## Notes

- All tasks follow the strict checklist format with ID, optional [P], and [USn] labels
- Story phases are ordered by priority from P1 through P9
- UI work is Flask-rendered and belongs under backend/src/templates/ and backend/src/static/
- Validation tasks cover quickstart behavior plus measurable success criteria where the spec requires them
- If dedicated story-level test-authoring tasks are later required, add them ahead of implementation tasks for that story
