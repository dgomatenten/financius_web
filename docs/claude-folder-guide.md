# .claude Folder — How to Use

The `.claude/` folder configures Claude Code behavior for this project.
Everything here is local to `financius_web` and overrides global Claude settings.

---

## Folder Structure

```
.claude/
├── CLAUDE.md                        # Points to root CLAUDE.md (project rules)
├── settings.json                    # Permissions, env vars, hooks
├── .env                             # Local secrets for Claude sessions
├── commands/
│   └── django.md                    # Slash command: /django
├── skills/
│   └── modern-web-guidance/         # Frontend best-practice skill
│       ├── SKILL.md                 # Skill definition
│       └── guides/                  # 100+ HTML/CSS/JS guides
└── log_to_obsidian.py               # Helper: logs sessions to Obsidian
```

---

## settings.json

Controls what Claude can run without prompting you for permission.

### Allowed commands (no prompt)

| Pattern | Purpose |
|---|---|
| `git *` | All git operations |
| `python3 *`, `pip3 *`, `pip *` | Python and package management |
| `ruff *`, `pytest *` | Linting and tests |
| `docker *`, `docker compose *` | Container management |
| `./scripts/run_services.sh *` | Service lifecycle |
| `flask *`, `gunicorn *` | Flask server commands |
| `manage.py *`, `python3 manage.py *` | Django management (ready for migration) |
| `adb *`, `flutter *` | Android dev tools |
| `find . *`, `grep *`, `ls *`, `tail *` | File exploration |

### Blocked commands (always denied)

- `git push --force` / `git push -f` — prevents force-pushes
- `rm -rf /*` — prevents root deletion

### Environment variables injected into every session

```json
PYTHONPATH = "backend/src"
FLASK_APP  = "backend/src/app.py"
FLASK_ENV  = "development"
```

### Hooks

After every `Edit` or `Write` tool call, Claude automatically runs:
```bash
ruff check backend/src/ --quiet --no-fix | head -20
```
This means lint errors appear inline after any code change — no need to run ruff manually.

---

## Slash Commands

### `/django`

**Usage:** Type `/django` in Claude Code chat (or `/django migrations` for a specific check).

**What it does:** Runs a Django health check in this order:
1. `python3 manage.py check --deploy` — model/config errors
2. `python3 manage.py showmigrations` — pending vs applied migrations
3. `python3 manage.py migrate --check` — confirms DB is up to date

Returns a 3-line summary: what's healthy, what's pending, what needs attention.

> Until Phase 1 of the Django migration is complete, this will report
> "Django not yet configured — run Phase 1 setup first."

**To add more commands:** Create a `.md` file in `.claude/commands/`.
Each file becomes `/filename` (without the extension).

---

## Skills

### `modern-web-guidance`

A mandatory skill for all frontend (HTML/CSS/JS) work.

**When Claude uses it automatically:**
- Modals, dialogs, popovers, anchor positioning
- Scroll-driven animations, view transitions
- Performance (LCP, INP, image loading)
- Forms, autofill, custom inputs
- Dark mode, container queries, `:has()`

**How it works:**
1. Searches ~100 curated guides for the relevant pattern
2. Retrieves the best-practice guide before writing any code
3. Adapts the guide to this project's vanilla JS + minimal CSS stack

**You don't invoke this manually** — Claude triggers it at the start of any frontend task.

**To add a custom skill:** Create `.claude/skills/<skill-name>/SKILL.md`
following the same frontmatter format (`name`, `description`, triggers).

---

## .env (Claude session secrets)

Secrets available to Claude during its tool calls (not committed to git).
Separate from the root `.env` which the Flask app reads at runtime.

Add any API keys here that Claude needs to run scripts during a session
(e.g. for test automation or data migration helpers).

---

## log_to_obsidian.py

A helper script that can be run to log Claude session summaries to an Obsidian vault.
Not invoked automatically — run manually when you want to capture a session.

```bash
python3 .claude/log_to_obsidian.py
```

---

## Workflows by Task Type

| Task | What Claude uses |
|---|---|
| Fix a backend bug | `/investigate` skill + ruff auto-lint hook |
| Add a Django model | `manage.py` permission + ruff hook |
| Check Django health | `/django` slash command |
| Build a UI component | `modern-web-guidance` skill (auto) |
| Run tests | `pytest *` permission (no prompt) |
| Docker rebuild | `docker compose *` permission (no prompt) |
| Ship a PR | `/ship` skill |
| QA the web app | `/qa` skill |

---

## Adding / Changing Settings

Edit `.claude/settings.json` directly, or use the `/update-config` skill
to add permissions, env vars, or hooks via chat.

Example: "allow curl commands" → Claude adds `"Bash(curl *)"` to the allow list.
