# Feature Specification: Financius Web — Data Management and Analytics Hub

**Feature Branch**: `001-financius-web-companion`

**Created**: 2026-05-16

**Status**: Draft

---

## User Scenarios & Testing

<!--
  User stories are ordered by delivery priority. Each represents a testable,
  independently valuable slice of the product that can be built, demoed, and
  shipped without requiring later stories to be complete.
-->

### User Story 1 — Authenticated Access (Priority: P1)

A user can create an account and sign in using either email + password or their
Google account. Each user's data is fully isolated from other users. Session tokens
expire and are refreshable without requiring re-login.

**Why this priority**: Authentication is the gateway to every other feature. No
other story is functional until a user can securely identify themselves and own
their data.

**Independent Test**: Register a new account, log in, view the empty dashboard,
log out, log back in. Verify no data bleeds between two different accounts.

**Acceptance Scenarios**:

1. **Given** a new visitor, **When** they register with a valid email and password,
   **Then** an account is created and they are redirected to the dashboard.
2. **Given** a registered user, **When** they sign in with correct credentials,
   **Then** they receive a valid session and see their personal data.
3. **Given** a registered user, **When** they click "Sign in with Google" and
   authorize the app, **Then** they are authenticated using their Google identity
   and land on the dashboard.
4. **Given** a logged-in user, **When** their access token expires, **Then** the
   system transparently refreshes the token without interrupting their session.
5. **Given** two users, **When** each is logged in, **Then** neither can access
   the other user's receipts, categories, or any other data.

---

### User Story 2 — Android Data Sync (Priority: P2)

The Financius Android app pushes receipts, transactions, and master data to the
Flask backend via REST API. The Flask app shows when data was last synced from
the user's device and accepts new data without creating conflicts.

**Why this priority**: The Flask app has no value to Android users unless their
data appears in it. Sync is the core data pipeline that all other stories consume.

**Independent Test**: Use a REST client to push a sample sync payload to the API
while logged in, then verify the synced records appear in the Flask UI and the
last-sync timestamp is updated.

**Acceptance Scenarios**:

1. **Given** an authenticated Android app, **When** it sends a sync payload of
   receipts and master data, **Then** the server accepts the data and returns a
   success response with accepted record counts.
2. **Given** synced data already exists, **When** the Android app sends the same
   records again (idempotent re-sync), **Then** no duplicate records are created.
3. **Given** a logged-in Flask user, **When** they view the dashboard, **Then**
   they see the date and time of the most recent sync from their Android device.
4. **Given** the Android user wants to connect a new device to their web account,
  **When** they scan the QR code displayed on the Flask app's pairing page,
   **Then** the Android app is configured with the correct server URL and
   authenticated for sync without manual entry.

---

### User Story 3 — Receipt & Transaction Management (Priority: P3)

A user can browse all receipts synced from their Android app, search and filter
them, view individual line items, edit receipt details, perform bulk operations
across multiple receipts, and import receipts from Amazon order CSV exports.

**Why this priority**: Receipts are the primary data entity. Users opened the
Flask app specifically to manage receipts at scale, which the phone screen makes
difficult.

**Independent Test**: With at least 20 synced receipts present, search for a
shop name, filter by category, open a receipt to see its line items, edit a
field, then bulk re-categorize three receipts at once. Verify all changes persist.

**Acceptance Scenarios**:

1. **Given** synced receipts exist, **When** the user opens the receipts list,
   **Then** receipts are shown paginated with date, shop, total, currency, and
   category.
2. **Given** a receipts list, **When** the user types a search term,
   **Then** receipts matching shop name, category, or notes are filtered in
   real-time.
3. **Given** a receipts list, **When** the user applies filters for date range,
   category, currency, or payment card, **Then** only matching receipts are shown.
4. **Given** a receipt with line items, **When** the user opens it,
   **Then** individual products, quantities, and prices are displayed.
5. **Given** an open receipt, **When** the user edits the category, notes, or
   payment card and saves, **Then** the changes are persisted and reflected
   immediately.
6. **Given** a receipts list, **When** the user selects multiple receipts and
   chooses bulk re-categorize, **Then** all selected receipts are updated to
   the chosen category in a single operation.
