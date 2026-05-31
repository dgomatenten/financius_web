# GH-600 Companion: Evaluation And Tuning Report

## Objective

Provide a worked reference for Domain 4 using the Financius repo's contract tests, unit tests, CI checks, and error-handling behavior.

This document covers:
- a practical error taxonomy
- worked failure classifications
- before/after tuning examples
- how to use repo evidence instead of intuition

---

## Evaluation Signals In This Repo

### Contract-level signals
- `backend/tests/dj/contract/test_envelope_contract.py`

These are high-value because they protect client-facing invariants, especially during migration from Flask to Django.

### Behavior-level signals
- `backend/tests/dj/unit/test_auth_views.py`
- `backend/tests/dj/unit/test_migrate_from_sqlite.py`

These are useful for narrowing the cause of a failure without immediately jumping to the whole suite.

### Control-plane signals
- `.github/workflows/ci.yml`

These are useful because they represent the final gated environment where lint, tests, build, and deploy ordering matter.

---

## Error Taxonomy

Use this four-part taxonomy when studying or debugging agentic workflows in this repo.

### Reasoning or specification issue
The plan, interpretation, or file targeting is wrong.

Typical signs:
- wrong file chosen as the controlling implementation surface
- implementation does not match accepted scope
- response proposes the wrong success criteria

### Tool misuse issue
The wrong tool or validation order was chosen.

Typical signs:
- broad edits before confirming the local control path
- retries without addressing the actual failure condition
- using a destructive or broad-scope tool where read-only inspection would suffice

### Environment issue
The logic may be fine, but the surrounding runtime is not ready.

Typical signs:
- missing environment variables
- unavailable database or service dependencies
- CI-only failure caused by missing runtime assumptions

### Policy or permission issue
The action crosses a boundary and should be blocked or escalated.

Typical signs:
- denied command pattern
- high-risk action attempted without approval
- workflow continues despite unresolved review findings

---

## Worked Failure Classifications

## Example 1: Contract envelope mismatch after endpoint change

Signal:
- `test_envelope_contract.py` fails on a route that no longer returns `{ data, error, meta }`

Classification:
- primary: reasoning or specification issue
- possible secondary: review failure if the change bypassed the expected contract check

Why:
- the repo has a stable contract requirement, so the issue is not that the test is too strict
- the more likely problem is that the implementation or plan ignored a stated invariant

Immediate next step:
- rerun the narrow contract test for the affected route and inspect the response shape before changing anything else

## Example 2: `pytest tests/dj/unit/test_auth_views.py -q` fails locally because JWT secret is missing

Classification:
- environment issue

Why:
- the test behavior depends on configured secrets and runtime settings
- the implementation is not yet disproven

Immediate next step:
- correct the environment and rerun the same narrow test before widening the investigation

## Example 3: An operator retries a failing migration command without checking why it failed

Classification:
- tool misuse issue

Why:
- repeated execution without diagnosis can turn a narrow failure into a state-integrity risk

Immediate next step:
- inspect the failure, confirm the current durable state, and rerun the smallest relevant validation first

## Example 4: A workflow attempts a deployment or destructive action without an approval checkpoint

Classification:
- policy or permission issue

Why:
- the problem is not model intelligence or code correctness first; it is that the workflow crossed a guardrail boundary

Immediate next step:
- stop, surface the blocked action, and request the required approval or escalation decision

## Example 5: Planner scope says docs-only, but implementation touches an API view and contract risk appears

Classification:
- primary: reasoning or specification issue
- secondary: coordination failure

Why:
- the work left the approved scope, and the resulting risk must be evaluated against the changed artifact set rather than the original plan alone

Immediate next step:
- freeze the workflow, compare actual file changes against approved scope, and hand the conflict to the coordinator or reviewer path

---

## Before/After Tuning Examples

## Tuning loop 1: Use narrower evaluation first

Before:
- run the entire `pytest tests/dj -q` suite immediately after a contract-related change

Problem:
- the signal is too broad for the first debugging move, so diagnosis is slower

Tuning change:
- run `pytest tests/dj/contract/test_envelope_contract.py -q` first, then widen only if needed

After:
- failures are localized faster
- the workflow better matches GH-600's preference for the cheapest falsifying check

## Tuning loop 2: Classify failure before retrying

Before:
- rerun a failing command as if every failure were transient

Problem:
- environment and policy failures do not improve with blind retry

Tuning change:
- classify the failure into reasoning, tool, environment, or policy before deciding whether retry is valid

After:
- fewer wasted reruns
- clearer escalation decisions
- better auditability of why the next action was chosen

---

## How To Use CI As Evidence

CI should be treated as the final consistency gate, not the first debugging instrument for every problem.

Good sequence:
1. run the smallest relevant local signal first
2. fix or classify the issue
3. rerun the same narrow signal
4. only then rely on CI to confirm that the larger workflow still holds together

This sequence is useful in both GH-600 exam answers and real engineering practice because it preserves causal clarity.

---

## Quick Study Exercise

Take three failures from this repo, real or simulated, and write them in this format:

```text
signal:
classification:
why:
smallest next validation:
tuning change if needed:
evidence after rerun:
```

If you cannot name the smallest next validation, you probably have not identified the controlling surface yet.