# Lab: Multi-Agent Coordination

## Goal

Simulate a coordinator-driven workflow for a medium-scope change using planner, implementer, and reviewer roles.

---

## Prerequisites

- read [../domain-5-multi-agent-coordination.md](../domain-5-multi-agent-coordination.md)
- read [../multi-agent-orchestration.md](../multi-agent-orchestration.md)

---

## Suggested Change Theme

Choose one medium-scope task such as:
- improving an API response validation path
- tightening a tool-governance doc
- adding a targeted test plus matching implementation clarification

Do not choose a destructive or deployment-affecting change for this lab.

---

## Files To Inspect

- `CLAUDE.md`
- `.github/workflows/ci.yml`
- `docs/gh600/multi-agent-orchestration.md`
- one feature-specific file set relevant to your chosen task

---

## Workflow To Simulate

### Planner phase
Produce:
- scope
- risk level
- files in scope
- validation checklist
- rollback note

### Implementer phase
Produce:
- summary of intended changes
- actual files touched
- commands run
- self-check results

### Reviewer phase
Produce:
- findings by severity
- contract or regression risks
- go, revise, or escalate recommendation

### Coordinator decision
Produce:
- final status
- whether scope stayed aligned
- whether conflicts were detected
- next authorized step

---

## What To Observe

1. Where can role boundaries blur if the artifacts are weak?
2. What conflict signal appears first when implementation drifts outside plan?
3. Which risks should automatically outrank delivery speed?
4. At what point should the coordinator stop the workflow and request human input?

---

## Reflection Prompts

Write short answers to these:
- What information was hardest to preserve across the handoff?
- Which role produced the highest-value artifact?
- What would have happened if the coordinator had not frozen the workflow when a conflict appeared?
- Which part of this process is already approximated by the repo's CI pipeline, and which part is missing?

---

## Completion Criteria

You are done when you can produce:
- one planner artifact
- one implementer artifact
- one reviewer artifact
- one coordinator decision summary
- one paragraph describing how a conflict would be handled in your chosen scenario