# GH-600 Companion: State And Memory Playbook

## Objective

Turn Domain 3 into a concrete operating playbook using the Financius migration and API continuity patterns.

This document covers:
- a practical run-ledger format
- the difference between short-term context and durable state
- context-drift indicators
- safe-resume and rollback thinking

---

## Core Distinction

### Short-term working context
The information needed to decide the next action right now.

Examples in this repo:
- which table migration step is currently executing
- which validation command should run next
- which file most directly controls the behavior under review

### Durable state
The information that must survive interruption, retries, or handoffs.

Examples in this repo:
- users, tokens, receipts, and related rows already persisted in Django
- the derived user-ID translation map during migration
- contract invariants such as the standard response envelope

If you mix these two layers together, workflows become fragile. The system starts treating temporary assumptions as if they were reliable stored state.

---

## Run Ledger Format

Use this lightweight structure whenever you rehearse or execute a meaningful workflow.

```yaml
task_id: GH600-YYYYMMDD-01
goal: Migrate Flask SQLite data into Django safely
phase: planning|execution|validation|rollback-ready
status: not_started|running|blocked|completed
current_step: explicit next action
durable_state:
  source_db: /path/to/source.db
  target_env: local-postgres
  invariants:
    - envelope remains { data, error, meta }
    - migration is idempotent on rerun
working_context:
  controlling_file: backend/ledger/management/commands/migrate_from_sqlite.py
  validation_focus: tests/dj/unit/test_migrate_from_sqlite.py
decisions:
  - why this next action is safe
risks:
  - stale source path
  - identifier translation error
drift_signals:
  - assumption no longer matches code or env
validation:
  commands:
    - pytest tests/dj/unit/test_migrate_from_sqlite.py -q
  results:
    - pass|fail summary
rollback_note: what can be reverted and what cannot
next_action: explicit next step
```

The important part is not the YAML itself. The important part is forcing the workflow to distinguish between what is known, what is assumed, and what must remain stable.

---

## Worked Example 1: Migration Dry Run

### Situation
You want to rehearse `migrate_from_sqlite` before using a real source database.

### What must persist
- the source path being used
- the target environment being exercised
- the invariant that no writes survive a dry run

### What can drift
- whether the source schema still matches what the command expects
- whether the operator is pointing at the intended database file
- whether the current architecture assumptions still match the repo's Django-first state

### Safe sequence
1. record the source database path and target environment in the run ledger
2. run `pytest tests/dj/unit/test_migrate_from_sqlite.py -q`
3. if available, run the dry-run command against a safe source database
4. compare the observed behavior with the invariant that dry-run leaves no persisted writes
5. only then consider a non-dry-run execution

### Why this is GH-600 relevant
This is a direct example of safe resumability. The workflow separates rehearsal from mutation while keeping the logic path representative.

---

## Worked Example 2: Stable Error Continuity

### Situation
An auth or validation error occurs during an API workflow.

### What must persist
- the client-facing envelope shape
- the interpretation that `data` is absent and `error` is populated on failure

### Where this is implemented
- `backend/financius_web/exception_handler.py`
- `backend/tests/dj/contract/test_envelope_contract.py`

### Why it matters
State continuity is not only about database rows. If the execution path changes error shapes between runs or across stacks, downstream consumers lose continuity even if the server thinks its internal state is valid.

---

## Context-Drift Checklist

Stop and refresh context if any of these appear:
1. a config or policy file still describes the old stack rather than the current stack
2. a command is being retried without understanding why it failed
3. the controlling file for the behavior is no longer the file you first assumed
4. the validation signal no longer matches the user-facing risk
5. the workflow depends on a mapping or assumption that is not written down anywhere

---

## Safe-Resume Rules

1. Prefer idempotent writes or conflict-safe insertion paths.
2. Keep translation state explicit when crossing system boundaries.
3. Use dry-run paths that exercise the real logic rather than bypassing it.
4. Rerun the smallest high-value validation before resuming after interruption.
5. Preserve stable client-facing contracts while internals change.

---

## Rollback Thinking

Rollback is not always full reversal. In this repo, rollback thinking should include:
- whether the action is dry-run only
- whether target rows can be safely re-derived on rerun
- whether contract regressions can be detected and corrected before release
- whether a human checkpoint is required before running a truly mutating operation

The exam is more likely to reward clear rollback reasoning than the claim that every workflow has a perfect undo button.

---

## Quick Study Exercise

Write one run ledger for:
1. a migration dry run
2. a real migration rehearsal plan
3. an auth-error contract check

For each, identify one drift signal, one invariant, and one validation command.