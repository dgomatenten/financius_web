Run a Django health check for the Financius Web project and report status.

Execute each of the following in order from /home/dgoma/app_dev/financius_web and summarise what you find:

1. `python3 manage.py check --deploy 2>&1 || python3 manage.py check 2>&1` — system checks (model errors, config issues)
2. `python3 manage.py showmigrations 2>&1` — list all apps and migration status ([ ] = pending, [x] = applied)
3. `python3 manage.py migrate --check 2>&1` — confirm no unapplied migrations exist

If manage.py is not found, report "Django not yet configured — run Phase 1 setup first."

After running: give a 3-line summary:
- What is healthy
- What is pending or missing
- What needs immediate attention (if anything)

If $ARGUMENTS is provided, treat it as a specific check to run (e.g. "migrations", "check", "dbshell").