7. **Given** the receipts list, **When** the user selects multiple receipts and
   chooses bulk delete, **Then** they are prompted to confirm, and upon
   confirmation all selected receipts are removed.
8. **Given** an Amazon order export CSV, **When** the user uploads it via the
   import page, **Then** orders are parsed and saved as receipts with correct
   dates, items, and amounts.

---

### User Story 4 — Master Data Management (Priority: P4)

A user can manage all reference data that the Android app relies on: the category
hierarchy, shops, payment cards, and AI auto-categorization mappings.

**Why this priority**: Master data accuracy directly affects receipt quality across
all other features. The web's larger surface area makes hierarchy editing and
bulk corrections far more practical than the phone.

**Independent Test**: Create a new parent category, add a child category with all
flags set, rename a shop, merge two duplicate shops, add a payment card, then
review and correct one category mapping. Verify all changes are reflected in
subsequent Android syncs.

**Acceptance Scenarios**:

1. **Given** the categories page, **When** the user creates a new parent
   category with Engel coefficient, needs/wants, housing, and fixed-expense
   flags configured, **Then** the category is saved and appears in the hierarchy.
2. **Given** an existing category, **When** the user nests it under a different
   parent or reorders it in the hierarchy, **Then** the new position is saved
   and the change propagates to all associated receipts.
3. **Given** two duplicate shops, **When** the user selects merge and picks a
   primary shop, **Then** all receipts previously assigned to the secondary shop
   are reassigned to the primary, and the secondary is removed.
4. **Given** the shops page, **When** the user edits a shop's name, address,
   or default category, **Then** the changes are saved and reflected in existing
   receipts from that shop.
5. **Given** the payment cards page, **When** the user adds a new card with
   type (credit/debit/prepaid/digital wallet), color code, and card network,
   **Then** the card is available for receipt assignment.
6. **Given** an existing payment card, **When** the user deactivates it,
   **Then** it no longer appears as an option for new receipts but existing
   records remain unchanged.
7. **Given** the category mappings page, **When** the user views the
   auto-categorization rules and corrects an incorrect mapping,
   **Then** the corrected rule is saved and will be applied to future receipts
   from that shop.

---

### User Story 5 — Budget Management (Priority: P5)

A user can set monthly spending budgets at both total and per-category level,
choose from multiple budget calculation modes, enable rollover, and monitor
their current-month spending progress against budget.

**Why this priority**: Budgets transform analytics from observation to action.
This is a key feature differentiating Financius from plain expense tracking.

**Independent Test**: Set a total monthly budget of $2,000, set a $300 budget
for Dining using forecast mode at 90%, enable rollover, then view the current
month's progress and confirm the rollover amount from the prior month is
reflected.

**Acceptance Scenarios**:

1. **Given** the budget settings page, **When** the user enters a total monthly
   budget amount and saves, **Then** the budget is applied to the current and
   future months.
2. **Given** a category budget form, **When** the user selects forecast-based
   mode with a 95% adjustment, **Then** the system calculates the budget as
   95% of the trailing average spend for that category.
3. **Given** a month with a budget surplus, **When** rollover is enabled and
   the next month begins, **Then** the surplus is added to the next month's
   available budget for that category.
4. **Given** a month with a budget deficit, **When** rollover is enabled,
   **Then** the deficit is subtracted from the next month's budget.
5. **Given** the budget overview page, **When** the user views it mid-month,
   **Then** they see each category's budget amount, amount spent, amount
   remaining, and a visual progress indicator.

---

### User Story 6 — Analytics Dashboard (Priority: P6)

A user can view spending analytics including summary metrics, category
breakdowns with drill-down, a daily spending heat-map, year-over-year
comparisons, BLS benchmark comparisons, and 13 spending insight metrics.
All views are filterable by currency and time period.

**Why this priority**: Analytics is the primary discovery value of the Flask app —
the "aha" feature that motivates users to adopt the companion beyond just
management tasks.

**Independent Test**: With at least 3 months of synced spending data, open the
Flask analytics dashboard, filter to "Last 3 months" in USD, drill into the Dining
category, switch to the calendar heat-map view, and confirm the BLS benchmark
comparison panel loads with color-coded over/under indicators.

