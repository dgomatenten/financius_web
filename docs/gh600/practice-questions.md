# GH-600 Practice Questions

## How To Use This File

Use this question bank after reading the domain notes and companion references.

If you are studying through GitHub Copilot instead of Claude Code, translate the config terms as you go:
- `CLAUDE.md` maps conceptually to `copilot-instructions.md`
- `.claude/commands/` maps to reusable prompt or task-entry files
- `.claude/skills/` maps to specialized prompt or agent customizations
- `.claude/settings.json` maps to tool and agent configuration controls

Recommended loop:
1. answer one domain section without looking at the notes
2. check the answer key and rationale
3. revisit the linked study material for any weak area
4. finish with the mixed mock section

The questions are intentionally weighted toward scenario reasoning instead of pure recall. That matches the kind of operational judgment GH-600 is more likely to reward.

---

## Domain 1: Agent Architecture And SDLC Processes

### Questions

1. Why is `CLAUDE.md` a Domain 1 artifact rather than just a convenience file for prompting? If you are thinking in Copilot terms, answer the same question for `copilot-instructions.md`.

2. In this repo, what is the clearest example of a validation control plane, and why does it belong in the architecture discussion?

3. A workflow writes code first and only later decides what success criteria should have been. What Domain 1 failure does that represent?

4. Which answer best describes the relationship between policy, execution, and validation in this repo?

A. They are combined inside the same scripts so the workflow moves faster.

B. Policy is documented separately, execution uses constrained workflows, and validation is externalized into tests and CI.

C. Validation replaces the need for policy.

D. Execution can define policy as it goes if the final tests pass.

### Answer Key And Rationale

1. `CLAUDE.md` is a system-of-record artifact because it captures architectural principles, operating constraints, and task routing outside the code being changed. GH-600 cares about inspectable governance, not only model behavior. The same reasoning applies if the file is named `copilot-instructions.md`.

2. `.github/workflows/ci.yml` is the clearest validation control plane because it stages lint, test, docker build, and deploy gating in an ordered pipeline. That makes the architecture auditable rather than implicit.

3. It represents a collapse of planning and execution. The workflow moved into mutation before the planning artifact and success criteria were stable.

4. Correct answer: B. This repo separates policy, execution, and validation into different artifacts, which is exactly the architecture pattern Domain 1 is testing.

---

## Domain 2: Tool Use And Environment Interaction

### Questions

1. Why is a read-only MCP server the right first MCP addition for this repo?

2. `.claude/settings.json` still contains Flask-era environment entries. What is the best GH-600 interpretation of that fact?

A. It is harmless because only the current runtime matters.

B. It is a useful example of policy drift and shows why tool-governance artifacts need maintenance.

C. It means the repo cannot use Django at all.

D. It should be ignored because MCP is more important than shell policy.

3. A contributor proposes adding a write-capable filesystem MCP server before any read-only server exists. What is the strongest response?

4. What is the difference between retry policy and rollback policy in this repo's tool strategy?

### Answer Key And Rationale

1. A read-only server improves inspectability while keeping blast radius low. It aligns with minimum viable capability and gives the team a safer first tool-governance artifact.

2. Correct answer: B. GH-600 rewards recognizing that configuration and policy artifacts can drift away from system reality, which creates governance risk.

3. Reject it as the first MCP addition, require risk classification and owner, and require proof that existing local mutation paths are insufficient. The key issue is unnecessary expansion of write scope.

4. Retry policy handles transient operational failures. Rollback policy handles cases where a mutating or environment-impacting action may need to be reversed or contained. They solve different risk classes.

---

## Domain 3: Memory, State, And Execution

### Questions

1. Why is `migrate_from_sqlite.py` a strong Domain 3 example rather than just a data-copying script?

2. In the migration workflow, what role does the email-to-UUID translation map play?

A. It is a logging convenience.

B. It is temporary formatting data with no effect on correctness.

C. It is a continuity artifact that preserves identifier meaning across systems.

D. It only exists to make the code shorter.

3. Why does the standard `{ data, error, meta }` envelope belong in a Domain 3 discussion?

4. A workflow reruns a migration without idempotency controls and duplicates rows. What type of Domain 3 failure is that?

### Answer Key And Rationale

1. It manages execution state across two systems, preserves identifier meaning, supports dry-run rehearsal, and stays safe on rerun. That makes it a state and resumability example.

2. Correct answer: C. The mapping is not cosmetic. It preserves the meaning of foreign-key references when moving from Flask's identifier scheme to Django's.

3. Stable response shape is part of continuity for downstream consumers. State continuity includes preserving interface behavior, not only database correctness.

4. It is a replay-without-idempotency failure. The workflow cannot resume or rerun safely because durable state is not being handled correctly.

---

## Domain 4: Evaluation, Error Analysis, And Tuning

### Questions

1. Why are the envelope contract tests a stronger signal than a generic statement that the API "still works"?

2. A test fails locally because the required JWT secret is missing from the environment. How should that failure be classified first?

A. reasoning issue

B. tool misuse issue

C. environment issue

D. coordination issue

3. Why should you rerun the same focused validation after a tuning change instead of switching immediately to a broader suite?

