# GH-600 Study Guide Using the Financius Web Codebase

## Purpose

This document turns your current repository into a hands-on lab for **Exam GH-600: Developing in Agentic AI Systems**.

Primary source used:
- Microsoft Learn GH-600 study guide (last updated 2026-05-13):
  https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/gh-600

Goal:
- Map each GH-600 skills domain to concrete artifacts in this repo.
- Provide practical exercises you can run here.
- Identify objective gaps and how to close them before exam day.

---

## GH-600 Skills At A Glance (Official)

| Domain | Weight |
|---|---:|
| Prepare agent architecture and SDLC processes | 15-20% |
| Implement tool use and environment interaction | 20-25% |
| Manage memory, state, and execution | 10-15% |
| Perform evaluation, error analysis, and tuning | 15-20% |
| Orchestrate multi-agent coordination | 15-20% |
| Implement guardrails and accountability | 10-15% |

Exam tip: Prioritize study time by weight. The largest domain is **tool use and environment interaction (20-25%)**.

---

## Repo-as-Lab: Objective Mapping

## 1) Prepare Agent Architecture And SDLC Processes (15-20%)

### What GH-600 expects
- Define what agents should do in each SDLC stage.
- Separate planning vs execution.
- Produce inspectable artifacts and control autonomy.

### Where this repo already demonstrates it
- Project-level governance and constraints:
  - `CLAUDE.md`
  - `.claude/CLAUDE.md`
- Team-operable command and skill structure:
  - `.claude/commands/django.md`
  - `.claude/commands/django-new.md`
  - `.claude/skills/modern-web-guidance/SKILL.md`
- CI as inspectable control plane:
  - `.github/workflows/ci.yml`

### Why this matters for GH-600
This mirrors the exam concept of “system of record + control plane.” Your repo already separates:
- **Policy/instructions** (`CLAUDE.md`)
- **Execution** (scripts, commands)
- **Validation artifacts** (CI jobs)

### Practice exercise
1. In `CLAUDE.md`, create a small planning gate for medium/high-risk changes.
2. Define required output artifact for plan approval (for example: impact, files touched, rollback path).
3. Validate that your CI pipeline can enforce at least one of those checks.

---

## 2) Implement Tool Use And Environment Interaction (20-25%)

### What GH-600 expects
- Select and configure tools.
- Configure MCP servers and allow lists.
- Scope execution context (repo, branch, CI).
- Implement retries/rollback/escalation paths.

### Where this repo already demonstrates it
- Tool permissions and deny rules:
  - `.claude/settings.json`
- Environment-scoped execution scripts:
  - `scripts/run_services.sh`
- Containerized env interaction:
  - `infra/compose/docker-compose.yml`
  - `infra/docker/backend.Dockerfile`
- Branch/PR CI behavior and deployment trigger:
  - `.github/workflows/ci.yml`

### GH-600 objective gap to close
- No project `.mcp.json` found yet.

### Practice exercise (high-priority)
1. Add `.mcp.json` with one safe read-oriented server.
2. Add explicit allow-list/permission rationale in docs.
3. Add a CI check that validates `.mcp.json` schema or required fields.
4. Document which tools are approved for autonomous execution vs human approval.

Deliverable suggestion:
- `docs/gh600/mcp-and-tools-profile.md`

---

## 3) Manage Memory, State, And Execution (10-15%)

### What GH-600 expects
- Use short-term vs long-term memory deliberately.
- Persist progress and avoid context drift.
- Resume work safely across tools/environments.

### Where this repo already demonstrates it
- Persistent migration state and resumability concepts:
  - `backend/ledger/management/commands/migrate_from_sqlite.py`
  - `backend/tests/dj/unit/test_migrate_from_sqlite.py`
- Durable DB-backed token/state handling:
  - `backend/accounts/models.py`
  - `backend/accounts/views.py`
- Deterministic envelope for continuity across services:
  - `backend/financius_web/exception_handler.py`
  - `backend/tests/dj/contract/test_envelope_contract.py`

### Why this matters for GH-600
The idempotent migration pattern and contract stability are practical analogs of agent memory/state continuity:
- No repeated destructive work.
- Resume execution without semantic drift.
- Keep outputs stable for downstream consumers.

### Practice exercise
1. Write a short “agent run ledger” format (status, decision, next action, rollback note).
2. Use it while performing a migration dry-run + real run.
3. Capture where stale context might occur and how you detect it.

Deliverable suggestion:
- `docs/gh600/state-and-memory-playbook.md`

---

## 4) Perform Evaluation, Error Analysis, And Tuning (15-20%)

### What GH-600 expects
- Define success criteria and evaluation signals.
- Classify failures by root cause.
- Tune instructions/workflows/tools based on evidence.

### Where this repo already demonstrates it
- Contract-level evaluation signals:
  - `backend/tests/dj/contract/test_envelope_contract.py`
- Unit/integration root-cause oriented tests:
  - `backend/tests/dj/unit/test_auth_views.py`
  - `backend/tests/dj/unit/test_migrate_from_sqlite.py`
- Logging and traceability in API flows:
  - `backend/accounts/views.py`
  - `backend/ledger/views.py`
- CI quality gates:
  - `.github/workflows/ci.yml`

### Practice exercise
1. Create an error taxonomy for this repo:
   - reasoning/config issue
   - tool misuse
   - environment issue
   - policy/permission issue
