# Interactive Daily GH-600 Study Plan (Financius Web)

## How To Use This Plan

This is a 30-day, hands-on GH-600 prep guide tied directly to this repository.

Session structure per day:
1. Read focus artifacts.
2. Execute hands-on task.
3. Run validation commands.
4. Self-score with rubric.
5. Log evidence.

Daily time target:
- 45 to 75 minutes

Definition of done for each day:
- All required checkboxes marked
- Validation command output captured
- Daily score recorded

---

## Baseline Setup (Run Once Before Day 1)

- [ ] Confirm repository is clean enough to work
- [ ] Confirm local Python and dependencies are ready
- [ ] Confirm tests run locally
- [ ] Confirm Docker build works locally

Commands:

```bash
cd backend
pytest tests/dj -q
ruff check accounts ledger financius_web tests/dj

cd ..
docker build -f infra/docker/backend.Dockerfile -t financius-web:study .
```

If any command fails:
- [ ] Record failure reason in your daily log
- [ ] Fix environment before proceeding

---

## Scoring Rubric (Use Every Day)

Score each category from 0 to 2:
- Understanding
- Execution quality
- Validation completeness
- Risk awareness
- Documentation quality

Daily score formula:
- Max = 10
- Green = 8 to 10
- Yellow = 6 to 7
- Red = 0 to 5

Action rule:
- Green: continue
- Yellow: do 1 remediation task next day before new content
- Red: repeat same day with smaller scope

---

## Week 1 (Days 1-7): Architecture And SDLC Integration

## Day 1 - GH-600 Map + Repo Control Plane
Focus files:
- CLAUDE.md
- .claude/CLAUDE.md
- .github/workflows/ci.yml

Tasks:
- [ ] Summarize how this repo separates planning, execution, and validation
- [ ] Identify one anti-pattern this repo avoids
- [ ] Identify one anti-pattern still possible

Validation:
- [ ] Explain (in writing) why CI is a control plane artifact

## Day 2 - Planning vs Action Boundaries
Focus files:
- CLAUDE.md
- docs/gh600/study-guide-financius-gh600.md

Tasks:
- [ ] Write a planning gate checklist for medium/high-risk changes
- [ ] Define required plan output fields: scope, risk, rollback, validation

Validation:
- [ ] Create a sample plan for a hypothetical auth endpoint change

## Day 3 - Observability And Inspectable Artifacts
Focus files:
- .github/workflows/ci.yml
- backend/tests/dj/contract/test_envelope_contract.py

Tasks:
- [ ] List observable artifacts produced by current workflow
- [ ] Propose 2 additional artifacts for better auditability

Validation:
- [ ] Map each artifact to one GH-600 objective bullet

## Day 4 - Agent Responsibilities In SDLC
Focus files:
- docs/gh600/multi-agent-orchestration.md
- CLAUDE.md

Tasks:
- [ ] Define planner vs implementer vs reviewer responsibilities for this repo
- [ ] Add boundaries for what each role must never do

Validation:
- [ ] Produce one handoff artifact for each role

## Day 5 - Safe Intervention Without Slowing Delivery
Focus files:
- .claude/settings.json
- docs/gh600/autonomy-and-guardrails-matrix.md

Tasks:
- [ ] Identify approvals that materially reduce risk
- [ ] Identify approvals that do not and should be removed

Validation:
- [ ] Propose one velocity optimization preserving guardrails

## Day 6 - Mini Drill: Architecture Domain
Tasks:
- [ ] Run a mock feature request through planning artifact only (no coding)
- [ ] Include success criteria and rollback strategy

Validation:
- [ ] Self-review with GH-600 domain checklist

## Day 7 - Week 1 Assessment
Tasks:
- [ ] 20-question self-quiz (create from your notes)
- [ ] Re-explain week 1 concepts without looking at docs

Validation:
- [ ] Score >= 8/10 or schedule remediation block

---

## Week 2 (Days 8-14): Tool Use, MCP, Environment Interaction

## Day 8 - Tool Inventory + Risk Classes
Focus files:
- .claude/settings.json
- docs/gh600/mcp-and-tools-profile.md

Tasks:
- [ ] Classify current tools into L0/L1/L2/L3 style categories
- [ ] Mark which tools are read-only vs mutating