4. What is wrong with tuning prompts, tools, and validation order all at once after a single failure?

### Answer Key And Rationale

1. The contract tests protect a real client-facing invariant: the stable response envelope that Android and web clients depend on. They are therefore closer to user impact.

2. Correct answer: C. Missing runtime configuration is an environment problem until proven otherwise.

3. Rerunning the same focused check preserves causal clarity. It tells you whether the specific tuning change improved the exact signal that motivated the change.

4. You lose the ability to explain why the result changed. GH-600 favors evidence-based tuning with one variable changed at a time.

---

## Domain 5: Multi-Agent Coordination

### Questions

1. Why is a coordinator not interchangeable with a planner in a multi-agent workflow?

2. Planner scope authorizes docs and tests only, but the implementer also edits an API view. What should happen next?

A. Continue if the implementer believes the change is low risk.

B. Let the reviewer fix the code directly during review.

C. Freeze the workflow, compare actual changes to approved scope, and resolve or escalate the conflict.

D. Ignore the extra file if tests still pass.

3. What is the minimum information a safe handoff artifact should preserve?

4. Why is "use multiple agents for speed" an incomplete GH-600 answer?

### Answer Key And Rationale

1. The coordinator owns gating, conflict resolution, and escalation across roles. A planner defines scope, but does not adjudicate the entire workflow once execution and review outputs diverge.

2. Correct answer: C. Scope drift plus potential contract impact is exactly the situation where the coordinator should freeze writes and resolve the conflict.

3. At minimum: task identity, phase owner, inputs, outputs, decisions, risks, validation state, and the next authorized step.

4. Because orchestration is about safe coordination, not just parallelism. GH-600 expects role boundaries, handoff quality, conflict handling, and observability.

---

## Domain 6: Guardrails And Accountability

### Questions

1. Why can the same code-editing workflow be L1 in one case and L2 in another?

2. A change touches auth token behavior and may affect Android clients. What is the most appropriate autonomy level?

A. L0 because it starts with reading files

B. L1 because it is still local code editing

C. L2 because it has contract and client-impact implications

D. L3 only if CI fails

3. Why is a blocked action different from a normal failed command?

4. What accountability artifacts should survive a medium- or high-risk workflow?

### Answer Key And Rationale

1. The level depends on risk and impact radius, not the superficial command category. Editing docs is low risk; editing auth or contract-sensitive behavior is not.

2. Correct answer: C. Auth and client-compatibility impact push the action into controlled mutation with approval and stronger evidence requirements.

3. A blocked action crossed a policy boundary, so retrying it without a human decision is itself a guardrail failure. It is not just an operational problem.

4. Plan artifact, action log, validation evidence, approval record where needed, escalation notes, and final disposition. Guardrails without records are not auditable.

---

## Mixed Mock Section

### Questions

1. You need to improve a repo workflow quickly. Which sequence is strongest?

A. Add a write-capable MCP server, let a single agent edit broadly, and rely on CI to catch mistakes.

B. Add a read-only MCP server first, identify the controlling file, make the smallest relevant change, and run the smallest discriminating validation before widening scope.

C. Start with a broad full-suite run, then decide what file probably matters.

D. Tune prompts and tools together until the output looks right.

2. A reviewer reports that the implementation touched files outside planner scope, but all tests pass. What is the best next step?

3. A local auth test fails because an expected secret is missing. What should you change first: prompt, policy, environment, or code?

4. Why is a stable response envelope relevant across Domains 3, 4, and 6 instead of just one domain?

5. A workflow attempts a production-adjacent action without approval. What failure class is primary, and why?

6. A repo uses `copilot-instructions.md` instead of `CLAUDE.md`, plus prompt files and tool configuration in other Copilot surfaces. What should you preserve when translating the GH-600 architecture concepts from this pack?

### Answer Key And Rationale

1. Correct answer: B. It combines minimum viable tool capability, local control-path identification, narrow validation, and disciplined scope growth.

2. Freeze the workflow and resolve the scope conflict through coordinator or human review. Passing tests do not erase an authorization mismatch.

3. Environment. Missing secret configuration is not fixed by changing prompts or code first.

4. Because it is simultaneously a continuity artifact for execution state, an evaluation invariant for contract testing, and an accountability mechanism for predictable error behavior.

5. Policy or permission failure. The workflow crossed an approval boundary, so the primary problem is governance, not ordinary command failure.

6. Preserve the architectural role, not the vendor-specific filename. You still need a shared instruction layer, reusable task-entry surfaces, and a tool-governance layer. GH-600 is testing those control surfaces, not whether one product uses `CLAUDE.md` versus `copilot-instructions.md`.

---

## Scoring Suggestion

Use this quick rubric:
- `16-20` correct: strong repo-specific GH-600 readiness
- `11-15` correct: solid foundation, but revisit the weaker domain sections
- `6-10` correct: reread the domain notes and rerun the labs before more question practice
- `0-5` correct: start again from the hub and study the worked examples before testing yourself further

For higher-value review, do not only count wrong answers. Write down why your chosen answer was wrong and which repo artifact should have led you to the stronger answer.