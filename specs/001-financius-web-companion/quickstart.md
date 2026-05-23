# Quickstart: Financius Web

## Prerequisites
- Docker and Docker Compose plugin installed
- Optional local tooling: Python 3.12

## 1. Configure Environment
Create a local env file (excluded from VCS):

```bash
cp .env.example .env
```

Minimum variables:

```env
DATABASE_URL=sqlite:///./data/financius.db
SECRET_KEY=replace-me
JWT_SECRET=replace-me
GOOGLE_CLIENT_ID=replace-me
GOOGLE_CLIENT_SECRET=replace-me
ALLOWED_ORIGINS=http://localhost:8000
QR_PAIRING_TOKEN_TTL_SECONDS=300
API_BASE_URL=http://localhost:8000
```

## 2. Start Services (Docker-first)

```bash
docker compose -f infra/compose/docker-compose.yml up --build
```

Expected local ports:
- Flask app (UI + API): `http://localhost:8000`

## 3. Initialize Database
Inside backend container:

```bash
docker compose -f infra/compose/docker-compose.yml exec backend alembic upgrade head
```

## 4. Smoke Test API Envelope

```bash
curl -s http://localhost:8000/api/v1/health | jq
```

Expected shape:

```json
{
  "data": { "status": "ok" },
  "error": null,
  "meta": {
    "request_id": "..."
  }
}
```

## 5. Validate Android Sync Path
1. Login and obtain JWT access token.
2. POST a sample sync payload to `/api/v1/sync`.
3. Verify response envelope and updated `last_sync_at`.

## 6. Run Test Suites

Backend tests:

```bash
docker compose -f infra/compose/docker-compose.yml exec backend pytest
```

Contract tests:

```bash
docker compose -f infra/compose/docker-compose.yml exec backend pytest tests/contract
```

## 7. Portability Validation Checklist
- No provider-specific constants in code/config.
- All settings sourced from environment variables.
- App starts and passes smoke tests using Docker only.
- `/api/v1` routes return `{ data, error, meta }` consistently.

## 8. Validation Record (2026-05-17)
- Backend syntax validation passed with `python3 -m compileall backend/src`.
- Contract verification passed:
  - `/api/v1` path entries found: 26
  - Envelope schema with required `{ data, error, meta }`: confirmed.

## 9. Local Launcher (Flask-Only)

Use the unified launcher for local development:

```bash
./scripts/launch.sh
```

Useful commands:

```bash
./scripts/run_services.sh status
./scripts/run_services.sh logs backend
./scripts/run_services.sh cleanup
```

## 10. Speckit Task Management Helper

Use the local helper script to manage implementation progress from `tasks.md`.

```bash
./scripts/speckit_tasks.sh status
./scripts/speckit_tasks.sh next
./scripts/speckit_tasks.sh pick US2
./scripts/speckit_tasks.sh done T023
./scripts/speckit_tasks.sh reopen T023
```

Tips:
- `status` shows completed/remaining counts and the current phase.
- `next` shows the first unchecked task.
- `pick <pattern>` scopes by story/phase labels.
- `done` and `reopen` update the checklist line directly in `tasks.md`.
