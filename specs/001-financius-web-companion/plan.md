# Implementation Plan: Financius Web - Data Management and Analytics Hub

**Branch**: `001-financius-web-companion` | **Date**: 2026-05-16 | **Spec**: `/specs/001-financius-web-companion/spec.md`

**Input**: Feature specification from `/specs/001-financius-web-companion/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a Docker-first web companion platform for existing Financius Android users, with
Flask REST APIs and Flask-rendered UI templates. The Android app remains the primary data-entry
client and syncs to this backend through versioned `/api/v1` endpoints. The web app
provides master-data management, receipt operations, budgeting, recurring/amortization
workflows, analytics, and export while enforcing a stable response envelope
`{ data, error, meta }`, strict per-user data isolation, and environment-driven
configuration for portability across AWS App Runner and low-cost alternatives.

## Technical Context

**Language/Version**: Python 3.12 (Flask API + server-rendered UI)

**Primary Dependencies**: Flask, SQLAlchemy, Alembic, PyJWT, Authlib (Google OAuth),
Pydantic (request/response validation), pytest

**Storage**: SQLite (current), migration-ready for PostgreSQL via SQLAlchemy + Alembic

**Testing**: pytest (unit/integration/contract)

**Target Platform**: Linux containers (Docker), modern desktop browsers, Android API consumer

**Project Type**: Web application (Flask single-service UI + API)

**Performance Goals**:
- Analytics dashboard response p95 <= 3s for 12-month data window
- Sync payload processing <= 10s for 500 receipts / 2,000 line items
- Bulk receipt operations <= 5s for up to 200 selected receipts
- Export generation <= 15s for up to 12 months of data

**Constraints**:
- All APIs under `/api/v1` with `{ data, error, meta }` response envelope
- Config and secrets via environment variables only
- Minimize dependencies; avoid premature microservice decomposition
- Exception-safe handlers with structured logging and no secret leakage
- Docker execution required for local dev, CI, and deployment

**Scale/Scope**:
- Single-user-per-account model; no team-sharing
- Up to low tens of thousands of users in initial deployment horizon
- 9 major product areas, 42 functional requirements, Android + web clients

## Constitution Check (Pre-Design)

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Container portability gate: Confirm all impacted services run via Docker and do not
  introduce platform lock-in.
  - PASS: Backend application and launcher tooling are defined as containerized or
    container-compatible services.
- Configuration gate: Confirm all new configuration is environment-variable driven with
  no hardcoded cloud/provider values.
  - PASS: Required environment variable set defined in spec CA-001.
- API contract gate: Confirm REST endpoints are under `/api/v1` and responses follow
  `{ data, error, meta }`.
  - PASS: API namespace and envelope are first-class requirements (FR-005, CA-002).
- Data layer gate: Confirm data access uses SQLAlchemy ORM with SQLite-compatible design
  and PostgreSQL migration readiness.
  - PASS: SQLAlchemy + Alembic selected; SQLite-now/PostgreSQL-later path preserved.
- Quality gate: Confirm PEP 8 compliance plan, function type hints, and graceful
  exception handling/logging strategy for all endpoints.
  - PASS: Quality rules codified in constitution principle V and CA-004/CA-005.

## Project Structure

### Documentation (this feature)

```text
specs/001-financius-web-companion/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/
│   └── openapi.yaml     # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
```text
backend/
├── src/
│   ├── app.py
│   ├── config/
│   ├── models/
│   ├── services/
│   ├── repositories/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── sync.py
│   │   │   ├── receipts.py
│   │   │   ├── categories.py
│   │   │   ├── shops.py
│   │   │   ├── cards.py
│   │   │   ├── budgets.py
│   │   │   ├── recurring.py
│   │   │   ├── amortization.py
│   │   │   ├── analytics.py
│   │   │   └── export.py
│   │   └── envelope.py
│   └── utils/
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

infra/
├── docker/
│   └── backend.Dockerfile
└── compose/
    └── docker-compose.yml
```

**Structure Decision**: Use a Flask single-service architecture where both API and UI are
served from `backend/`, keeping Android integration focused in backend v1 routes and
minimizing deployment/runtime complexity.

## Phase 0: Research Summary

- Completed in `research.md` with concrete decisions for API contract envelope,
  sync idempotency, SQLAlchemy modeling strategy, auth/token approach, charting strategy,
  Docker/deployment portability, and observability baseline.
- All potential `NEEDS CLARIFICATION` areas are resolved through explicit assumptions
  and decisions; no unresolved blocker remains.

## Phase 1: Design Outputs

- Data model documented in `data-model.md`
- API/interface contracts documented in `contracts/openapi.yaml`
- Developer validation flow documented in `quickstart.md`
- Agent context updated in `.github/copilot-instructions.md`

## Constitution Check (Post-Design)

- Container portability gate: PASS. Dockerfiles + compose topology defined in structure
  and quickstart workflow.
- Configuration gate: PASS. Environment variable inventory and startup expectations
  documented; no provider-specific constants required.
- API contract gate: PASS. `contracts/openapi.yaml` enforces `/api/v1` paths and
  `ApiEnvelope` response schema.
- Data layer gate: PASS. `data-model.md` uses SQLAlchemy-friendly types and relational
  mapping that is SQLite-compatible and PostgreSQL-ready.
- Quality gate: PASS. Plan includes typed backend functions, PEP 8, and standardized
  exception-to-envelope handling.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
