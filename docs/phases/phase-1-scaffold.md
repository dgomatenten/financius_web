# Phase 1 — Django Scaffold

## Status
[x] Complete | Date: 2026-05-29

## Goal
Stand up a working Django + DRF project alongside the existing Flask app with zero
disruption to the Flask stack.

## What was done

| Item | Detail |
|---|---|
| Django version | 6.0.5 |
| DRF version | 3.17.1 |
| Scaffold location | `backend/` (alongside Flask `src/`) |
| Entrypoint | `backend/manage.py` |
| Project package | `backend/financius_web/` |

## Decisions

1. **Separate DB env var** — Django uses `DJANGO_DATABASE_URL`; Flask keeps `DATABASE_URL`.
   The Flask `.env` value is a relative SQLite path (`./data/financius.db`) that cannot be
   parsed from the `backend/` working directory. Django defaults to
   `data/django_dev.db` (absolute path) for local dev.

2. **`AUTH_USER_MODEL = "accounts.User"`** — set before any migration so all future FK
   references to User resolve to the custom model. Must never change after first migrate.

3. **`rest_framework` in `INSTALLED_APPS`** — added immediately so DRF settings and
   decorators are available from Phase 3 onwards.

4. **`SECRET_KEY` from env** — falls back to an insecure dev default. Production requires
   the env var to be set explicitly.

## Files created

- `backend/manage.py`
- `backend/financius_web/settings.py`
- `backend/financius_web/urls.py`
- `backend/financius_web/wsgi.py`
- `backend/financius_web/asgi.py`

## Checklist
- [x] `python3 manage.py check` passes (0 issues)
- [x] `requirements.txt` updated with Django/DRF/psycopg2/dj-database-url
- [x] Flask stack unaffected
