# Domain 4: Evaluation, Error Analysis, And Tuning

## Why This Domain Matters

Agentic systems become unreliable when teams start tuning before they have trustworthy evaluation signals. GH-600 tests whether you can define those signals, classify failures correctly, and make changes based on evidence rather than intuition.

Financius is strong here because it already has a useful evaluation surface:
- contract tests protect the response envelope
- unit tests capture view and migration behavior
- CI turns those checks into a repeatable gate

---

## What GH-600 Is Testing

You should be able to do four things:
- define success criteria before changing prompts, tools, or workflows
- distinguish reasoning failures from tool, policy, and environment failures
- choose the smallest useful validation loop after each change
- explain what evidence would justify further tuning versus escalation

---

## Repo Mapping

### `backend/tests/dj/contract/test_envelope_contract.py`

This is the clearest evaluation artifact in the repo.

What it teaches:
- contract tests define invariant behavior, not just point functionality
- the repo treats the `{ data, error, meta }` envelope as a stable client-facing contract
- evaluation can compare old and new systems during migration, not just test a single implementation in isolation

The strongest GH-600 insight here is that evaluation signals should reflect the thing downstream consumers actually depend on.

### `backend/tests/dj/unit/test_auth_views.py` and `backend/tests/dj/unit/test_migrate_from_sqlite.py`

These are narrower evaluation signals.

What they teach:
- root-cause-oriented tests help isolate failure classes
- migration and auth flows are especially useful because they combine state, validation, and edge handling

### `.github/workflows/ci.yml`

CI turns evaluation into a control loop.

What it teaches:
- the system has ordered gates
- evaluation artifacts are reproducible across runs
- deploy is downstream of lint, tests, and build rather than mixed together with them

---

## Worked Example: What The Envelope Contract Tests Really Measure

A shallow reading says the contract tests "check API responses."

A stronger reading says they do three deeper things:
1. preserve Android client compatibility during migration
2. compare the Django implementation against a Flask baseline where needed
3. provide a precise signal for whether a change is safe to ship from a consumer-contract perspective

That distinction matters in GH-600. Good evaluation signals are close to user impact.

---

## A Practical Error Taxonomy For This Repo

Use this four-part classification when studying failures:

### Reasoning or specification failure
The agent misunderstood the requirement, chose the wrong files, or proposed an invalid plan.

Example pattern:
- edits drift outside approved scope
- a review artifact does not address the acceptance criteria

### Tool misuse failure
The wrong tool was chosen, or the right tool was used in the wrong order.

Example pattern:
- broad mutation before confirming the controlling file
- retrying a validation command without addressing the real cause

### Environment failure
The code or command is valid, but the environment is missing dependencies, variables, services, or compatible data.

Example pattern:
- CI-only failure because an expected env var is not present locally
- database-dependent tests failing because the service is unavailable

### Policy or permission failure
The workflow is blocked because it crosses a risk or permission boundary.

Example pattern:
- a command is denied by policy
- an action should require approval but is attempted as autonomous work

---

## Tuning Loop To Practice

Use this loop when reviewing any agentic workflow:
1. choose one signal that actually matters
2. run the smallest validation that can falsify your current understanding
3. classify the failure before changing anything
4. tune only one thing at a time: instruction, tool choice, environment, or policy
5. rerun the same signal to confirm whether the change helped

If you tune several variables at once, you lose the ability to explain why the result changed.

---

## Common Failure Modes

### Tuning before measurement
Teams change prompts or tools because the output "feels wrong" without defining a stable signal first.

### Over-broad validation
Teams run a huge suite when a narrow, discriminating check was available.

### Misclassified failures
A policy failure gets treated like a model error, or an environment failure gets treated like a reasoning problem.

### No before/after evidence
The workflow changes, but nobody records what improved and what stayed the same.

---

## What Good Looks Like In An Exam Answer

If asked how to evaluate a repo migration workflow, a strong answer would say:
- define contract stability as the primary signal
- use focused unit tests for local behavior checks
- use CI as the final consistency gate
- classify failures into reasoning, tool, environment, and policy buckets before tuning
- rerun the same check after each tuning change to prove impact

---

## Self-Check

1. Why are contract tests stronger than generic "API works" checks in this repo?
2. What failure class would you assign to a missing CI secret?
3. Why should you rerun the same validation after a tuning change?
4. When is a broad test run the wrong first move?

---

## Next Steps

- Run [labs/lab-evaluation-and-tuning.md](labs/lab-evaluation-and-tuning.md)
- Review [backend/tests/dj/contract/test_envelope_contract.py](../../backend/tests/dj/contract/test_envelope_contract.py)
- Capture one real or simulated failure in the four-part taxonomy above