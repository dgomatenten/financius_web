# GH-600 Study Pack Using the Financius Web Codebase

## Purpose

This document is the entry point for a repo-backed GH-600 study pack.

Use it to do three things:
- map each GH-600 domain to concrete Financius artifacts
- move from concept study into hands-on repo labs
- track what is available now versus what is still planned

Primary source used:
- Microsoft Learn GH-600 study guide (last updated 2026-05-13):
  https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/gh-600

---

## How To Use This Pack

Study each domain in the same order:
1. Read the domain lesson note.
2. Inspect the referenced repo files.
3. Run the matching lab.
4. Capture what you learned in your notes or journal.
5. Return later for practice questions and the 4-week schedule.

If you are short on time, start with Domain 2, Domain 4, and Domain 5. Those are the highest-value sections currently implemented in detail.

## Claude To Copilot Translation

Most repo artifacts in this pack are named for Claude Code because that is the current project setup. If you are studying through GitHub Copilot, use this translation table while reading:

| Claude-oriented artifact | Closest GitHub Copilot equivalent | How to think about it |
|---|---|---|
| `CLAUDE.md` | `copilot-instructions.md` | always-loaded project instructions and engineering rules |
| `.claude/CLAUDE.md` | repo or folder-scoped Copilot instruction files | project-scoped agent guidance |
| `.claude/commands/*.md` | prompt files or reusable chat prompts | repeatable task entry points |
| `.claude/skills/.../SKILL.md` | specialized Copilot prompt or agent customization files | reusable domain behavior with constraints |
| `.claude/settings.json` | Copilot chat/tool configuration and agent restrictions | tool permissions, safety boundaries, and execution defaults |

This is a conceptual map, not a strict file-for-file migration guide. The exam-relevant idea is the role each artifact plays: instruction layer, task-routing layer, and tool-governance layer.

---

## GH-600 Skills At A Glance

| Domain | Weight | Status In This Pack |
|---|---:|---|
| Prepare agent architecture and SDLC processes | 15-20% | detailed note available |
| Implement tool use and environment interaction | 20-25% | detailed note and lab available |
| Manage memory, state, and execution | 10-15% | detailed note, lab, and reference available |
| Perform evaluation, error analysis, and tuning | 15-20% | detailed note and lab available |
| Orchestrate multi-agent coordination | 15-20% | detailed note and lab available |
| Implement guardrails and accountability | 10-15% | detailed note and reference available |

Exam tip: Domain 2 carries the highest weight, but Domains 4 and 5 are where repo-backed reasoning practice becomes most visible.

---

## Available Study Materials

### Domain notes available now
- [domain-1-architecture-and-sdlc.md](domain-1-architecture-and-sdlc.md)
- [domain-2-tools-and-environment.md](domain-2-tools-and-environment.md)
- [domain-3-memory-state-execution.md](domain-3-memory-state-execution.md)
- [domain-4-evaluation-and-tuning.md](domain-4-evaluation-and-tuning.md)
- [domain-5-multi-agent-coordination.md](domain-5-multi-agent-coordination.md)
- [domain-6-guardrails-and-accountability.md](domain-6-guardrails-and-accountability.md)

### Labs available now
- [labs/lab-tools-and-environment.md](labs/lab-tools-and-environment.md)
- [labs/lab-memory-and-state.md](labs/lab-memory-and-state.md)
- [labs/lab-evaluation-and-tuning.md](labs/lab-evaluation-and-tuning.md)
- [labs/lab-multi-agent-workflow.md](labs/lab-multi-agent-workflow.md)

### Existing companion references
- [mcp-and-tools-profile.md](mcp-and-tools-profile.md)
- [multi-agent-orchestration.md](multi-agent-orchestration.md)
- [autonomy-and-guardrails-matrix.md](autonomy-and-guardrails-matrix.md)
- [state-and-memory-playbook.md](state-and-memory-playbook.md)
- [evaluation-and-tuning-report.md](evaluation-and-tuning-report.md)
- [practice-questions.md](practice-questions.md)
- [study-schedule-4-weeks.md](study-schedule-4-weeks.md)

### Planned next additions
- alignment updates for the broader study docs under `docs/study/`

---

## Repo-As-Lab Mapping

## 1) Prepare Agent Architecture And SDLC Processes

### What GH-600 expects
- define agent responsibilities by SDLC stage
- separate planning from execution
- keep outputs inspectable and reviewable

### Best repo anchors
- `CLAUDE.md`
- `.claude/CLAUDE.md`
- `.claude/commands/django.md`
- `.claude/commands/django-new.md`
- `.github/workflows/ci.yml`

### Why this matters here
This repo already separates policy, execution, and validation. That is the core GH-600 architecture pattern even before any multi-agent system is added.

### Study action
- Lesson note: [domain-1-architecture-and-sdlc.md](domain-1-architecture-and-sdlc.md)

---

## 2) Implement Tool Use And Environment Interaction

### What GH-600 expects
- choose tools deliberately
- limit capability by environment and risk
- define retries, rollback, and escalation paths
- make tool use auditable

### Best repo anchors
- `.claude/settings.json`
- `.github/workflows/ci.yml`
- `scripts/run_services.sh`
- `infra/compose/docker-compose.yml`
- `infra/docker/backend.Dockerfile`

