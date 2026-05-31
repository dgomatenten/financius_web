# Lab: Memory, State, And Execution

## Goal

Study how this repo preserves execution continuity, supports safe reruns, and protects downstream consumers from state drift.

---

## Prerequisites

- read [../domain-3-memory-state-execution.md](../domain-3-memory-state-execution.md)
- understand the difference between working context and durable execution state

---

## Files To Inspect

- `backend/ledger/management/commands/migrate_from_sqlite.py`
- `backend/tests/dj/unit/test_migrate_from_sqlite.py`
- `backend/financius_web/exception_handler.py`
- `backend/accounts/models.py`
- `backend/accounts/views.py`

---

## Suggested Commands

Run these from `backend/`.

```bash
pytest tests/dj/unit/test_migrate_from_sqlite.py -q
```

If you have a safe source database available for rehearsal, use the dry-run path:

```bash
python manage.py migrate_from_sqlite --sqlite-path /path/to/flask.db --dry-run
```

If you do not have a safe source database, treat the dry-run command as illustrative and focus on the tests.

---

## What To Observe

1. Which parts of the migration logic make reruns safe?
2. What state is explicit, and what state is derived during execution?
3. Why is the email-to-UUID mapping a critical continuity artifact?
4. How does the exception handler preserve stable output behavior even on errors?

---

## Reflection Prompts

Write short answers to these:
- What is the difference between dry-run safety and rollback readiness?
- What is one place where stale context would make this workflow dangerous?
- Which test best proves resumability or idempotency?
- Why does output-envelope stability belong in a discussion about state continuity?

---

## Completion Criteria

You are done when you can produce:
- a short run ledger for the migration workflow
- one paragraph explaining why rerun safety matters here
- one example of context drift and how you would detect it before continuing