# Render PostgreSQL Setup — Step by Step

## How it works

`render.yaml` already declares both the web service and a managed PostgreSQL
database. Render reads this file when you connect the repo and provisions both
together. `DJANGO_DATABASE_URL` is injected automatically via `fromDatabase` —
you never touch the connection string manually.

`entrypoint.sh` runs `python manage.py migrate --noinput` on every container
start, so schema changes deploy automatically with no manual migration step.

---

## First-time setup

### Step 1 — Connect the repo to Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **New** → **Blueprint**
3. Connect your GitHub account if not connected
4. Select the `financius_web` repo
5. Render detects `render.yaml` automatically → click **Apply**

Render provisions in this order:
- `financius-db` — PostgreSQL 16 (free tier)
- `financius-web` — Docker web service (waits for DB to be ready)

This takes 2–5 minutes. Watch the **Events** tab.

---

### Step 2 — Set required environment variables

After provisioning, go to **financius-web → Environment** and set:

| Variable | Value |
|---|---|
| `GOOGLE_CLIENT_ID` | Your OAuth client ID from Google Cloud Console |
| `API_BASE_URL` | `https://financius-web.onrender.com` |
| `ALLOWED_HOSTS` | `financius-web.onrender.com` |

`SECRET_KEY`, `JWT_SECRET`, and `DJANGO_DATABASE_URL` are set automatically
by `render.yaml` (generated value + fromDatabase injection).

---

### Step 3 — Trigger the first deploy

```bash
# From your local machine
git commit --allow-empty -m "chore: trigger initial Render deploy"
git push origin master
```

Or click **Manual Deploy → Deploy latest commit** in the Render dashboard.

Watch the deploy logs — you should see:

```
==> Waiting for database...
Database ready (attempt 1)
==> Running migrations...
Operations to perform:
  Apply all migrations: accounts, admin, auth, contenttypes, ledger, sessions
Running migrations:
  Applying accounts.0001_initial... OK
  ...
==> Collecting static files...
==> Starting gunicorn...
[INFO] Listening at: http://0.0.0.0:10000
```

---

### Step 4 — Verify the app is live

```
https://financius-web.onrender.com/api/v1/health/
```

Expected response:
```json
{"data": {"status": "ok"}, "error": null, "meta": {}}
```

---

## Schema changes (DDL) — how to deploy

Every Django migration file committed to `master` is applied automatically on
the next deploy. No manual steps required.

**Workflow for a model change:**

```bash
# 1. Make your model change locally
# 2. Generate the migration
cd backend
python manage.py makemigrations

# 3. Test it locally
python manage.py migrate

# 4. Commit both the model change and the migration file
git add .
git commit -m "feat: add <field> to <Model>"
git push origin master

# 5. CI runs tests → passes → triggers Render deploy hook
# 6. Render pulls new image, runs entrypoint.sh
#    → migrate --noinput applies the new migration automatically
```

**If CI is not wired to auto-deploy** (autoDeploy is false in render.yaml),
trigger manually after CI passes:

```bash
curl -X POST "$RENDER_DEPLOY_HOOK"
```

Or click **Manual Deploy** in the dashboard.

---

## Connect to the Render database from your local machine

Useful for running `migrate_from_sqlite` or inspecting production data.

1. Go to **financius-db → Info** in the Render dashboard
2. Copy the **External Database URL** (starts with `postgres://...`)
3. Run locally:

```bash
# Migrate your SQLite data to Render's Postgres
docker cp data/financius.db compose-backend-1:/tmp/financius.db  # or any path
DJANGO_DATABASE_URL="<external-url>" \
python3 backend/manage.py migrate_from_sqlite \
    --sqlite-path data/financius.db

# Or connect with psql
psql "<external-url>"
```

> Use the **Internal URL** only from within Render's network (the web service
> uses this automatically). Use the **External URL** from your local machine.

---

## Free tier limits

| Limit | Value |
|---|---|
| Storage | 1 GB |
| Connections | 97 concurrent |
| Expiry | **90 days** — Render deletes free databases after 90 days of inactivity |
| Backups | None on free tier |

**Before the 90-day expiry:** upgrade to a paid plan ($7/month) or export
your data and recreate the database.

Export before expiry:
```bash
pg_dump "<external-url>" > backup.sql
```

---

## Troubleshooting

**Deploy fails with "could not connect to server"**
→ The web service started before the database was ready. The `entrypoint.sh`
  retries 30 times over 60 seconds. If it still fails, check the database
  service status in the Render dashboard.

**"relation does not exist" error**
→ Migrations didn't run. Check deploy logs for migration output. If missing,
  the `DJANGO_DATABASE_URL` env var may not be set correctly.

**"ALLOWED_HOSTS" error (400 Bad Request)**
→ Add `financius-web.onrender.com` to the `ALLOWED_HOSTS` environment variable
  in the Render dashboard.

**Static files return 404**
→ `collectstatic` runs in `entrypoint.sh`. Check logs for errors there.
  WhiteNoise serves static files from gunicorn — no separate nginx needed.
