#!/bin/sh
# Wait for Postgres to accept connections, run migrations, then exec gunicorn.
# Retries handle the race where Docker DNS isn't ready at container restart.
set -e

DB_URL="${DJANGO_DATABASE_URL:-}"

_wait_for_db() {
    echo "==> Waiting for database..."
    python - <<'PYEOF'
import os, sys, time
import psycopg2
from urllib.parse import urlparse

url = os.environ.get("DJANGO_DATABASE_URL", "")
if not url:
    print("No DJANGO_DATABASE_URL — skipping DB wait")
    sys.exit(0)

p = urlparse(url)
kwargs = dict(
    host=p.hostname,
    port=p.port or 5432,
    dbname=(p.path or "/").lstrip("/"),
    user=p.username,
    password=p.password,
    connect_timeout=3,
)

for attempt in range(1, 31):
    try:
        conn = psycopg2.connect(**kwargs)
        conn.close()
        print(f"Database ready (attempt {attempt})")
        sys.exit(0)
    except Exception as e:
        print(f"  [{attempt}/30] {e}")
        time.sleep(2)

print("ERROR: database never became ready")
sys.exit(1)
PYEOF
}

_wait_for_db

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "==> Starting gunicorn..."
exec gunicorn financius_web.wsgi:application \
    --bind "0.0.0.0:${PORT:-10000}" \
    --workers 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
