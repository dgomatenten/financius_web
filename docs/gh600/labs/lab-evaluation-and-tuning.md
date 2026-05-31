# Lab: Evaluation, Error Analysis, And Tuning

## Goal

Use the repo's tests and CI flow as evaluation signals, then classify failures before deciding what to tune.

---

## Prerequisites

- read [../domain-4-evaluation-and-tuning.md](../domain-4-evaluation-and-tuning.md)
- understand the standard `{ data, error, meta }` envelope

---

## Files To Inspect

- `backend/tests/dj/contract/test_envelope_contract.py`
- `backend/tests/dj/unit/test_auth_views.py`
- `backend/tests/dj/unit/test_migrate_from_sqlite.py`
- `backend/financius_web/exception_handler.py`
- `.github/workflows/ci.yml`

---

## Suggested Commands

Run these from `backend/` unless noted.

```bash
pytest tests/dj/contract/test_envelope_contract.py -q
pytest tests/dj/unit/test_auth_views.py -q
pytest tests/dj/unit/test_migrate_from_sqlite.py -q
```

Optional broader check:

```bash
pytest tests/dj -q
```

---

## What To Observe

1. Which checks are validating stable contracts versus narrow internal behavior?
2. If a contract test fails, what downstream risk does that imply?
3. Which failures would count as reasoning failures, tool failures, environment failures, or policy failures?
4. How does CI reinforce the local evaluation loop?

---

## Reflection Prompts

Write short answers to these:
- Which test in this repo is your highest-value evaluation signal, and why?
- What is one failure you could easily misclassify if you were moving too fast?
- What is the smallest validation you would rerun after changing an auth or envelope-related workflow?
- What evidence would make you stop tuning and escalate instead?

---

## Completion Criteria

You are done when you can produce:
- a four-part failure taxonomy for this repo
- one worked example of a contract-risk failure and its validation path
- one before/after tuning loop written as signal, change, and result