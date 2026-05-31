# Domain 1: Agent Architecture And SDLC Processes

## Why This Domain Matters

GH-600 starts with architecture and SDLC discipline because agentic systems become unsafe long before they become technically impressive if planning, execution, and review are mixed together without control points.

This repo already demonstrates a useful architecture pattern for the exam:
- policy is written down in repo-level instructions
- execution happens through constrained commands and workflows
- validation is externalized into tests and CI

That separation is the beginning of an agent architecture, even before formal subagents are introduced.

---

## What GH-600 Is Testing

You should be able to explain:
- how agents fit into different SDLC stages
- why planning and execution should be separated
- what artifacts make an agent workflow inspectable
- how control planes and policy files reduce unsafe autonomy
- when a workflow should pause for review instead of continuing automatically

---

## Repo Mapping

### `CLAUDE.md`

This is the strongest Domain 1 anchor in the repo.

What it teaches:
- high-level system principles are made explicit
- architecture constraints are stated before implementation begins
- role expectations are separated from individual tasks
- policy exists outside the code that the workflow mutates

The most important GH-600 lesson here is that architecture rules must be inspectable by humans, not only inferred from agent behavior after the fact.

### `.claude/commands/django.md` and `.claude/commands/django-new.md`

These files show that execution behavior can be packaged into reusable task patterns.

What they teach:
- repeated workflows should be standardized
- scaffolding and implementation flows can encode quality expectations up front
- skill routing is part of the SDLC, not an afterthought

### `.github/workflows/ci.yml`

CI is the clearest control-plane example.

What it teaches:
- validation stages are explicit and ordered
- successful execution is not enough; the result must pass the declared quality gates
- deployment is downstream of validation, not mixed into the same unchecked step

---

## The Core Architecture Pattern

Use this mental model when answering Domain 1 questions:

### Policy layer
Defines what is allowed, required, and out of bounds.

Repo examples:
- `CLAUDE.md`
- `.claude/settings.json`

### Execution layer
Performs the work using approved commands, tools, and scoped tasks.

Repo examples:
- repo scripts
- command files under `.claude/commands/`
- local docker and Django workflows

### Validation layer
Confirms whether the execution respected quality and safety requirements.

Repo examples:
- `pytest` and `ruff`
- contract tests
- CI jobs in `.github/workflows/ci.yml`

If you collapse these layers together, the workflow becomes hard to review and harder to trust.

---

## Worked Example: Why `CLAUDE.md` Is More Than A Prompt File

A weak reading of `CLAUDE.md` is: "it contains instructions for the coding agent."

A stronger GH-600 reading is:
1. it acts as a system-of-record for operating principles
2. it defines architectural constraints before implementation work starts
3. it routes work toward different skills depending on task type
4. it creates a planning boundary between what should happen and how that work is later executed

This matters because exam questions often test whether you recognize governance artifacts as part of architecture rather than mere documentation.

---

## SDLC Placement Of Agents In This Repo

### Planning
Best anchored in:
- `CLAUDE.md`
- design and strategy skill routing
- repo principles around portability, configuration, and API stability

### Implementation
Best anchored in:
- constrained commands
- reusable command/skill workflows
- repo-local code edits and validation loops

### Review and release
Best anchored in:
- `ruff`, `pytest`, and contract checks
- `.github/workflows/ci.yml`
- explicit deployment separation on `main`

The GH-600 idea is that different phases need different autonomy and evidence rules.

---

## Common Failure Modes

### Planning and execution collapse together
The same workflow invents scope and edits code without any inspectable approval point.

### Policy is implicit
The team relies on memory or habit instead of documented constraints.

### Validation comes too late
The workflow does broad mutation before any narrow confirmation step.

### Architecture drift
The policy docs still describe an older system shape while implementation has moved on.

---

## What Good Looks Like In An Exam Answer

If asked how this repo supports agent architecture and SDLC control, a strong answer would say:
- architectural principles are centralized in `CLAUDE.md`
- execution patterns are routed through reusable command and skill surfaces
- CI acts as an inspectable control plane for validation and release gating
- planning, implementation, and review are intentionally separated rather than merged into one opaque workflow

That answer is stronger than saying, "the repo has docs and CI," because it explains the role each artifact plays in the SDLC.

---

## Self-Check

1. Why should policy live outside the code being changed?
2. What makes CI part of the architecture rather than just an automation convenience?
3. Why is skill routing relevant to SDLC design?
4. What is one signal that planning and execution have been collapsed too aggressively?

---

## Next Steps

- Review `CLAUDE.md` and `.github/workflows/ci.yml` together as policy-versus-control-plane artifacts
- Compare Domain 1 with [domain-5-multi-agent-coordination.md](domain-5-multi-agent-coordination.md) to see how architecture patterns later become explicit orchestration patterns