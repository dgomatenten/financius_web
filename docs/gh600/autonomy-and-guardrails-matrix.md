# GH-600 Companion: Autonomy And Guardrails Matrix (Financius Web)

## Objective

Operationalize GH-600 Domain 6 (Implement guardrails and accountability) with explicit autonomy levels, approval paths, and evidence requirements for this repository.

## What GH-600 Is Testing Here

This domain is testing whether you can control autonomy by risk rather than by convenience.

You should be able to explain:
- which actions remain fully autonomous
- which actions require approval before execution
- what evidence must survive after medium- or high-risk work
- why blocked actions should stop the workflow rather than be retried casually

---

## Guardrail Principles

1. Least privilege by default.
2. Human approval for irreversible or compliance-sensitive actions.
3. Fast path for low-risk work to preserve delivery velocity.
4. Every non-trivial action leaves an audit trail.

Current baseline references:
- `.claude/settings.json`
- `.github/workflows/ci.yml`
- `CLAUDE.md`

Study note:
- the repo already has the raw pieces for a guardrail model, but a learner still needs to connect those pieces to actual approval decisions and audit artifacts

---

## Autonomy Levels

## L0: Read-only Autonomous
Definition:
- agent can inspect files, logs, and docs without mutation

Approval:
- none required

Examples:
- file search
- code reading
- documentation analysis

## L1: Low-risk Local Mutation Autonomous
Definition:
- agent can edit local code/docs and run local validation

Approval:
- none required when scope is clear and non-sensitive

Examples:
- refactor non-critical modules
- add/update tests
- documentation updates

Required checks:
- lint/test on touched area
- changed-file scope stays aligned to task

## L2: Controlled Mutation (Conditional Approval)
Definition:
- agent can perform broader code changes that may impact contracts or migrations

Approval:
- single maintainer approval before execution

Examples:
- API behavior adjustments
- schema migration generation
- auth-related code changes

Required checks:
- explicit plan artifact
- regression and contract checks
- rollback notes

## L3: High-risk / Irreversible (Human-in-the-loop Mandatory)
Definition:
- actions with production, security, or irreversible impact

Approval:
- explicit human approval, usually dual-review for sensitive operations

Examples:
- production deploy triggers
- destructive data operations
- credential/secret changes
- force push (blocked by policy)

Required checks:
- pre-action risk sign-off
- rollback tested or documented
- post-action verification evidence

## Worked Classification Examples

Use these repo examples to practice autonomy decisions:

| Action | Suggested Level | Why |
|---|---|---|
| reading source files and docs | L0 | no mutation and no environment risk |
| updating study docs and running quick review | L1 | local, low-risk mutation |
| editing auth behavior or contract-sensitive views | L2 | local change with client or security implications |
| local migration rehearsal on meaningful data | L2 | state-impacting with rollback concerns |
| deployment trigger or destructive cleanup | L3 | irreversible or production-adjacent |

The important skill is not memorizing the table. It is being able to justify why the same command family can move between levels depending on impact.

---

## Repo Action Matrix

| Action | Level | Auto Allowed | Human Approval | Control Source | Evidence Required |
|---|---|---|---|---|---|
| Search/read code | L0 | yes | no | default tooling | task notes |
| Edit docs | L1 | yes | no | local workflow | diff + quick review |
| Edit backend code | L1/L2 | conditional | for L2 | CLAUDE rules + CI | tests/lint outputs |
| Run pytest/ruff | L1 | yes | no | CI parity workflow | command results |
| Run DB migration locally | L2 | conditional | yes | maintainer policy | migration plan + output |
| Build docker image | L1 | yes | no | CI parity | build result |
| Trigger deploy | L3 | no | yes | GitHub + Render controls | deploy record + validation |
| Force push | L3 | no (blocked) | n/a | `.claude/settings.json` deny | n/a |
| Destructive delete operation | L3 | no | yes | policy + review | rollback and approval log |

## Worked Approval Example

Scenario:
- a change touches auth token behavior and may affect Android clients

Good handling:
1. classify it as L2, not L1
2. require a short plan artifact and rollback note before execution
3. require contract and auth validation after the change
4. block promotion to release until evidence is attached

This is stronger than saying "be careful with auth" because it translates concern into process.

---

## Human-In-The-Loop Checkpoints

Mandatory checkpoints:
1. before L2/L3 execution starts
2. when workflow stalls or context drift is detected
3. after critical review findings (security/contract/data)
4. before production-affecting actions

Checkpoint payload must include:
- proposed action
- risk level and rationale
- expected impact radius
- rollback path
- required validation plan

## Worked Human-In-The-Loop Checkpoint

```yaml
task_id: GH600-20260531-02
action: adjust auth refresh-token behavior
risk_level: L2
rationale: contract and client-auth compatibility may be affected
impact_radius:
	- backend auth endpoints
	- Android token refresh flow
rollback_path:
	- revert change set
	- rerun auth and contract tests
validation_plan:
	- pytest tests/dj/unit/test_auth_views.py -q
	- pytest tests/dj/contract/test_envelope_contract.py -q
approval_required: true
```

The exam is likely to favor answers that preserve this level of decision clarity.

---

## Policy Violations And Blocking Rules

Hard-block conditions:
- attempt to run denied commands
- out-of-scope edits without re-approval
- missing rollback for high-risk actions
- unresolved critical review findings

When blocked:
1. stop execution
2. emit violation summary
3. request human decision
4. resume only after explicit authorization

Why this matters:
- blocked actions are not transient failures
- retrying a blocked action is itself a guardrail failure

---

## Accountability Artifacts

For each medium/high-risk run, store:
- plan artifact
- command/action log
- validation evidence
- approval records
- escalation events
- final disposition

Suggested path:
- `docs/gh600/runs/<task_id>/`

## What A Strong Exam Answer Sounds Like

For this repo, a strong answer would say:
- keep L0 and most L1 work autonomous to preserve delivery speed
- require L2 approval for contract, auth, or migration-sensitive changes
- reserve L3 for deployment, destructive, or irreversible actions
- preserve plan, validation, and escalation artifacts so actions remain auditable

---

## Velocity Protection Rules

To avoid over-approval bottlenecks:
1. keep L0/L1 fully autonomous where safe.
2. require approvals only where risk materially increases.
3. pre-approve standard low-risk patterns (docs/tests/refactors).
4. use reusable checklists for frequent L2 actions.

This balances GH-600 guardrail rigor with practical delivery speed.

---

## Quick Implementation Steps

1. Adopt autonomy levels L0-L3 in team workflow docs.
2. Add a short approval template for L2/L3 tasks.
3. Require run artifacts for medium/high-risk work.
4. Review `.claude/settings.json` quarterly to keep least-privilege current.
5. Align CI checks with guardrail policy updates.

## Self-Check

1. Why can the same code-editing workflow be L1 in one case and L2 in another?
2. What makes a blocked action different from a normal failed command?
3. Why does guardrail design need both speed protection and approval checkpoints?
4. What evidence should always survive an L2 or L3 action?
