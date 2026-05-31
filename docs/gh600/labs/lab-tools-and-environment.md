# Lab: Tool Use And Environment Interaction

## Goal

Study how this repo constrains tool use, scopes execution environments, and separates low-risk from higher-risk operations.

---

## Prerequisites

- basic familiarity with the GH-600 Domain 2 objectives
- read [../domain-2-tools-and-environment.md](../domain-2-tools-and-environment.md)

---

## Files To Inspect

- `.claude/settings.json`
- `.github/workflows/ci.yml`
- `infra/compose/docker-compose.yml`
- `infra/docker/backend.Dockerfile`
- `scripts/run_services.sh`

---

## Suggested Commands

Run these from the repo root or `backend/` as noted.

```bash
cd backend
pytest tests/dj -q
ruff check accounts ledger financius_web tests/dj
```

```bash
docker build -f infra/docker/backend.Dockerfile -t financius-web:ci .
```

Review the existing `.mcp.json` as part of the lab. Do not expand it beyond the current server set unless you are intentionally turning this lab into a repo change.

---

## What To Observe

1. Which actions are explicitly allowed, and which are denied, in `.claude/settings.json`?
2. Which parts of the policy still reflect legacy Flask assumptions rather than the current Django-first stack?
3. How does `.github/workflows/ci.yml` turn tool use into a staged control flow?
4. Why are `filesystem-readonly`, `postgres-readonly`, `github`, `playwright`, `docker`, and `fetch-url` reasonable MCP choices for this repo?
5. How do `GITHUB_TOKEN` scope and Docker tool exposure change MCP risk classification even when the server names look familiar?
6. Which of the added MCPs are best treated as inspection-only despite having broader possible capability?
7. Which steps are safe for autonomous execution, and which should require approval?

---

## Reflection Prompts

Write short answers to these:
- What is the smallest useful MCP profile you would add first?
- If the current `.mcp.json` is the baseline, what should the next expansion avoid adding too early beyond these inspection-heavy servers?
- Which allowed commands would you keep, remove, or update?
- Where does CI act as a guardrail rather than just a convenience?
- What is the difference between a retry path and a rollback path in this repo?

---

## Completion Criteria

You are done when you can produce:
- a tool inventory grouped by risk level
- one paragraph identifying policy drift in `.claude/settings.json`
- one explanation of why the current MCP profile is still least-privilege, including token-scope and runtime-impact limits