**Acceptance Scenarios**:

1. **Given** the analytics dashboard, **When** the user views the summary panel,
   **Then** they see total spending, month-over-month change percentage, receipt
   count, top 5 categories, and top 5 shops for the selected period.
2. **Given** the category breakdown view, **When** the user clicks a parent
   category in the chart, **Then** the view drills into that category's
   sub-categories with updated chart and amounts.
3. **Given** the spending calendar view, **When** the user views a month,
   **Then** each day is color-coded by spending intensity relative to their daily
   average, and clicking a day shows the receipts for that day.
4. **Given** the year-over-year comparison view, **When** the user selects a
   category, **Then** they see the per-category spending change as a percentage
   from the same period in the prior year.
5. **Given** the BLS benchmark panel, **When** the user views it,
   **Then** their spending per category is shown alongside the US national
   Consumer Expenditure Survey average, with color-coded over/under indicators.
6. **Given** the insights panel, **When** the user views it, **Then** they see
   the 13 spending insight metrics including: category trend deviation, daily
   average, weekend vs weekday ratio, zero-spend days count, Engel coefficient,
   saving rate estimate, fixed expense ratio, 50/30/20 budget rule compliance,
   housing ratio, and remaining applicable metrics.
7. **Given** any analytics view, **When** the user changes the currency filter
   or time period selector, **Then** all panels and charts update to reflect
   the new filter without a full page reload.

---

### User Story 7 — Recurring Expenses (Priority: P7)

A user can create and manage recurring expense templates for subscriptions, rent,
and utilities, and track which scheduled expenses have generated receipts and
which are upcoming.

**Why this priority**: Recurring expenses represent committed spending that users
want to verify against actual receipts without manual searching each month.

**Independent Test**: Create a monthly "Netflix" recurring expense template for
$15.99 in the Entertainment category, then verify it appears in the upcoming
expenses list and — after syncing a matching receipt — it shows as fulfilled.

**Acceptance Scenarios**:

1. **Given** the recurring expenses page, **When** the user creates a template
   with name, amount, category, frequency (monthly/weekly/yearly), and start
   date, **Then** the template is saved and the next occurrence is calculated.
2. **Given** existing recurring templates, **When** the current date is within
   the expected window for an occurrence, **Then** the expense is shown as
   "upcoming" with days remaining.
3. **Given** a recurring expense with an upcoming occurrence, **When** a
   matching receipt is synced from the Android app, **Then** the occurrence
   status changes from "upcoming" to "fulfilled" with a link to the receipt.
4. **Given** an existing template, **When** the user deactivates it,
   **Then** no further occurrences are generated but historical records remain.

---

### User Story 8 — Amortization Rules (Priority: P8)

A user can create rules that spread the cost of a large one-time purchase across
several months, view the amortized monthly cost alongside actual cash spending,
and manage active and completed rules.

**Why this priority**: Amortization gives users a truer picture of their monthly
cost of living for large purchases (appliances, electronics, annual subscriptions
paid upfront).

**Independent Test**: Create an amortization rule for a $1,200 laptop spread over
12 months, link it to the corresponding receipt, then verify the analytics
dashboard shows $100/month amortized cost alongside the actual $1,200 cash
entry.

**Acceptance Scenarios**:

1. **Given** the amortization rules page, **When** the user creates a rule with
   total amount, number of months, start month, and an optional linked receipt,
   **Then** the monthly amortized amount is calculated and the rule is saved.
2. **Given** an active rule, **When** the user views the amortization detail,
   **Then** they see the amortized monthly cost and the actual cash spending
   side-by-side for each month in the rule's span.
3. **Given** a rule whose span has elapsed, **When** the user views the rules
   list, **Then** the rule appears in the "completed" section.
4. **Given** an active rule, **When** the user deletes it, **Then** they are
   warned that amortized monthly figures will be removed from analytics, and
   upon confirmation the rule is deleted.

---

### User Story 9 — Data Export (Priority: P9)

A user can export their receipts and analytics data as JSON (full backup) or
CSV, filtered by date range, category, and currency.

