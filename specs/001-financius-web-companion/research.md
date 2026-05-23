# Research: Financius Web

## Decision 1: API response contract envelope
- Decision: Use one canonical envelope for every API response:
  `{ "data": <payload|null>, "error": <error-object|null>, "meta": <object> }`.
- Rationale: Enforces stable parsing for Android Retrofit and web clients,
  simplifies error handling, and satisfies constitution Principle III.
- Alternatives considered:
  - Raw endpoint-specific JSON: rejected due to inconsistent client parsing.
  - GraphQL-style error array: rejected to avoid added complexity and dependency overhead.

## Decision 2: Versioned route strategy
- Decision: Keep all endpoints under `/api/v1/*`; future breaking changes move
  to `/api/v2/*` while keeping v1 active during migration windows.
- Rationale: Protects Android compatibility and formalizes contract evolution.
- Alternatives considered:
  - Unversioned routes: rejected due to high breakage risk.
  - Date-versioned routes: rejected for unnecessary complexity at current scale.

## Decision 3: Sync idempotency and conflict handling
- Decision: Use user-scoped, client-generated receipt/transaction external IDs with
  upsert semantics; record sync events in `sync_events`; apply last-write-wins for
  concurrent updates on same external ID.
- Rationale: Matches existing assumptions and supports repeat sync retries safely.
- Alternatives considered:
  - Server-only IDs with dedupe by fuzzy matching: rejected as unreliable.
  - Strict optimistic locking requiring manual conflict resolution: rejected for v1 UX complexity.

## Decision 4: Storage and migration path
- Decision: Use SQLAlchemy ORM with Alembic migrations targeting SQLite initially,
  constrained to PostgreSQL-compatible schema patterns.
- Rationale: Preserves local simplicity while enabling low-risk production migration.
- Alternatives considered:
  - Raw SQL: rejected by constitution and maintainability risk.
  - PostgreSQL-only now: rejected for unnecessary early operational cost.

## Decision 5: Authentication implementation
- Decision: Email/password and Google OAuth login with short-lived JWT access token
  and rotating refresh token persisted server-side.
- Rationale: Meets FR-001..FR-004 while supporting Android/web auth parity.
- Alternatives considered:
  - Session-cookie only auth: rejected due to Android API integration requirements.
  - Non-rotating refresh tokens: rejected due to weaker security posture.

## Decision 6: Backend technology boundaries
- Decision: Flask app with modular blueprints by bounded endpoint groups
  (`auth`, `sync`, `receipts`, `categories`, `analytics`, etc.) and a shared
  response/envelope utility.
- Rationale: Keeps dependency footprint low while maintaining clean boundaries.
- Alternatives considered:
  - Full async framework migration: rejected as unnecessary for initial scale.
  - Monolithic single-route module: rejected for maintainability issues.

## Decision 7: UI architecture
- Decision: Flask-rendered templates plus lightweight static JavaScript/CSS served by the
  backend single service.
- Rationale: Reduces operational complexity, avoids dual-runtime drift, and keeps UI/API
  changes in one deployable unit.
- Alternatives considered:
  - Legacy SPA client stack: retired after migration to Flask-only runtime.
  - Heavy enterprise framework: rejected by minimal-dependencies principle.

## Decision 8: Charting and analytics rendering
- Decision: Use one lightweight charting library (Recharts) for pie/bar/trend and
  a custom calendar heat-map component for spending calendar.
- Rationale: Covers required visualizations without large visualization stack overhead.
- Alternatives considered:
  - Multiple chart libs: rejected due to bundle bloat.
  - Fully custom SVG charts: rejected due to implementation time and risk.

## Decision 9: Export format behavior
- Decision: Implement synchronous export for typical ranges with streamed response;
  return user-facing "no matching data" error envelope when filters produce zero rows.
- Rationale: Meets FR-040..FR-042 and SC-006 while avoiding premature background job system.
- Alternatives considered:
  - Async job queue for all exports: rejected as over-engineering for v1.

## Decision 10: Deployment portability posture
- Decision: Standardize on Dockerfiles + compose with environment-driven runtime and
  no cloud-specific code paths; deployment adapters remain external (App Runner/Render/etc.).
- Rationale: Direct constitution compliance and simpler migration between low-cost platforms.
- Alternatives considered:
  - App Runner-only assumptions in app code: rejected due to lock-in.

## Decision 11: Error handling and logging baseline
- Decision: Every endpoint wraps service execution with standardized exception mapping
  to envelope errors and structured logging with request/user correlation IDs.
- Rationale: Improves debuggability and guarantees safe, consistent client errors.
- Alternatives considered:
  - Per-handler ad hoc error responses: rejected for inconsistency risk.

## Decision 12: QR pairing flow
- Decision: Web app emits QR payload containing `server_base_url` and a short-lived,
  single-use pairing token; Android exchanges pairing token for standard auth flow.
- Rationale: Minimizes manual setup and keeps long-lived credentials out of QR payload.
- Alternatives considered:
  - Embedding long-lived API tokens in QR: rejected for security risk.
