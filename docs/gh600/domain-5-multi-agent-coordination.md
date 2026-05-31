# Domain 5: Multi-Agent Coordination

## Why This Domain Matters

GH-600 does not only test whether you can call multiple agents. It tests whether you can define role boundaries, preserve observability, resolve conflicts, and decide when a coordinator must stop autonomous progress and escalate.

This repo is a good teaching surface because it already has role-like separation in policy and validation, but it still needs explicit handoff discipline to become a true multi-agent workflow.

---

## What GH-600 Is Testing

You should be able to explain:
- when to split work across specialized agents
- why a coordinator is different from a worker
- what must be in a handoff artifact
- how to detect and resolve conflicts across agent outputs
- when to stop the workflow and require human approval

---

## Repo Mapping

### `CLAUDE.md`

This file already introduces role routing and skill selection.

What it teaches:
- not every task should be handled the same way
- routing rules are part of orchestration design
- a system of specialized behaviors can exist even before formal subagents are added

### `.github/workflows/ci.yml`

CI is not a multi-agent system, but it is a useful orchestration analogy.

What it teaches:
- stages have dependencies
- downstream work waits for upstream validation
- deploy should not run until earlier phases succeed

### `docs/gh600/multi-agent-orchestration.md`

This is the strongest direct reference.

What it teaches:
- coordinator-driven orchestration
- planner, implementer, and reviewer role boundaries
- handoff schema and conflict protocol

---

## The Core Pattern To Learn

Use a coordinator with three worker roles:
- planner: defines scope, risks, success criteria, and validation
- implementer: performs approved changes only
- reviewer: checks contract, regression, and policy risks

This pattern matters because it separates three failure types that get blurred in a single-agent workflow:
- bad planning
- bad execution
- bad review discipline

---

## Worked Example: How Conflict Resolution Should Work

Imagine a planner says a change is low-risk and limited to docs plus tests. The implementer edits an API view as well. The reviewer then flags contract risk because a response shape may have changed.

The correct coordinator response is not to keep moving. It is to freeze the workflow and resolve the conflict.

A strong response looks like this:
1. compare planner scope to the actual changed files
2. collect the reviewer evidence and failing or at-risk checks
3. apply priority order: security and contract correctness outrank delivery speed
4. either narrow the scope and redo implementation, or escalate to a human decision

This is the kind of judgment GH-600 is targeting.

---

## Mandatory Handoff Thinking

Each phase handoff should answer the same questions:
- what task is being advanced
- what files or artifacts were used as input
- what decision was made
- what risks remain
- what validation has already run
- what exact next step is authorized

If a handoff leaves those questions unanswered, the next agent is forced to infer too much. That is how coordination drift starts.

---

## Common Failure Modes

### Role overlap
The planner starts editing or the reviewer starts redesigning the task instead of reviewing it.

### Missing coordinator authority
Agents disagree, but there is no explicit rule for who resolves the disagreement.

### Weak handoff artifacts
The next agent gets prose without scope, evidence, or next-step clarity.

### Hidden conflicts
Changed files drift outside approved scope, but nobody compares the plan against the implementation.

---

## What Good Looks Like In An Exam Answer

If asked how to design multi-agent coordination for this repo, a strong answer would say:
- use a coordinator-driven pattern
- give planner, implementer, and reviewer distinct permissions and outputs
- require a structured handoff artifact at every phase
- freeze writes when scope conflicts or contract risks appear
- use human escalation for high-risk or unresolved conflicts

That answer is stronger than simply saying, "use multiple agents for speed," because it explains how the coordination stays safe and inspectable.

---

## Self-Check

1. Why should a reviewer be unable to modify code during the review phase?
2. What is the coordinator's job when planner scope and implementation scope diverge?
3. Why is a CI pipeline a useful analogy for orchestration but not the same thing as multi-agent coordination?
4. What information must every handoff artifact preserve?

---

## Next Steps

- Run [labs/lab-multi-agent-workflow.md](labs/lab-multi-agent-workflow.md)
- Review [multi-agent-orchestration.md](multi-agent-orchestration.md)
- Practice writing a planner-to-implementer handoff using one medium-scope repo change