Validation:
- [ ] Explain one least-privilege improvement

## Day 9 - MCP Fundamentals (Repo-Specific)
Focus files:
- docs/gh600/mcp-and-tools-profile.md

Tasks:
- [ ] Draft a minimal .mcp.json design for this repo
- [ ] Define scope and permissions for first MCP server

Validation:
- [ ] Write a short allow-list policy statement

## Day 10 - CI Integration For Tool Safety
Focus files:
- .github/workflows/ci.yml
- docs/gh600/mcp-and-tools-profile.md

Tasks:
- [ ] Define CI checks for .mcp.json validity
- [ ] Define failure behavior when policy violations are detected

Validation:
- [ ] Draft check commands and expected output

## Day 11 - Environment Context And Constraints
Focus files:
- infra/compose/docker-compose.yml
- infra/docker/backend.Dockerfile
- scripts/run_services.sh

Tasks:
- [ ] Identify environment-specific constraints and how to encode them
- [ ] Document one safe path for local and one for CI

Validation:
- [ ] Execute local docker build and backend tests

Commands:

```bash
cd backend
pytest tests/dj -q

cd ..
docker build -f infra/docker/backend.Dockerfile -t financius-web:study .
```

## Day 12 - Error Handling Paths (Retry, Rollback, Escalation)
Focus files:
- scripts/run_services.sh
- docs/gh600/mcp-and-tools-profile.md

Tasks:
- [ ] Define transient vs non-transient failure patterns
- [ ] Define retry budget and escalation threshold
- [ ] Define rollback trigger list

Validation:
- [ ] Simulate one failure and classify correctly

## Day 13 - Traceability For Tool Actions
Focus files:
- backend/accounts/views.py
- backend/ledger/views.py

Tasks:
- [ ] Identify logged action points that aid audits
- [ ] Define missing traceability fields for future runs

Validation:
- [ ] Produce one sample execution trace record

## Day 14 - Week 2 Assessment
Tasks:
- [ ] Build a one-page tool governance summary
- [ ] Teach it aloud in under 8 minutes

Validation:
- [ ] Score >= 8/10 or repeat Day 10-12 drills

---

## Week 3 (Days 15-21): Memory, State, Evaluation, Tuning

## Day 15 - Memory Models In Practice
Focus files:
- backend/ledger/management/commands/migrate_from_sqlite.py
- docs/gh600/study-guide-financius-gh600.md

Tasks:
- [ ] Identify short-term vs durable state examples in repo
- [ ] Map where context drift can occur

Validation:
- [ ] Create drift detection checklist (5 items minimum)

## Day 16 - Resumability And Idempotency
Focus files:
- backend/ledger/management/commands/migrate_from_sqlite.py
- backend/tests/dj/unit/test_migrate_from_sqlite.py

Tasks:
- [ ] Explain idempotency guarantees in migration flow
- [ ] Explain dry-run behavior and why it matters

Validation:
- [ ] Run one dry-run thought experiment and expected outcomes

## Day 17 - Evaluation Signal Design
Focus files:
- backend/tests/dj/contract/test_envelope_contract.py
- backend/tests/dj/unit/test_auth_views.py

Tasks:
- [ ] Define qualitative and quantitative success signals
- [ ] Separate contract vs behavior vs reliability signals

Validation:
- [ ] Build a simple pass/fail matrix for one endpoint

## Day 18 - Root Cause Analysis Practice
Focus files:
- backend/accounts/views.py
- backend/financius_web/exception_handler.py

Tasks:
- [ ] Create 4 failure scenarios
- [ ] Classify root cause: reasoning, tool misuse, context, environment

Validation:
- [ ] Provide one fix per scenario and expected verification

## Day 19 - Tuning Loop 1
Tasks:
- [ ] Choose one instruction/workflow tweak
- [ ] Run baseline checks
- [ ] Apply tweak
- [ ] Re-run checks and compare

Validation commands:

```bash
cd backend
pytest tests/dj -q
ruff check accounts ledger financius_web tests/dj
```

## Day 20 - Tuning Loop 2
Tasks:
- [ ] Repeat Day 19 with a different variable (tool scope, prompt constraints, or validation gate)
- [ ] Capture before/after evidence

Validation:
- [ ] Document whether change reduced risk or improved velocity