**Why this priority**: Export is an essential data ownership feature that
prevents vendor lock-in and enables external analysis.

**Independent Test**: Export all receipts from the last 3 months in the
Dining category as CSV, then verify the downloaded file contains the expected
columns and row count.

**Acceptance Scenarios**:

1. **Given** the export page, **When** the user selects format (JSON or CSV),
   date range, category, and currency filters, then clicks Export,
   **Then** a file download begins containing only the matching records.
2. **Given** a JSON export, **When** the user downloads and inspects it,
   **Then** the file contains all receipt fields including line items, metadata,
   and category assignments — suitable for a full backup and re-import.
3. **Given** a CSV export, **When** the user downloads it, **Then** each row
   represents one receipt with flat columns for date, shop, total, currency,
   category, and payment method.
4. **Given** an export request with no matching records, **When** the user
   initiates it, **Then** they receive a clear message that no data matches the
   selected filters before any download attempt.

---

### Edge Cases

- What happens when the Android app attempts to sync while another sync from
  the same account is already in progress?
- How does the system handle a receipt with no matching shop or category in the
  current master data (e.g., after a shop merge)?
- What happens when a user attempts to delete a category that has receipts
  assigned to it?
- How does the budget calculation behave in the first month of use when there
  is no trailing history for forecast mode?
- What happens when a QR code pairing link is accessed after the short-lived
  pairing token has expired?
- What happens when an Amazon CSV import contains rows that duplicate
  already-synced receipts?

---

## Requirements

### Functional Requirements

**Authentication and Authorization**

- **FR-001**: Users MUST be able to register with a unique email address and
  a password meeting minimum strength requirements.
- **FR-002**: Users MUST be able to authenticate via Google OAuth using the same
  Google account identity used by the Financius Android app.
- **FR-003**: All session management MUST use JWT access tokens with a refresh
  token mechanism; access tokens expire within one hour.
- **FR-004**: Each user's data MUST be fully isolated; cross-user data access
  MUST be rejected at the authorization layer.

**Android Data Sync**

- **FR-005**: The API MUST expose a sync endpoint under `/api/v1/sync` that
  accepts batched receipts, transactions, and master data payloads from the
  Android app.
- **FR-006**: Sync operations MUST be idempotent — re-sending the same records
  MUST NOT create duplicates.
- **FR-007**: The system MUST record the timestamp of the most recent successful
  sync per user and expose it in the API and Flask UI.
- **FR-008**: The Flask app MUST display a QR code on the pairing page that
  encodes the server URL and a short-lived pairing token so the Android app can
  auto-configure its sync endpoint.

**Receipt & Transaction Management**

- **FR-009**: Users MUST be able to view a paginated list of all their receipts
  sortable by date, total, and shop name.
- **FR-010**: Users MUST be able to search receipts by shop name, category name,
  and notes text.
- **FR-011**: Users MUST be able to filter receipts by date range, category,
  currency, and payment card.
- **FR-012**: Users MUST be able to view all line items (products, quantities,
  prices) for any individual receipt.
- **FR-013**: Users MUST be able to edit a receipt's category, notes, and
  payment card assignment.
- **FR-014**: Users MUST be able to perform bulk re-categorize, bulk payment-card
  reassignment, and bulk delete across a selected set of receipts.
- **FR-015**: Users MUST be able to import receipts from an Amazon order CSV
  export file; the system MUST parse order date, items, prices, and total.

**Master Data Management**

- **FR-016**: Users MUST be able to create, rename, reorder, nest, and delete
  categories in a parent/child hierarchy.
- **FR-017**: Each category MUST support four boolean flags: Engel coefficient,
  needs/wants classification, housing flag, and fixed-expense flag.
- **FR-018**: Deleting a category that has receipts assigned to it MUST require
  the user to reassign those receipts to another category before the deletion
  is allowed.
- **FR-019**: Users MUST be able to view all shops, edit their name and address,
  change their default category, and merge two shops into one.
- **FR-020**: Shop merge MUST reassign all receipts from the secondary shop to
  the primary shop and remove the secondary.