### Why this matters here
Financius already shows tool allow-lists, deny rules, CI-scoped execution, containerized environment control, and a project `.mcp.json` with filesystem, PostgreSQL, and GitHub MCP servers. The main next gap is validating and governing that MCP surface over time, especially token scope and policy drift.

### Study materials
- Lesson note: [domain-2-tools-and-environment.md](domain-2-tools-and-environment.md)
- Lab: [labs/lab-tools-and-environment.md](labs/lab-tools-and-environment.md)
- Reference: [mcp-and-tools-profile.md](mcp-and-tools-profile.md)

---

## 3) Manage Memory, State, And Execution

### What GH-600 expects
- distinguish short-term versus persistent state
- resume safely after interruption
- detect stale context before acting

### Best repo anchors
- `backend/ledger/management/commands/migrate_from_sqlite.py`
- `backend/tests/dj/unit/test_migrate_from_sqlite.py`
- `backend/accounts/models.py`
- `backend/accounts/views.py`
- `backend/financius_web/exception_handler.py`

### Why this matters here
The migration command is an unusually strong study example because it is explicitly idempotent, supports dry-run behavior, and translates state between two systems without repeating destructive work.

### Study action
- Lesson note: [domain-3-memory-state-execution.md](domain-3-memory-state-execution.md)
- Lab: [labs/lab-memory-and-state.md](labs/lab-memory-and-state.md)
- Reference: [state-and-memory-playbook.md](state-and-memory-playbook.md)

---

## 4) Perform Evaluation, Error Analysis, And Tuning

### What GH-600 expects
- define good evaluation signals before you tune
- separate reasoning failures from tool or environment failures
- rerun checks after each change to confirm improvement

### Best repo anchors
- `backend/tests/dj/contract/test_envelope_contract.py`
- `backend/tests/dj/unit/test_auth_views.py`
- `backend/tests/dj/unit/test_migrate_from_sqlite.py`
- `backend/financius_web/exception_handler.py`
- `.github/workflows/ci.yml`

### Why this matters here
The repo already has contract-level and unit-level checks that can be used as evaluation signals. The main study move is learning how to classify failures and decide what to tune from the evidence.

### Study materials
- Lesson note: [domain-4-evaluation-and-tuning.md](domain-4-evaluation-and-tuning.md)
- Lab: [labs/lab-evaluation-and-tuning.md](labs/lab-evaluation-and-tuning.md)

---

## 5) Orchestrate Multi-Agent Coordination

### What GH-600 expects
- coordinate specialist roles safely
- handle parallel work and conflict resolution
- keep handoffs inspectable

### Best repo anchors
- `CLAUDE.md`
- `.github/workflows/ci.yml`
- `docs/gh600/multi-agent-orchestration.md`

### Why this matters here
The repo has role routing and pipeline stages already, but GH-600 expects explicit coordinator logic, handoff artifacts, and conflict handling. That is why this domain needs both a lesson note and a lab.

### Study materials
- Lesson note: [domain-5-multi-agent-coordination.md](domain-5-multi-agent-coordination.md)
- Lab: [labs/lab-multi-agent-workflow.md](labs/lab-multi-agent-workflow.md)
- Reference: [multi-agent-orchestration.md](multi-agent-orchestration.md)

---

## 6) Implement Guardrails And Accountability

### What GH-600 expects
- set autonomy levels by risk
- keep high-risk actions behind approval gates
- preserve auditability

### Best repo anchors
- `.claude/settings.json`
- `backend/financius_web/settings.py`
- `backend/financius_web/exception_handler.py`
- `docs/gh600/autonomy-and-guardrails-matrix.md`

### Why this matters here
Least privilege is already present in the repo, but the learner still needs worked examples that show how guardrails affect real execution decisions.

### Study action
- Lesson note: [domain-6-guardrails-and-accountability.md](domain-6-guardrails-and-accountability.md)
- Reference: [autonomy-and-guardrails-matrix.md](autonomy-and-guardrails-matrix.md)

---

## Suggested First Week From This Pack

1. Read [domain-2-tools-and-environment.md](domain-2-tools-and-environment.md) and run [labs/lab-tools-and-environment.md](labs/lab-tools-and-environment.md).
2. Read [domain-4-evaluation-and-tuning.md](domain-4-evaluation-and-tuning.md) and run [labs/lab-evaluation-and-tuning.md](labs/lab-evaluation-and-tuning.md).
3. Read [domain-5-multi-agent-coordination.md](domain-5-multi-agent-coordination.md) and run [labs/lab-multi-agent-workflow.md](labs/lab-multi-agent-workflow.md).
4. Read [domain-3-memory-state-execution.md](domain-3-memory-state-execution.md) and run [labs/lab-memory-and-state.md](labs/lab-memory-and-state.md).
5. Review [mcp-and-tools-profile.md](mcp-and-tools-profile.md), [state-and-memory-playbook.md](state-and-memory-playbook.md), [evaluation-and-tuning-report.md](evaluation-and-tuning-report.md), [multi-agent-orchestration.md](multi-agent-orchestration.md), and [autonomy-and-guardrails-matrix.md](autonomy-and-guardrails-matrix.md).
6. Use [../study/getting-started.md](../study/getting-started.md) for the broader study sequence outside GH-600-specific work.

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

1. Add CI validation for `.mcp.json` syntax and required keys.
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