## Day 21 - Week 3 Assessment
Tasks:
- [ ] Produce one-page evaluation and tuning report
- [ ] Include taxonomy, evidence, and next tuning candidates

Validation:
- [ ] Score >= 8/10

---

## Week 4 (Days 22-30): Multi-Agent Coordination + Guardrails Mastery

## Day 22 - Workflow Assembly
Focus files:
- docs/gh600/multi-agent-orchestration.md
- docs/gh600/autonomy-and-guardrails-matrix.md

Tasks:
- [ ] Prepare coordinator playbook for one feature task
- [ ] Prepare planner/implementer/reviewer handoff templates

Validation:
- [ ] Verify all templates include risks and escalation fields

## Day 23 - Parallel Work And Isolation
Tasks:
- [ ] Design two parallel work streams on non-overlapping scopes
- [ ] Define isolation boundaries and merge checkpoints

Validation:
- [ ] Define conflict detection signal list

## Day 24 - Conflict Resolution Drill
Tasks:
- [ ] Simulate contradictory outputs between implementer and reviewer
- [ ] Execute conflict protocol from the orchestration guide

Validation:
- [ ] Produce final coordinator decision with rationale

## Day 25 - Failure Recovery Drill
Tasks:
- [ ] Simulate partial completion and stalled execution
- [ ] Apply recovery patterns and escalation logic

Validation:
- [ ] Record exact trigger that moved to human-in-the-loop

## Day 26 - Autonomy Matrix Deep Dive
Focus files:
- docs/gh600/autonomy-and-guardrails-matrix.md
- .claude/settings.json

Tasks:
- [ ] Map 10 real repo actions to L0-L3
- [ ] Identify 2 policy gaps and propose controls

Validation:
- [ ] Confirm no high-risk action is auto-approved

## Day 27 - Accountability Artifacts
Tasks:
- [ ] Build one complete run folder skeleton for medium/high-risk work
- [ ] Include approvals, logs, validation results, final disposition

Validation:
- [ ] Perform peer-style audit against your own artifact

## Day 28 - Full Simulation (End-to-End)
Tasks:
- [ ] Run a complete simulated cycle: plan -> implement -> review -> decision
- [ ] Enforce all guardrails and escalation rules

Validation:
- [ ] Produce a go/no-go report with evidence links

## Day 29 - Weak Area Remediation Day
Tasks:
- [ ] Pick your two lowest-scoring domains
- [ ] Re-run the hardest drill from each

Validation:
- [ ] Reach >= 8/10 on both domains

## Day 30 - Final Readiness Day
Tasks:
- [ ] 60-minute capstone oral walkthrough (all six GH-600 domains)
- [ ] Recreate key artifacts from memory
- [ ] Run final validation commands

Commands:

```bash
cd backend
pytest tests/dj -q
ruff check accounts ledger financius_web tests/dj

cd ..
docker build -f infra/docker/backend.Dockerfile -t financius-web:final-readiness .
```

Final gate:
- [ ] Average score over last 7 days >= 8/10
- [ ] No red days in final week
- [ ] Can explain trade-offs among safety, autonomy, and delivery speed

---

## Daily Interactive Log Prompt (Copy Each Day)

- Date:
- Day number:
- Domain focus:
- Time spent:
- Today objective:
- Checkboxes completed:
- Commands executed:
- Results summary:
- Biggest risk discovered:
- Fix or mitigation:
- Score (0-10):
- Tomorrow first task:

---

## Adaptive Path Rules

If two consecutive days are Yellow:
- reduce scope by 30 percent
- spend first 20 minutes reviewing prior evidence
- delay new domain until one Green day

If one day is Red:
- repeat the same day plan with half scope
- ask one peer or reviewer to inspect your artifact
- do not advance until score >= 7

If three Greens in a row:
- add one stretch task:
  - stricter guardrail policy
  - deeper failure simulation
  - tighter evidence requirements

---

## Suggested Stretch Tasks (Optional)

- Create .mcp.json and add CI validation
- Build docs/gh600/runs directory structure with one full example run
- Add a reusable review checklist template for contract and safety checks
- Add a policy doc for escalation SLAs

This plan is intentionally execution-heavy so you build exam-ready operational judgment, not just theory.