- **FR-021**: Users MUST be able to add, edit, and deactivate payment cards
  with type (credit/debit/prepaid/digital wallet), color code, and card network.
- **FR-022**: Users MUST be able to view and edit the AI auto-categorization
  mapping rules (shop → category associations learned by the Android scanner).

**Budget Management**

- **FR-023**: Users MUST be able to set a total monthly budget amount.
- **FR-024**: Users MUST be able to set per-category monthly budgets with three
  modes: manual amount, forecast-based (trailing average), and forecast with a
  percentage adjustment between 80% and 120%.
- **FR-025**: Users MUST be able to enable or disable surplus/deficit rollover
  per category budget.
- **FR-026**: The budget overview page MUST show, for each category: budget
  amount, amount spent, amount remaining, and a visual progress indicator.

**Recurring Expenses**

- **FR-027**: Users MUST be able to create recurring expense templates with
  name, amount, category, frequency (daily/weekly/monthly/yearly), and start
  date.
- **FR-028**: The system MUST calculate the next expected occurrence for each
  active template and display it as "upcoming" when within the expected window.
- **FR-029**: When a receipt matching a recurring template (by category and
  approximate amount within ±10%) is synced, the system MUST mark the
  nearest upcoming occurrence as fulfilled and link it to that receipt.

**Amortization Rules**

- **FR-030**: Users MUST be able to create an amortization rule specifying total
  amount, number of months, start month, and an optional linked receipt.
- **FR-031**: The amortization detail view MUST show the calculated monthly
  amortized cost alongside the actual cash spending for each month in the rule's
  span.
- **FR-032**: Rules whose full span has elapsed MUST be automatically moved to a
  "completed" state.

**Analytics Dashboard**

- **FR-033**: The summary panel MUST display total spending, month-over-month
  percentage change, receipt count, top 5 categories by spend, and top 5 shops
  by spend for the selected filter period.
- **FR-034**: The category breakdown MUST render as a pie and/or bar chart with
  drill-down support to sub-categories.
- **FR-035**: The spending calendar MUST render a monthly heat-map where each
  day is color-coded by spending intensity; clicking a day shows that day's
  receipts.
- **FR-036**: The year-over-year comparison MUST show per-category spending
  change as a percentage from the same period in the prior year.
- **FR-037**: The BLS benchmark panel MUST compare the user's category spending
  against bundled US Consumer Expenditure Survey averages with color-coded
  over/under indicators.
- **FR-038**: The insights panel MUST compute and display all 13 spending insight
  metrics: category trend deviation, daily average spend, weekend vs weekday
  ratio, zero-spend days count, Engel coefficient, saving rate estimate, fixed
  expense ratio, 50/30/20 budget rule compliance, housing ratio, top recurring
  spend category, largest single expense, average receipt size, and most
  frequent shop.
- **FR-039**: All analytics views MUST support filtering by currency (USD/JPY/EUR/
  GBP/KRW/CNY/CAD/AUD) and time period (this month, last month, 3/6/12 months,
  year-to-date, and custom date range).

**Data Export**

- **FR-040**: Users MUST be able to export filtered receipt data as JSON or CSV,
  with filters for date range, category, and currency.
- **FR-041**: JSON export MUST include all receipt fields, line items, and
  metadata sufficient for a full re-import (backup format).
- **FR-042**: CSV export MUST produce one row per receipt with flat columns for
  date, shop, total, currency, category path, and payment method.

### Key Entities

- **User**: Account holder; owns all data below. Attributes: email, hashed
  credential, Google identity reference, last-sync timestamp.
- **Receipt**: A single shopping or payment event synced from Android. Attributes:
  date, shop reference, total, currency, notes, payment card reference, category
  reference, sync source.
- **ReceiptLineItem**: One product or service within a receipt. Attributes:
  receipt reference, name, quantity, unit price, subtotal.
- **Category**: Hierarchical spending classification. Attributes: name, parent
  reference, display order, Engel flag, needs/wants flag, housing flag,
  fixed-expense flag.
- **Shop**: A merchant or payee. Attributes: name, address, default category
  reference.
