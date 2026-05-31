# GH-600 Four-Week Study Schedule

## How To Use This Schedule

This schedule assumes a steady cadence of about 30 to 60 minutes a day.

Each day has four parts:
- primary study material
- one repo action or lab step
- one output artifact to write down
- one quick review checkpoint

If you miss a day, do not restart the week. Resume at the next unfinished day and carry the missed artifact forward into the next review checkpoint.

If you are using GitHub Copilot instead of Claude Code, translate names as you read:
- `CLAUDE.md` maps conceptually to `copilot-instructions.md`
- `.claude/commands/` maps to reusable prompt or task-entry files
- `.claude/skills/` maps to specialized agent or prompt customizations
- `.claude/settings.json` maps to Copilot-side tool and agent configuration

---

## Week 1: Architecture, Tooling, And Control Planes

### Day 1
- Time budget: 45 minutes
- Read: [study-guide-financius-gh600.md](study-guide-financius-gh600.md) and [domain-1-architecture-and-sdlc.md](domain-1-architecture-and-sdlc.md)
- Do: inspect [CLAUDE.md](../../CLAUDE.md) and [.github/workflows/ci.yml](../../.github/workflows/ci.yml). If you are thinking in Copilot terms, treat `CLAUDE.md` as the role that `copilot-instructions.md` would play.
- Output: write a short note describing policy layer, execution layer, and validation layer in this repo
- Review checkpoint: can you explain why CI is part of the architecture rather than only automation?

### Day 2
- Time budget: 45 minutes
- Read: [domain-2-tools-and-environment.md](domain-2-tools-and-environment.md)
- Do: inspect [.claude/settings.json](../../.claude/settings.json) and [mcp-and-tools-profile.md](mcp-and-tools-profile.md). If you are using Copilot, read `.claude/settings.json` as the role that tool and agent configuration would play there.
- Output: produce a Class A, B, C, D tool inventory for at least six repo actions
- Review checkpoint: can you justify why a read-only MCP server is the safest first MCP addition?

### Day 3
- Time budget: 45 minutes
- Read: [labs/lab-tools-and-environment.md](labs/lab-tools-and-environment.md)
- Do: run the lab's suggested local validation commands if your environment is ready
- Output: write one paragraph on policy drift inside `.claude/settings.json`
- Review checkpoint: can you distinguish retry policy from rollback policy?

### Day 4
- Time budget: 30 minutes
- Read: [autonomy-and-guardrails-matrix.md](autonomy-and-guardrails-matrix.md)
- Do: classify five repo actions into L0 through L3
- Output: create a one-page autonomy matrix in your notes
- Review checkpoint: can you explain why the same edit workflow can be L1 in one case and L2 in another?

### Day 5
- Time budget: 30 minutes
- Read: [practice-questions.md](practice-questions.md) Domain 1 and Domain 2 sections
- Do: answer those questions without looking at the notes first, using the Claude-to-Copilot translation if that is the toolset you study with
- Output: record wrong answers and the repo artifact you should have used
- Review checkpoint: are your mistakes mostly recall errors or judgment errors?

### Day 6
- Time budget: 45 minutes
- Read: [domain-6-guardrails-and-accountability.md](domain-6-guardrails-and-accountability.md)
- Do: compare [.claude/settings.json](../../.claude/settings.json) with [backend/financius_web/settings.py](../../backend/financius_web/settings.py)
- Output: write one approval-checkpoint example for an L2 auth or contract change
- Review checkpoint: can you describe what makes a blocked action different from an ordinary failed command?

### Day 7
- Time budget: 30 minutes
- Read: review your Week 1 notes
- Do: revisit any wrong Domain 1, 2, or 6 question-bank answers
- Output: create a one-paragraph Week 1 summary of architecture, tools, and guardrails
- Review checkpoint: if asked for the repo's control plane, can you answer in under one minute?

---

## Week 2: Memory, State, And Safe Execution

### Day 8
- Time budget: 45 minutes
- Read: [domain-3-memory-state-execution.md](domain-3-memory-state-execution.md)
- Do: inspect [backend/ledger/management/commands/migrate_from_sqlite.py](../../backend/ledger/management/commands/migrate_from_sqlite.py)
- Output: list three examples of working context versus durable state from the command
- Review checkpoint: can you explain why idempotency is a state-management concern?

### Day 9
- Time budget: 45 minutes
- Read: [state-and-memory-playbook.md](state-and-memory-playbook.md)
- Do: inspect [backend/tests/dj/unit/test_migrate_from_sqlite.py](../../backend/tests/dj/unit/test_migrate_from_sqlite.py)
- Output: draft one run ledger for a migration dry run
- Review checkpoint: what exact drift signals would make you stop and refresh context?

### Day 10
- Time budget: 45 minutes
- Read: [labs/lab-memory-and-state.md](labs/lab-memory-and-state.md)
- Do: run `pytest tests/dj/unit/test_migrate_from_sqlite.py -q` from `backend/` if your environment is ready
- Output: write one paragraph on how dry-run safety differs from rollback readiness
- Review checkpoint: which test best proves rerun safety?

### Day 11
- Time budget: 30 minutes
- Read: review [backend/financius_web/exception_handler.py](../../backend/financius_web/exception_handler.py)
- Do: connect the envelope shape to continuity, not just error handling
- Output: note one reason output stability belongs in Domain 3
- Review checkpoint: can you explain why interface continuity is part of execution continuity?

### Day 12
- Time budget: 30 minutes
- Read: [practice-questions.md](practice-questions.md) Domain 3 section
- Do: answer the questions without checking the notes
- Output: correct your answers using the playbook and migration tests as evidence
- Review checkpoint: can you explain the email-to-UUID mapping without looking at the file?

