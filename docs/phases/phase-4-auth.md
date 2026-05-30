# Phase 4 — Port Auth

## Status
[x] Complete | Date: 2026-05-29

## Goal
Harden the Django auth layer and prove token cross-stack compatibility so the Android
app can switch base URLs without re-authenticating.

## What was already done in Phase 3

Phase 3 built the auth infrastructure:

| Component | Location | What it does |
|---|---|---|
| `JWTAuthentication` | `accounts/auth.py` | DRF auth class — decodes Bearer tokens for all protected endpoints |
| `RegisterView` | `accounts/views.py` | `POST /api/v1/auth/register` — email/password registration |
| `LoginView` | `accounts/views.py` | `POST /api/v1/auth/login` — email/password login |
| `GoogleLoginView` | `accounts/views.py` | `POST /api/v1/auth/google` — Google OAuth via tokeninfo |
| `RefreshView` | `accounts/views.py` | `POST /api/v1/auth/refresh` — refresh token → new access token |
| `LogoutView` | `accounts/views.py` | `POST /api/v1/auth/logout` — revoke refresh token |
| `envelope_exception_handler` | `financius_web/exception_handler.py` | Wraps all DRF 401/403 in `{data, error, meta}` |

## Phase 4 additions

### Test suite (`tests/dj/unit/test_auth_views.py` — 29 tests)

| Class | Tests |
|---|---|
| `TestRegisterView` | valid, duplicate email, invalid email, short password, missing body, DB record created, email lowercased |
| `TestLoginView` | valid, wrong password, unknown email, missing fields, response envelope |
| `TestRefreshView` | valid + stable refresh token, backward-compat aliases, expired token, access-token-as-refresh, missing token, auto-heal |
| `TestLogoutView` | valid (token deleted from DB), unknown token (idempotent), missing token |
| `TestProtectedEndpointAuth` | valid JWT, no token → 401 envelope, expired → 401 envelope, malformed, wrong secret |
| `TestTokenCrossStackCompatibility` | Flask-style JWT works on Django endpoint; full E2E flow (register → access → refresh → logout) |

## Decisions

1. **PyJWT over djangorestframework-simplejwt** — The Flask stack issues HS256 tokens with
   `{"sub": user_id, "exp": ...}` claims. Simplejwt uses a different claim shape (`user_id`
   instead of `sub`) which would break token portability during the migration window. PyJWT
   with the same `JWT_SECRET` env var keeps tokens interchangeable across stacks.

2. **Stable refresh tokens** — The refresh endpoint issues a new access token but returns the
   same refresh token. This matches Flask's behaviour and prevents auth loops on Android clients
   that do not reliably persist the rotated token.

3. **Auto-heal refresh** — If a valid signed refresh token is not in the DB (e.g., client kept
   an old token across a DB wipe), the endpoint re-links it rather than rejecting. Matches the
   Flask fallback. Tested in `test_auto_heal_missing_db_record`.

4. **Envelope on 401/403** — All DRF auth errors go through `envelope_exception_handler` so
   Android clients always receive `{data, error, meta}` regardless of whether the error is a
   validation failure or an auth failure. Tested in `test_no_token_returns_401_in_envelope`.

## Token portability invariant

Both stacks read `JWT_SECRET` from the same env var and use HS256. Tokens are structurally
identical: `{"sub": "<uuid>", "exp": <unix timestamp>}`.

```
Flask issues:   jwt.encode({"sub": user.id, "exp": exp}, settings.jwt_secret, "HS256")
Django accepts: jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
```

As long as `JWT_SECRET == jwt_secret` in the deployed environment, Android clients can switch
from `FLASK_BASE_URL` to `DJANGO_BASE_URL` with no re-auth required.

## Test coverage

- `backend/tests/dj/unit/test_auth_views.py` — 29 tests (auth endpoints + token portability)

## Checklist
- [x] `JWTAuthentication` validates Bearer tokens on all protected endpoints
- [x] All 5 auth endpoints implemented and tested
- [x] `envelope_exception_handler` wraps DRF 401/403 in `{data, error, meta}`
- [x] Cross-stack token compatibility proven by `TestTokenCrossStackCompatibility`
- [x] End-to-end flow test: register → access → refresh → logout
- [x] 109 total tests passing (29 new auth tests + 80 prior)
