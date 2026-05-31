# Domain 3: Memory, State, And Execution

## Why This Domain Matters

GH-600 treats memory and execution as an operational discipline, not a vague prompt feature. The question is not whether a system can remember something. The question is whether it can preserve the right state, detect stale context, and resume safely without repeating destructive work.

This repo is unusually strong for Domain 3 because it contains a real migration workflow that has to translate state between two systems while remaining idempotent.

---

## What GH-600 Is Testing

You should be able to explain and apply these ideas:
- the difference between short-term working context and durable execution state
- how to resume after interruption without creating duplicates or semantic drift
- how to detect when context is stale or incomplete before taking the next action
- why stable output contracts matter for continuity across tools and consumers

---

## Repo Mapping

### `backend/ledger/management/commands/migrate_from_sqlite.py`

This is the main Domain 3 anchor.

What it teaches:
- idempotent execution through `update_or_create` and conflict-tolerant inserts
- safe rehearsal using `--dry-run`
- explicit translation from Flask user identifiers to Django user identifiers
- ordered execution over a set of dependent tables

This is not only a data-migration example. It is also a state-management example because the command has to keep track of what source identifiers mean in the target system.

### `backend/tests/dj/unit/test_migrate_from_sqlite.py`

This file turns the migration behavior into inspectable evidence.

What it teaches:
- the system must prove idempotency, not merely claim it
- dry-run behavior should be testable
- compatibility logic such as password wrapping and identifier mapping must survive repetition and partial reruns

### `backend/financius_web/exception_handler.py`

This file is a different kind of continuity artifact.

What it teaches:
- error responses are normalized into the `{ data, error, meta }` envelope
- stable response shape is part of execution continuity for downstream consumers
- state continuity includes output continuity, not just database state

---

## The Most Important Mental Model

For GH-600, think in three layers:

### Working memory
The immediate context used to decide the next action.

Example in this repo:
- which table is being migrated right now
- which validation command should run next

### Durable execution state
The persistent state that lets the system resume without losing correctness.

Example in this repo:
- migrated users already represented in Django
- refresh tokens stored in the database
- target rows that should not be duplicated on rerun

### Stable interface state
The contract other systems depend on while execution continues or changes underneath.

Example in this repo:
- the standard error envelope
- auth token compatibility across stacks

---

## Worked Example: Why The Migration Command Is A Domain 3 Study Asset

The migration command does not just "copy rows."

It has to:
1. open the source SQLite database safely
2. build a user mapping from Flask identifiers to Django UUIDs
3. preserve ordering across dependent tables
4. stay safe on rerun
5. provide a dry-run path that exercises the logic without committing changes

That combination is exactly why it is valuable for GH-600 study. It forces you to reason about state translation, restart safety, and rollback behavior together.

---

## Context Drift In This Repo

Domain 3 is also about recognizing when the system's current mental model is no longer trustworthy.

Likely drift signals here:
- a policy file still assumes Flask-first execution when the codebase is Django-first
- a migration plan assumes source identifiers map directly, but they actually require translation
- a validation step is skipped because a previous run is incorrectly assumed to still apply
- a consumer contract changes shape even though the workflow assumes continuity

When you see one of these, stop and refresh the relevant source of truth before continuing.

---

## Common Failure Modes

### Replay without idempotency
The same workflow runs twice and creates duplicates or conflicting state.

### Dry-run that is not representative
The rehearsal path skips the real logic, so it does not tell you whether the actual execution is safe.

### Hidden translation state
The workflow relies on an implicit mapping or derived state that is never recorded explicitly.

### Stable outputs treated as optional
The execution path changes behavior in a way that breaks downstream consumers even though internal state looks correct.

---

## What Good Looks Like In An Exam Answer

If asked how to manage state safely in this repo, a strong answer would say:
- use the migration command as the model for idempotent execution and resumability
- preserve identifier translation explicitly when moving between systems
- rehearse risky flows with a representative dry-run path
- use tests to verify rerun safety and output continuity
- treat stable response envelopes as part of durable system behavior

That answer is stronger than saying, "store state in a database," because it explains how the workflow stays correct across interruption and repetition.

---

## Self-Check

1. Why is idempotency a state-management concern rather than only a database concern?
2. What does the migration command remember that a naive row copier would not?
3. Why is a stable API envelope relevant to Domain 3?
4. What is one concrete signal that your working context has gone stale?

---

## Next Steps

- Run [labs/lab-memory-and-state.md](labs/lab-memory-and-state.md)
- Review [state-and-memory-playbook.md](state-and-memory-playbook.md)
- Inspect [backend/ledger/management/commands/migrate_from_sqlite.py](../../backend/ledger/management/commands/migrate_from_sqlite.py) and [backend/tests/dj/unit/test_migrate_from_sqlite.py](../../backend/tests/dj/unit/test_migrate_from_sqlite.py)