### Day 13
- Time budget: 30 minutes
- Read: your Week 2 notes only
- Do: rewrite your run ledger in a clearer form
- Output: one final run-ledger example for rehearsal or real execution
- Review checkpoint: if the migration were interrupted midstream, what would you verify before resuming?

### Day 14
- Time budget: 20 minutes
- Read: none; focus on recall
- Do: verbally summarize Week 2 from memory
- Output: one short list of concepts still unclear
- Review checkpoint: can you distinguish working memory, durable state, and stable interface state?

---

## Week 3: Evaluation, Error Analysis, And Tuning

### Day 15
- Time budget: 45 minutes
- Read: [domain-4-evaluation-and-tuning.md](domain-4-evaluation-and-tuning.md)
- Do: inspect [backend/tests/dj/contract/test_envelope_contract.py](../../backend/tests/dj/contract/test_envelope_contract.py)
- Output: write down the strongest evaluation signal in this repo and why
- Review checkpoint: can you explain why contract tests are closer to user impact than generic API checks?

### Day 16
- Time budget: 45 minutes
- Read: [evaluation-and-tuning-report.md](evaluation-and-tuning-report.md)
- Do: classify three real or simulated failures into reasoning, tool, environment, or policy categories
- Output: one filled-in taxonomy worksheet for three failures
- Review checkpoint: which of your failures would be easy to misclassify under time pressure?

### Day 17
- Time budget: 45 minutes
- Read: [labs/lab-evaluation-and-tuning.md](labs/lab-evaluation-and-tuning.md)
- Do: run one narrow validation such as `pytest tests/dj/contract/test_envelope_contract.py -q` if your environment is ready
- Output: one before/after tuning loop written as signal, change, and result
- Review checkpoint: can you justify why that validation was the smallest useful check?

### Day 18
- Time budget: 30 minutes
- Read: [backend/tests/dj/unit/test_auth_views.py](../../backend/tests/dj/unit/test_auth_views.py)
- Do: identify one likely environment failure and one likely reasoning failure
- Output: a short note comparing those two failure classes
- Review checkpoint: can you explain why missing secrets are not a prompt problem first?

### Day 19
- Time budget: 30 minutes
- Read: [practice-questions.md](practice-questions.md) Domain 4 section
- Do: answer the section without notes
- Output: record which rationale changed your mind most
- Review checkpoint: are you classifying failures before choosing the next action?

### Day 20
- Time budget: 30 minutes
- Read: your Week 3 notes
- Do: pick one repo workflow and define its strongest signal, smallest check, and escalation trigger
- Output: a one-page evaluation plan
- Review checkpoint: can you state what evidence would make you stop tuning and escalate?

### Day 21
- Time budget: 20 minutes
- Read: none; focus on recall
- Do: explain the repo's evaluation loop from memory
- Output: list any terms you still use imprecisely
- Review checkpoint: can you distinguish signal selection from tuning itself?

---

## Week 4: Multi-Agent Coordination, Guardrails, And Final Review

### Day 22
- Time budget: 45 minutes
- Read: [domain-5-multi-agent-coordination.md](domain-5-multi-agent-coordination.md)
- Do: inspect [multi-agent-orchestration.md](multi-agent-orchestration.md)
- Output: define planner, implementer, reviewer, and coordinator responsibilities in your own words
- Review checkpoint: can you explain why the coordinator is not just another planner?

### Day 23
- Time budget: 45 minutes
- Read: [labs/lab-multi-agent-workflow.md](labs/lab-multi-agent-workflow.md)
- Do: simulate a planner artifact for one medium-scope repo task
- Output: one planner handoff artifact
- Review checkpoint: does the handoff authorize a concrete next step or only describe a goal?

### Day 24
- Time budget: 45 minutes
- Read: [multi-agent-orchestration.md](multi-agent-orchestration.md) again, focusing on conflicts
- Do: write an implementer artifact and a reviewer artifact for the same simulated task
- Output: one conflict scenario and one coordinator decision summary
- Review checkpoint: can you state which risks outrank delivery speed?

### Day 25
- Time budget: 30 minutes
- Read: [domain-6-guardrails-and-accountability.md](domain-6-guardrails-and-accountability.md)
- Do: review one L2 and one L3 scenario from [autonomy-and-guardrails-matrix.md](autonomy-and-guardrails-matrix.md)
- Output: one approval checkpoint payload in your own words
- Review checkpoint: what evidence must survive an L2 action?

### Day 26
- Time budget: 30 minutes
- Read: [practice-questions.md](practice-questions.md) Domains 5 and 6 sections
- Do: answer without notes
- Output: a short list of coordination and guardrail mistakes you still make
- Review checkpoint: are your misses about role boundaries, approval levels, or artifact quality?

### Day 27
- Time budget: 45 minutes
- Read: [practice-questions.md](practice-questions.md) mixed mock section
- Do: take the mixed mock in one sitting
- Output: score yourself and list your three weakest concepts
- Review checkpoint: do your misses cluster around one domain or across several?

### Day 28
- Time budget: 45 minutes
- Read: your weakest domain note plus its companion reference
- Do: review your artifacts from the prior weeks
- Output: one final exam-readiness summary with strengths, weak domains, and next revision targets
- Review checkpoint: can you explain each GH-600 domain with one repo example and one risk-control principle?

---

## Final Readiness Check

You are close to exam-ready when you can do all of the following from memory:
- explain the repo's policy, execution, and validation layers
- justify a read-only-first MCP/tool strategy
- describe rerun safety and context-drift detection using the migration workflow
- classify failures before tuning anything
- describe planner, implementer, reviewer, and coordinator boundaries
- map repo actions to autonomy levels and approval requirements

If one of those is weak, revisit that domain note, rerun its lab, and answer the matching practice questions again before moving on.