2. Pick 5 recent failures (or simulate) and classify them.
3. Tune one instruction or script, then re-run tests to validate improvement.

Deliverable suggestion:
- `docs/gh600/evaluation-and-tuning-report.md`

---

## 5) Orchestrate Multi-Agent Coordination (15-20%)

### What GH-600 expects
- Coordinate multiple agents safely.
- Handle parallel work and conflict resolution.
- Preserve observability of handoffs and outcomes.

### Where this repo partially demonstrates it
- Existing role routing and skill invocation patterns:
  - `CLAUDE.md` (skill routing table)
- CI job orchestration and stage dependencies:
  - `.github/workflows/ci.yml` (lint, test, docker, deploy)

### GH-600 objective gap to close
- No explicit multi-agent workflow artifact in-repo (for example: coordinator policy + handoff schema + conflict-resolution policy).

### Practice exercise (high-priority)
1. Design a 3-agent workflow for this repo:
   - Planner Agent: scope + risk + success criteria
   - Implementer Agent: code changes
   - Reviewer Agent: contract/security/regression checks
2. Define conflict protocol (who wins, merge policy, escalation).
3. Define mandatory handoff artifact for each phase.

Deliverable suggestion:
- `docs/gh600/multi-agent-orchestration.md`

---

## 6) Implement Guardrails And Accountability (10-15%)

### What GH-600 expects
- Define autonomy levels by risk.
- Require human approval for irreversible/compliance-sensitive actions.
- Enforce least privilege and auditability.

### Where this repo already demonstrates it
- Explicit command allow/deny boundaries:
  - `.claude/settings.json`
- Environment-driven security boundaries:
  - `backend/financius_web/settings.py`
- API envelope and error standardization for safe client handling:
  - `backend/financius_web/exception_handler.py`

### Practice exercise
1. Create an autonomy matrix for repo actions:
   - Auto allowed
   - Auto with constraints
   - Human approval required
2. Include risky actions (schema changes, destructive scripts, force push, deployment).
3. Tie each class to concrete controls in config/CI.

Deliverable suggestion:
- `docs/gh600/autonomy-and-guardrails-matrix.md`

---

## 4-Week GH-600 Plan Using This Repo

## Week 1: Architecture + Tooling Foundations
- Read and annotate:
  - `CLAUDE.md`
  - `.claude/settings.json`
  - `.github/workflows/ci.yml`
- Produce:
  - tool inventory
  - autonomy boundaries
  - draft MCP plan

## Week 2: Memory/State + Reliability
- Deep study:
  - `backend/ledger/management/commands/migrate_from_sqlite.py`
  - `backend/tests/dj/unit/test_migrate_from_sqlite.py`
  - `backend/accounts/views.py`
- Produce:
  - state model for long-running execution
  - context-drift detection checklist

## Week 3: Evaluation + Tuning
- Deep study:
  - `backend/tests/dj/contract/test_envelope_contract.py`
  - `backend/tests/dj/unit/test_auth_views.py`
  - `backend/financius_web/exception_handler.py`
- Produce:
  - failure taxonomy
  - root-cause worksheet
  - 2 tuning loops with before/after evidence

## Week 4: Multi-Agent + Guardrails Drill
- Design and run a simulated multi-agent workflow over one medium feature change.
- Produce:
  - handoff artifacts
  - conflict-resolution log
  - post-hoc analysis and guardrail updates

---

## Practical Command Checklist

Run these from repo root as your baseline loop:

```bash
# Backend test suite used as evaluation signals
cd backend
pytest tests/dj -q

# Lint checks aligned with CI
ruff check accounts ledger financius_web tests/dj

# Migration safety rehearsal (state/resume behavior)
python manage.py migrate_from_sqlite --sqlite-path /path/to/flask.db --dry-run
```

Container and environment checks:

```bash
# Start local stack in containerized mode
docker compose -f infra/compose/docker-compose.yml up --build -d

# Run CI-equivalent sequence locally
cd backend
python manage.py migrate --noinput
pytest tests/dj -q

cd ..
docker build -f infra/docker/backend.Dockerfile -t financius-web:ci .
```

---

## Self-Assessment Rubric (Pass-Ready)

You are close to exam-ready when you can do all of the following from memory:

1. Explain how planning is separated from execution in your workflow.
2. Show how tool permissions are least-privilege and auditable.
3. Demonstrate state persistence and safe resume after interruption.
4. Define quantitative and qualitative evaluation signals.
5. Run a root-cause analysis and tune instructions/workflow accordingly.
6. Orchestrate at least 3 agent roles with explicit handoff artifacts.
7. Enforce autonomy levels with human-in-the-loop for high-risk actions.

---

## Fast Gap Closure Priorities

If time is limited before the exam, do these first:

1. Implement and document `.mcp.json` with allow-list strategy.
2. Create one concrete multi-agent orchestration spec for this repo.
3. Build a guardrails matrix mapped to `.claude/settings.json` + CI controls.
4. Run two full evaluate-tune iterations using your real test artifacts.

---

## Recommended Companion Documents In This Repo

- `docs/study/getting-started.md`
- `docs/study/claude-study-guide.md`
- `docs/study/certified-architect-foundations.md`
- `docs/claude-folder-guide.md`

Use this GH-600 guide as the practical layer on top of those foundations.
