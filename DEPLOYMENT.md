# Financius Web — Deployment & Configuration Guide

## Table of Contents

1. [Local Development](#1-local-development)
2. [Environment Variables Reference](#2-environment-variables-reference)
3. [CI/CD Pipeline (GitHub Actions)](#3-cicd-pipeline-github-actions)
4. [Render Deployment](#4-render-deployment)
5. [Google OAuth Setup](#5-google-oauth-setup)
6. [Persistent Storage (SQLite Disk)](#6-persistent-storage-sqlite-disk)

---

## 1. Local Development

### Prerequisites

- Python 3.12
- Docker (optional, for container testing)

### Setup

```bash
# Clone and enter the repo
git clone https://github.com/dgomatenten/financius_web.git
cd financius_web

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Copy env file and fill in values
cp .env.example .env
# Edit .env — see Section 2 for each key

# Start Flask
./scripts/run_services.sh start flask
```

> **Note:** Flask runs via `nohup` and does **not** hot-reload. After any template or JS
> change, restart with:
> ```bash
> ./scripts/run_services.sh cleanup && ./scripts/run_services.sh start flask
> ```

### Run tests

```bash
PYTHONPATH=backend/src pytest backend/tests -q
```

### Lint

```bash
pip install ruff
ruff check backend/src backend/tests
```

---

## 2. Environment Variables Reference

| Variable | Local default | Render value | Description |
|---|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/financius.db` | `sqlite:////var/data/financius.db` | SQLite path (4 slashes = absolute on Render) |
| `SECRET_KEY` | `replace-me` | Generate random | Flask session signing key |
| `JWT_SECRET` | `replace-me` | Generate random | JWT access/refresh token signing key |
| `GOOGLE_CLIENT_ID` | `replace-me` | Your OAuth Client ID | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | `replace-me` | Your OAuth Client Secret | From Google Cloud Console |
| `API_BASE_URL` | `http://localhost:5000` | `https://financius-web.onrender.com` | Used to build Google OAuth redirect URI |
| `ALLOWED_ORIGINS` | `http://localhost:5000` | `https://financius-web.onrender.com` | CORS allowed origins |
| `FLASK_ENV` | `development` | `production` | Enables/disables debug mode |
| `BACKEND_PORT` | `8001` | — | Local port only; Render uses `PORT=10000` |
| `QR_PAIRING_TOKEN_TTL_SECONDS` | `300` | `300` | Pairing token expiry in seconds |

### Generate secure random values

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Run twice — once for `SECRET_KEY`, once for `JWT_SECRET`.

---

## 3. CI/CD Pipeline (GitHub Actions)

Pipeline file: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

### Trigger rules

| Event | Jobs that run |
|---|---|
| Push to **any branch** | lint, test, docker build |
| Push to **main** | lint, test, docker build → deploy (if all pass) |
| Pull request targeting main | lint, test, docker build |

### Jobs

```
lint ──┐
test ──┼──► deploy (main only, after all 3 pass)
docker ┘
```

| Job | What it does |
|---|---|
| **lint** | Runs `ruff check` on `backend/src` and `backend/tests` |
| **test** | Installs deps, runs `pytest backend/tests` with a test SQLite DB |
| **docker** | Builds the production Docker image to catch build errors early |
| **deploy** | POSTs to `RENDER_DEPLOY_HOOK` to trigger a Render deploy |

### Required GitHub secret

| Secret | Where to get it |
|---|---|
| `RENDER_DEPLOY_HOOK` | Render dashboard → your service → Settings → Deploy Hook |

Add it at: `github.com/dgomatenten/financius_web` → **Settings → Secrets and variables → Actions → New repository secret**

---

## 4. Render Deployment

Production URL: **https://financius-web.onrender.com**

### Service configuration

| Setting | Value |
|---|---|
| Runtime | Docker |
| Dockerfile | `./infra/docker/backend.Dockerfile` |
| Docker context | `.` (repo root) |
| Branch | `main` |
| Auto-Deploy | No (CI controls deploys via deploy hook) |
| Port | `10000` |

### Environment variables to set in Render dashboard

Go to: Render dashboard → financius-web → **Environment**

```
FLASK_ENV=production
SECRET_KEY=<generate with python3 -c "import secrets; print(secrets.token_hex(32))">
JWT_SECRET=<generate separately>
DATABASE_URL=sqlite:////var/data/financius.db
GOOGLE_CLIENT_ID=<from Google Cloud Console>
GOOGLE_CLIENT_SECRET=<from Google Cloud Console>
API_BASE_URL=https://financius-web.onrender.com
ALLOWED_ORIGINS=https://financius-web.onrender.com
QR_PAIRING_TOKEN_TTL_SECONDS=300
```

### Manual deploy trigger

```bash
git commit --allow-empty -m "chore: trigger deploy" && git push origin master
```

Or push any real change to `master` — CI runs automatically and deploys on success.

---

## 5. Google OAuth Setup

The app uses Google's OAuth 2.0 implicit flow. The frontend redirects the user to Google,
receives an `id_token` in the URL hash, and POSTs it to `/api/v1/auth/google` for
server-side verification.

### Step 1 — Create OAuth credentials in Google Cloud Console

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Select or create a project
3. **APIs & Services → OAuth consent screen**
   - User type: **External**
   - App name: `Financius Web`
   - Add your email as a test user
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   - Application type: **Web application**
   - Name: `financius-web`

### Step 2 — Register authorized redirect URIs

Under the OAuth client, add **all** environments you need:

| Environment | Redirect URI |
|---|---|
| Production | `https://financius-web.onrender.com/login` |
| Local dev | `http://localhost:5000/login` |

Click **Save**. Changes take ~5 minutes to propagate.

### Step 3 — Copy credentials

From the OAuth client detail page, copy:
- **Client ID** — paste as `GOOGLE_CLIENT_ID` in Render and `.env`
- **Client Secret** — paste as `GOOGLE_CLIENT_SECRET` in Render and `.env`

### Step 4 — Set env vars

**Render** (dashboard → Environment):
```
GOOGLE_CLIENT_ID=812922218260-xxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxx
API_BASE_URL=https://financius-web.onrender.com
```

**Local** (`.env`):
```
GOOGLE_CLIENT_ID=812922218260-xxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxx
API_BASE_URL=http://localhost:5000
```

> `API_BASE_URL` is critical — it determines the redirect URI sent to Google.
> If it's wrong, Google returns `redirect_uri_mismatch`.

### How the flow works

```
User clicks "Continue with Google"
  → Frontend builds OAuth URL with redirect_uri = API_BASE_URL + /login
  → Google authenticates user, redirects back with id_token in URL hash
  → Frontend extracts id_token, POSTs to /api/v1/auth/google
  → Backend verifies token against Google's tokeninfo endpoint
  → Backend creates/links user, returns accessToken + refreshToken
  → Frontend stores tokens in sessionStorage
```

---

## 6. Persistent Storage (SQLite Disk)

On Render's free tier, the container filesystem is **ephemeral** — it resets on every
deploy or restart. To persist the SQLite database, attach a Render Disk.

### Add a disk

1. Render dashboard → financius-web → **Disks** tab
2. **Add Disk**
   - Name: `financius-data`
   - Mount path: `/var/data`
   - Size: 1 GB (minimum, ~$0.25/month)
3. Save — Render redeploys automatically

After this, `/var/data/financius.db` survives deploys and restarts.

> Without a disk, all data is lost every time Render restarts the container (which
> happens on every deploy and periodically on the free tier).
