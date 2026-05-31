# Domain 6: Guardrails And Accountability

## Why This Domain Matters

GH-600 expects you to control autonomy by risk. A system is not well-designed just because it can act. It has to know when to stop, what requires approval, and what evidence must be preserved after a decision.

This repo already contains the right raw materials for Domain 6:
- explicit command allow and deny patterns
- environment-driven configuration boundaries
- stable error handling and contract behavior
- a written autonomy matrix for risk levels

---

## What GH-600 Is Testing

You should be able to explain:
- how to map actions to autonomy levels
- which actions require human-in-the-loop approval
- why least privilege matters for agent tools and environments
- what accountability artifacts must be preserved
- when a workflow should be blocked instead of retried

---

## Repo Mapping

### `.claude/settings.json`

This file is the clearest guardrail artifact.

What it teaches:
- allowed actions should be explicit
- some actions should be hard-blocked even if related tool families are generally available
- post-edit validation can be attached automatically to mutations

The Domain 6 lesson is that guardrails are operational, not merely advisory.

### `backend/financius_web/settings.py`

This file shows environment-driven boundary control.

What it teaches:
- secrets and operational settings should come from environment variables
- defaults can exist for local development, but production-sensitive values must remain configurable
- environment handling itself is part of the safety model

### `backend/financius_web/exception_handler.py`

This file is an accountability surface.

What it teaches:
- when failures happen, the system still responds in a stable and inspectable structure
- accountability includes making error behavior auditable by downstream consumers

### `docs/gh600/autonomy-and-guardrails-matrix.md`

This is the strongest direct reference.

What it teaches:
- L0 through L3 autonomy levels
- approval paths for riskier actions
- evidence requirements for medium- and high-risk work

---

## The Core Guardrail Pattern

Think in four steps:
1. classify the action by risk
2. determine whether autonomy is allowed, constrained, or blocked
3. define the validation and evidence required before and after the action
4. preserve an audit trail for medium- and high-risk work

This matters because guardrails are not only about denial. They are about allowing low-risk work to move quickly while forcing explicit control over riskier actions.

---

## Worked Example: Why Least Privilege Matters Even In A Dev Repo

A weak reading of `.claude/settings.json` is: "the repo blocks force-push and dangerous deletes."

A stronger GH-600 reading is:
1. the policy narrows the command surface before execution starts
2. deny rules block high-risk actions even when other git or shell actions are broadly allowed
3. hooks attach validation behavior after mutation, which improves accountability
4. stale policy entries are themselves a guardrail risk because a policy that no longer matches reality can create false confidence

That last point is important. Guardrails have to be maintained, not only created.

---

## Human-In-The-Loop Thinking

In this repo, the most obvious approval-triggering cases are:
- schema or migration actions with real data impact
- auth or contract changes that may affect clients
- deployment or production-adjacent operations
- destructive or irreversible commands

A strong GH-600 answer should not only say, "require approval." It should also say what information the approval checkpoint must include:
- action being proposed
- risk level and impact radius
- rollback or mitigation path
- validation plan

---

## Common Failure Modes

### Approval-free risk creep
The workflow starts as low risk but expands into contract, auth, or deployment impact without reclassification.

### Blocking rules are advisory only
The system describes a restriction but does not actually stop execution when it is crossed.

### Accountability artifacts are missing
No plan, log, validation result, or escalation note survives after the action.

### Environment defaults become production assumptions
Local fallback values are treated as if they were an acceptable production safety model.

---

## What Good Looks Like In An Exam Answer

If asked how to implement guardrails in this repo, a strong answer would say:
- map actions to explicit autonomy levels such as L0 through L3
- keep low-risk read and local validation work autonomous
- require approval and rollback notes for migration, contract, auth, or deployment-impacting actions
- enforce least privilege through allow and deny patterns
- preserve auditability through logs, validation evidence, and stable error reporting

That answer is stronger than saying, "add human approval for risky changes," because it explains how risk, policy, and evidence fit together.

---

## Self-Check

1. Why is least privilege a speed enabler as well as a safety control?
2. What kind of action should move from L1 to L2 in this repo?
3. Why does stable error-envelope behavior contribute to accountability?
4. What is one sign that a workflow should be blocked instead of retried?

---

## Next Steps

- Review [autonomy-and-guardrails-matrix.md](autonomy-and-guardrails-matrix.md)
- Compare `.claude/settings.json` against `backend/financius_web/settings.py` and note where tool policy and environment policy reinforce each other
- Use Domain 6 together with [domain-2-tools-and-environment.md](domain-2-tools-and-environment.md) to distinguish tool governance from approval governance