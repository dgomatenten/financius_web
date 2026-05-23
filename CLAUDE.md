# Financius Web — Claude Code Instructions

## Project Principles

### I. Container-First Portability
All runtime services MUST run in containers, executable via Docker in local, CI, and
deployment environments. Hosting MUST remain portable across AWS App Runner, Render,
Railway, and Fly.io. Code MUST NOT embed provider-specific behavior unless explicitly
abstracted.

### II. Environment-Driven Configuration
All configuration MUST come from environment variables. Hardcoded cloud identifiers,
endpoints, regions, or credentials are prohibited. Secrets MUST never be committed.
Development defaults MAY live in local env files excluded from version control.

### III. Versioned API Contract Discipline
REST endpoints MUST be published under `/api/v1`. Every response MUST use the envelope
`{ data, error, meta }` with stable field semantics. Contract changes that can break
Android Retrofit clients MUST trigger explicit versioning and be documented before release.

### IV. Data Layer Stability
Backend MUST use SQLAlchemy ORM with SQLite as the current default. Schema design MUST
preserve forward migration to PostgreSQL without rewriting business logic. All SQL MUST
flow through ORM models or sanctioned query abstractions.

### V. Python Quality
Backend MUST follow PEP 8 with type hints on all functions. Dependencies MUST be minimal
and justified by direct product need. All API endpoints MUST catch, log, and map
unexpected exceptions to safe error responses within the standard envelope.

## Technology Standards

- **Backend:** Python Flask, SQLAlchemy, SQLite → PostgreSQL migration path
- **Frontend:** Minimal HTML/JS (`app.css` + vanilla JS); no unnecessary frameworks
- **API consumers:** Android Retrofit clients and web clients share identical contracts
- **Docker:** Images MUST define deterministic builds with explicit entrypoints
- **Logging:** Include request correlation context; never expose secrets or tokens

## Claude's Role

- Write and review code against the principles above
- Catch missing type hints, hardcoded config values, or bare `except` clauses
- Prefer migration-safe patterns — no AWS SDK lock-in where avoidable
- Flag any API response that breaks the `{ data, error, meta }` envelope

## Flask Dev Server Note

Flask runs via `nohup` (not dev mode) and does **not** hot-reload templates or static
files. After any template or JS change, restart with:

```bash
./scripts/run_services.sh cleanup && ./scripts/run_services.sh start flask
```

## Skill Routing

When the user's request matches an available skill, invoke it via the Skill tool.

| Request type | Skill |
|---|---|
| Product ideas / brainstorming | `/office-hours` |
| Strategy / scope | `/plan-ceo-review` |
| Architecture | `/plan-eng-review` |
| Design system / plan review | `/design-consultation` or `/plan-design-review` |
| Full review pipeline | `/autoplan` |
| Bugs / errors | `/investigate` |
| QA / testing site behavior | `/qa` or `/qa-only` |
| Code review / diff check | `/review` |
| Visual polish | `/design-review` |
| Ship / deploy / PR | `/ship` or `/land-and-deploy` |
| Save progress | `/context-save` |
| Resume context | `/context-restore` |