- **CategoryMapping**: Auto-categorization rule. Attributes: shop reference,
  category reference, confidence score, source (AI/user-corrected).
- **PaymentCard**: A payment instrument. Attributes: name, type, color code,
  card network, active flag.
- **Budget**: Monthly budget entry. Attributes: user, category reference (null =
  total), month, mode, amount, rollover flag.
- **RecurringExpense**: Template for expected repeated spending. Attributes: name,
  amount, category, frequency, start date, active flag.
- **AmortizationRule**: Spread-cost rule. Attributes: total amount, months,
  start month, linked receipt reference, active/completed flag.
- **SyncEvent**: Record of an Android sync operation. Attributes: user, device
  identifier, timestamp, record counts.

### Constitution Alignment *(mandatory)*

- **CA-001**: Environment variables required by this feature: `DATABASE_URL`,
  `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`,
  `JWT_SECRET`, `ALLOWED_ORIGINS`, `QR_PAIRING_TOKEN_TTL_SECONDS`.
  No hardcoded cloud-provider values permitted.
- **CA-002**: All REST endpoints under `/api/v1`; every response uses
  `{ data, error, meta }` envelope. Affected endpoint groups: `/api/v1/sync`,
  `/api/v1/receipts`, `/api/v1/categories`, `/api/v1/shops`,
  `/api/v1/cards`, `/api/v1/budgets`, `/api/v1/recurring`,
  `/api/v1/amortization`, `/api/v1/analytics`, `/api/v1/export`,
  `/api/v1/auth`.
- **CA-003**: All data persistence through SQLAlchemy ORM models; no raw SQL
  outside of ORM-generated queries. Schema designed for PostgreSQL compatibility
  (no SQLite-only types or pragmas in ORM models).
- **CA-004**: Every endpoint handler must use try/except, log the exception with
  request context, and return a structured error response within the standard
  envelope. Secrets and tokens MUST NOT appear in log output.
- **CA-005**: All backend Python files must follow PEP 8 with function-level
  type hints. Dependency additions must be justified by a direct product
  requirement.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: A user who already uses the Financius Android app can complete the
  full onboarding flow (register, pair device, view synced receipts) in under
  5 minutes.
- **SC-002**: The analytics dashboard loads all panels for a user with 12 months
  of data within 3 seconds on a standard broadband connection.
- **SC-003**: Bulk operations on up to 200 receipts complete within 5 seconds
  from submission to confirmed result.
- **SC-004**: The Android sync endpoint accepts and processes a standard monthly
  payload (up to 500 receipts, 2,000 line items) within 10 seconds.
- **SC-005**: All pages are usable on screen widths from 1024px upward without
  horizontal scrolling or truncated controls.
- **SC-006**: Data export for up to 12 months of receipts completes and triggers
  a download within 15 seconds.
- **SC-007**: 100% of API endpoints return structured error responses within the
  standard envelope — no unhandled exceptions surface raw error messages to
  clients.

---

## Assumptions

- The Financius Android app is the only data-entry point; the Flask app is
  read-heavy with selective edit/management operations.
- BLS Consumer Expenditure Survey benchmark data is bundled as a static asset
  in the application and updated by developers when new survey data is released
  (no external API dependency at runtime).
- QR code pairing encodes the server base URL and a short-lived single-use
  token; the Android app then uses its own OAuth credentials for all subsequent
  sync requests.
- A single user account may be paired with more than one Android device, but
  conflict resolution for simultaneous sync is handled by last-write-wins on
  the receipt identifier.
- Amazon CSV import uses the standard Amazon order history export format
  (as of 2025); format changes will require a maintenance update.
- Recurring expense fulfillment matching uses category and amount (±10%)
  as the matching signal; more sophisticated matching is out of scope for v1.
- The 13 spending insight metrics are calculated server-side and cached per
  user per time period for performance; stale cache is acceptable up to 15
  minutes.
- Multi-language and multi-timezone support are out of scope; dates are stored
  as UTC and displayed in the browser's local timezone.
- Team/sharing features (multiple users accessing the same account) are out of
  scope.
- Mobile-browser responsiveness below 1024px is a nice-to-have; the primary
  target is desktop/laptop browsers.
