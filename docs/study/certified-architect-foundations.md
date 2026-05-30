# Claude Certified Architect — Foundations Study Guide

**Certification:** Claude Certified Architect — Foundations (Anthropic)
**Source:** Based on paullarionov/claude-certified-architect (community exam guide)
**Format:** Multiple choice, 100–1000 scale, passing score **720**. No guessing penalty — answer every question.
**Scenarios:** 4 randomly selected from 8 possible. You do not know which 4 you will get.

---

## Actual Exam Domains (correct weights)

| Domain | Weight | Focus |
|---|---|---|
| 1. Agent Architecture & Orchestration | **27%** | Agentic loops, coordinator–subagent, hooks, task decomposition |
| 2. Tool Design & MCP Integration | **18%** | Tool descriptions, tool_choice, MCP servers, error responses |
| 3. Claude Code Configuration & Workflows | **20%** | CLAUDE.md hierarchy, skills, planning mode, CI/CD |
| 4. Prompt Engineering & Structured Output | **20%** | Few-shot, explicit criteria, tool_use for JSON, validation |
| 5. Context Management & Reliability | **15%** | Lost-in-middle, escalation, error propagation, provenance |

> **Important:** The exam is NOT primarily about the basic Messages API (model selection, streaming, temperature). It tests architectural decisions in production multi-agent systems using the Claude Agent SDK, MCP, and Claude Code.

---

## The 8 Exam Scenarios (memorize all 8 — you get 4 randomly)

| # | Scenario | Key domain tested |
|---|---|---|
| 1 | Customer Support Agent | Agentic loop, tool ordering, escalation, hooks |
| 2 | Code Generation with Claude Code | CLAUDE.md, planning mode, skills, iterative refinement |
| 3 | Multi-Agent Research System | Coordinator–subagent, error propagation, provenance |
| 4 | Developer Productivity Tools | Built-in tools (Read/Grep/Glob/Edit/Bash), codebase exploration |
| 5 | Claude Code for CI/CD | `-p` flag, `--output-format json`, session isolation, batch API |
| 6 | Structured Data Extraction | tool_use + JSON schema, validation loops, semantic vs syntax errors |
| 7 | Conversational AI Architecture | Context window management, memory strategies, tool design |
| 8 | Agentic AI Tools *(partial)* | Similar to Scenarios 1 & 3 |

---

## Domain 1 — Agent Architecture & Orchestration (27%)

### The Agentic Loop — know every detail

```
1. Send Claude request with tools
2. Check stop_reason:
   "tool_use"  → execute the tool, append result to history, go to step 1
   "end_turn"  → task complete, return result to user
3. Repeat until end_turn
```

**The ONLY reliable completion signal is `stop_reason == "end_turn"`.**

Anti-patterns the exam tests you on:
- Parsing assistant text for "Task completed" → wrong
- Using `max_iterations=5` as primary stop → wrong
- Checking if content array has text → wrong

### Hub-and-Spoke: Coordinator + Subagents

```
         Coordinator
        /     |      \
  Subagent1  Subagent2  Subagent3
  (search)  (analysis)  (synthesis)
```

**Subagents have isolated context — they do NOT inherit the coordinator's history.**
All context must be explicitly passed in the subagent's prompt.

**Coordinator responsibilities:**
- Task decomposition and delegation
- Dynamic subagent selection
- Result aggregation and validation
- Error handling and retries
- All inter-agent communication flows through coordinator

**Spawning subagents via the `Task` tool:**
```python
# Coordinator's allowed_tools must include "Task"
coordinator = AgentDefinition(
    allowed_tools=["Task", "get_customer"],
)

# BAD: subagent has no context
Task: "Analyze the document"

# GOOD: explicit context in prompt
Task: "Analyze the document below.
Document: [full text]
Prior search results: [results]
Required output format: [schema]"
```

**Parallel subagents:** coordinator returns multiple `Task` calls in one response — they run concurrently.

### Hooks — deterministic vs probabilistic

| | Hooks | Prompt instructions |
|---|---|---|
| Guarantee | **Deterministic (100%)** | Probabilistic (~90%, not 100%) |
| Use for | Financial limits, compliance, critical business rules | Preferences, recommendations, formatting |

```python
# PostToolUse: normalize data before the model sees it
@hook("PostToolUse", tool="lookup_order")
def trim_order_fields(result):
    return {k: result[k] for k in ["order_id", "status", "total", "items"]}

# PreToolUse: block policy-violating actions
@hook("PreToolUse")
def enforce_refund_limit(tool_call):
    if tool_call.name == "process_refund" and tool_call.args.amount > 500:
        return redirect_to_escalation(tool_call)
```

**Rule:** When failure has financial, legal, or safety consequences → use hooks, not prompts.

### AgentDefinition

```python
agent = AgentDefinition(
    name="customer_support",
    description="Handles customer requests for returns and order issues",
    system_prompt="You are a customer support agent...",
    allowed_tools=["get_customer", "lookup_order", "process_refund", "escalate_to_human"],
)
```

Principle of least privilege: give each agent only the tools it needs for its role. Too many tools (18 vs 4–5) reduces tool selection reliability.

### Session management

- `--resume <session-name>` — continue a named session
- `fork_session` — branch from shared context to explore two approaches in parallel
- Start a NEW session (with a written summary) when files have changed or results are stale

### Task decomposition: fixed vs dynamic

| | Fixed (prompt chaining) | Dynamic (adaptive) |
|---|---|---|
| Use when | Predictable, repeatable tasks | Open-ended investigations |
| Example | Code review: file-by-file then integration pass | "Add tests to legacy codebase" |

Multi-pass code review for 10+ files:
- Pass 1: analyze each file individually (avoids attention dilution)
- Pass 2: cross-file integration pass for dataflow and type consistency

### Escalation patterns

| Trigger | Action |
|---|---|
| Customer says "get me a manager" | Escalate immediately — do not attempt to solve |
| Policy is silent on the request | Escalate — don't guess |
| Agent cannot make progress | Escalate after reasonable attempts |
| Financial operation above threshold | Hook-enforced escalation |
| Multiple customer matches | Ask for more identifiers |

**Unreliable escalation triggers:** sentiment analysis, model self-rated confidence (1–10), automatic classifiers.

**Structured handoff on escalation:**
```json
{
  "customer_id": "CUST-12345",
  "issue_summary": "Refund request for damaged item",
  "actions_taken": ["verified identity", "looked up order", "offered replacement — declined"],
  "recommended_action": "Approve full refund",
  "escalation_reason": "Customer requested manager"
}
```

---

## Domain 2 — Tool Design & MCP Integration (18%)

### Tool descriptions — primary selection mechanism

The model chooses which tool to call based entirely on its description.

**Bad:** `"Retrieves customer information"`
**Good:** `"Finds a customer by email or ID. Returns profile, order history, account status. Use BEFORE lookup_order to verify identity. Accepts email (user@domain.com) or numeric customer_id."`

Include in descriptions:
- What the tool does and returns
- Input formats and examples
- When to use this tool vs similar alternatives
- Edge cases and constraints

Overlapping descriptions cause misrouting. Fix by renaming tools to eliminate semantic overlap (e.g., `analyze_content` → `extract_web_results`).

### `tool_choice` parameter

| Value | Behavior | Use when |
|---|---|---|
| `{"type": "auto"}` | Model decides | Default for most cases |
| `{"type": "any"}` | Model MUST call some tool | Need guaranteed structured output |
| `{"type": "tool", "name": "extract_metadata"}` | Model MUST call specific tool | Need guaranteed first step |

### JSON schemas for structured output

`tool_use` + JSON schema is the **most reliable** way to get structured output. It eliminates syntax errors but NOT semantic errors.

```json
{
  "type": "object",
  "properties": {
    "category": {
      "type": "string",
      "enum": ["bug", "feature", "docs", "unclear", "other"]
    },
    "category_detail": {"type": ["string", "null"]},
    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
  },
  "required": ["category", "severity"]
}
```

Schema design rules:
- Make fields optional/nullable (`"type": ["string", "null"]`) when information may be absent — prevents hallucination
- Add `"other"` + a detail field to enums — prevents data loss for edge cases
- Add `"unclear"` to enums — honest uncertainty beats wrong category

### MCP servers

**Project config (`.mcp.json`)** — shared via VCS, available to all team members:
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}
    }
  }
}
```

**User config (`~/.claude.json`)** — personal/experimental, NOT shared.

**MCP resources** (vs tools): data the agent reads for context without taking actions — schemas, catalogs, documentation. Reduces exploratory tool calls.

### Structured error responses

```json
{
  "isError": true,
  "content": {
    "errorCategory": "transient",
    "isRetryable": true,
    "message": "Timeout calling orders API.",
    "attempted_query": "order_id=12345",
    "partial_results": null
  }
}
```

A generic `"Operation failed"` gives the coordinator nothing to act on.

Error categories:
- **Transient** (timeout, 503) → retry with exponential backoff
- **Validation** (bad input format) → fix the request, don't retry
- **Business** (policy violation) → explain to user, propose alternative
- **Permission** (access denied) → escalate

---

## Domain 3 — Claude Code Configuration & Workflows (20%)

### CLAUDE.md hierarchy

```
1. User-level:     ~/.claude/CLAUDE.md        — personal, NOT in VCS
2. Project-level:  .claude/CLAUDE.md or CLAUDE.md — team-shared, IN VCS
3. Directory-level: CLAUDE.md in subdirectories — scoped to that directory
```

**Exam trap:** If a new team member doesn't get project instructions, check whether they were placed in `~/.claude/CLAUDE.md` (user-level) instead of `.claude/CLAUDE.md` (project-level).

**`@path` imports** for modular config:
```markdown
Coding standards: @./standards/coding-style.md
Test requirements: @./standards/testing.md
```

**`.claude/rules/` with glob patterns** for conditional loading:
```yaml
---
paths: ["**/*.test.tsx", "**/*.test.ts"]
---
Tests must use describe/it blocks. No hardcoded data — use factories.
```
This rule loads ONLY when editing test files. Saves context and tokens.

When to use `.claude/rules/` with paths vs directory-level CLAUDE.md:
- `.claude/rules/` + paths → conventions that apply by file type across many directories (tests, migrations)
- Directory-level CLAUDE.md → conventions tied to one specific directory

### Custom slash commands and skills

**Project commands** (`.claude/commands/` or `.claude/skills/`) → stored in VCS, available to everyone:
```
.claude/commands/review.md     → /review command
.claude/skills/review/SKILL.md → /review skill (with frontmatter)
```

**User commands** (`~/.claude/commands/` or `~/.claude/skills/`) → personal, not shared.

**Skill frontmatter:**
```yaml
---
context: fork       # isolates skill output from main session context
allowed-tools: ["Read", "Grep", "Glob"]   # restricts available tools
argument-hint: "Path to analyze"           # prompts for missing argument
---
```

`context: fork` runs the skill in a subagent so verbose output doesn't pollute main session.

**Skill vs CLAUDE.md:**
- Skill → on-demand invocation for specific tasks
- CLAUDE.md → always-loaded conventions and standards

### Planning mode vs direct execution

**Planning mode** — model only reads, no writes:
- Explores codebase with Read, Grep, Glob
- Produces a plan the user approves
- Use for: large changes (dozens of files), architectural decisions, multiple viable approaches, unfamiliar codebases

**Direct execution:**
- Use for: single-file fixes with clear stack trace, well-understood simple changes

**Explore subagent:** isolates verbose discovery output from main context — prevents context exhaustion.

**Combined approach:** planning mode to investigate → user approves → direct execution to implement.

### Claude Code for CI/CD

```bash
# CORRECT: non-interactive mode for CI
claude -p "Analyze this PR for security issues"

# Structured output for automated parsing
claude -p "Review this PR" \
  --output-format json \
  --json-schema '{"type":"object","properties":{"findings":{...}}}'
```

`-p` (or `--print`) is the ONLY correct way to run Claude Code in CI pipelines.

**Session context isolation:** The same Claude session that generated code is less effective at reviewing it — it retains its reasoning context and is biased toward its own decisions. Use an independent instance for review.

**Preventing duplicate comments:** include prior review results in context and instruct Claude to report only new or unresolved issues.

Built-in tools reference:

| Task | Tool |
|---|---|
| Find files by pattern | Glob: `**/*.test.tsx` |
| Search within files | Grep: function name, import |
| Read full file | Read |
| Create new file | Write |
| Precise edit to existing file | Edit (unique text match required) |
| Run shell command | Bash |

If Edit fails (non-unique match) → fall back to Read + Write.

---

## Domain 4 — Prompt Engineering & Structured Output (20%)

### Explicit criteria beat vague instructions

**Vague:**
```
Check comments for accuracy. Be conservative.
```

**Explicit:**
```
Flag a comment ONLY if:
1. It describes behavior that CONTRADICTS the actual code
2. It references a non-existent function or variable
3. A TODO refers to a bug already fixed in code

Do NOT flag:
- Stylistically outdated comments
- Missing comments (separate category)
```

### Few-shot examples — most reliable for consistent output

Provide 2–4 targeted examples covering:
- Ambiguous cases with rationale (what to escalate vs handle)
- Output format (location, issue, severity, fix)
- Acceptable vs problematic patterns (reduces false positives)
- Different document structures (for extraction tasks)

```
Example 1:
Request: "My order is broken"
Action: get_customer → lookup_order → check status
Rationale: "broken" may mean damaged item — need order details first

Example 2:
Request: "Get me a manager"
Action: escalate_to_human immediately
Rationale: explicit request for human — do not attempt to solve autonomously
```

### Prompt chaining for multi-step tasks

```
Step 1: Analyze auth.ts (local issues only)   → list of issues
Step 2: Analyze database.ts (local issues)    → list of issues
Step 3: Integration pass (cross-file deps)    → cross-boundary issues
```

Why not send all files at once: **attention dilution** — the model may miss bugs in some files while giving shallow analysis to others.

### Validation and retry with feedback

```
Step 1: Extract data
Step 2: Validate with Pydantic/JSON Schema
Step 3: If error → retry with: original doc + wrong extraction + specific error
         "Field 'total' = 150 but sum(items) = 145. Re-check."
```

Retry will be effective for: format errors, structural errors, arithmetic inconsistencies.
Retry will NOT help when: information is simply absent from the source document.

### Self-correction pattern

Include both the stated and computed value so Claude can detect its own errors:
```json
{
  "stated_total": 150.00,
  "calculated_total": 145.00,
  "conflict_detected": true
}
```

### Message Batches API

| | Synchronous | Batch API |
|---|---|---|
| Savings | — | **50% cheaper** |
| Latency | Immediate | Up to **24 hours** |
| Multi-turn tool use | Supported | **NOT supported** |
| Use for | Blocking checks (pre-merge) | Non-urgent (overnight, weekly) |

`custom_id` links request to response in batches. On partial failure, re-submit only failed items by `custom_id`.

SLA planning: if deadline is 30 hours and batch takes up to 24h → submit batches at most 24h before deadline.

---

## Domain 5 — Context Management & Reliability (15%)

### Lost-in-the-middle effect

Models reliably process information at the **start** and **end** of long inputs. Middle sections (especially numeric values, dates, percentages) are often missed.

Mitigation:
- Place key findings at the beginning with explicit section headings
- Place action items at the end
- Extract critical facts into a separate persistent block:

```
=== CASE FACTS (updated on each new fact) ===
Customer ID: CUST-12345
Order ID: ORD-67890
Amount: $89.99
Issue: Damaged item
Status: Pending manager approval
===
```

Include this block in every prompt regardless of history summarization.

### Trim tool results

If `lookup_order` returns 40+ fields but you need 5 — use a `PostToolUse` hook to strip the rest before it reaches the model. Saves context, reduces noise.

### Context management strategies

- **Scratchpad files:** agent writes key findings to a file during long investigations; reads it in new sessions instead of re-discovering
- **Delegate to subagent:** subagent reads 15 files and returns a 1-line summary; main agent keeps minimal context
- **Structured state persistence:** each agent exports state to a known file path; coordinator loads manifest on resume

```json
// agent-state/manifest.json
{
  "web-search": "completed",
  "doc-analysis": "in_progress",
  "synthesis": "not_started"
}
```

### Progressive summarization risks

When compressing history, exact numeric values, dates, and specific percentages get lost and become vague ("about", "roughly"). Mitigate by extracting facts into a persistent block outside history.

### Provenance preservation

**Bad:** "The AI music market is $3.2B." (no source)
**Good:**
```json
{
  "claim": "The AI music market is $3.2B",
  "source_url": "https://...",
  "publication_date": "2024-06-15",
  "confidence": 0.9
}
```

When two sources conflict — preserve BOTH with attribution. Include dates to distinguish temporal change from contradiction.

---

## Exam Question Patterns — learn the logic, not just the answers

**Pattern 1: Hooks vs prompts**
Q: Agent skips required step 12% of the time despite prompt instructions. Fix?
A: Programmatic precondition blocking downstream tools until required step completes. NOT adding more prompt instructions.
Why: Hooks are deterministic. Prompts are probabilistic.

**Pattern 2: Tool descriptions**
Q: Agent calls wrong tool 45% of the time. Tool descriptions are minimal and similar.
A: Expand descriptions with input formats, examples, when to use vs alternatives.
Why: Descriptions are the primary selection mechanism — this is the lowest-effort highest-impact fix.

**Pattern 3: Batch API**
Q: Which workflow should use Batch API?
A: Non-blocking, non-urgent work (overnight reports, weekly audits). Never for blocking checks (pre-merge hooks).

**Pattern 4: Planning mode**
Q: Restructure monolith into microservices (dozens of files, architectural decisions).
A: Planning mode — explore first, then implement.
Why: Large changes, multiple viable approaches, architectural decisions = planning mode.

**Pattern 5: CLAUDE.md hierarchy**
Q: New team member doesn't get project instructions after cloning repo.
A: Instructions were in `~/.claude/CLAUDE.md` (user-level) not `.claude/CLAUDE.md` (project-level).

**Pattern 6: Coordinator decomposition**
Q: Multi-agent research only covers visual art, ignoring music/literature/film. All subagents completed successfully.
A: Coordinator decomposed too narrowly. Fix decomposition, not subagents.

**Pattern 7: Error propagation**
Q: Subagent times out. How to return error to coordinator?
A: Structured error with failure type, executed query, partial results, alternative approaches. Never generic "search unavailable".

**Pattern 8: Attention dilution**
Q: Review of 14-file PR produces inconsistent depth and missed bugs.
A: Split into per-file passes + separate integration pass.
Why: Single-pass over many files causes attention dilution.

**Pattern 9: CI/CD non-interactive mode**
Q: Pipeline hangs waiting for user input.
A: Use `claude -p "..."` (--print flag).

**Pattern 10: Few-shot vs explicit criteria**
Q: Instructions like "be more conservative" don't produce consistent behavior.
A: 3–4 few-shot examples showing exact format beats vague instructions.

---

## 4-Week Exam Prep Schedule

### Week 1 — Agent Architecture
- Read: [Claude Agent SDK overview](https://platform.claude.com/docs/en/agent-sdk/overview)
- Read: [Agent SDK — Hooks](https://platform.claude.com/docs/en/agent-sdk/hooks)
- Read: [Agent SDK — Subagents](https://platform.claude.com/docs/en/agent-sdk/subagents)
- Do: Draw the coordinator–subagent topology for Financius — coordinator routes sync requests to category-agent, receipt-agent, shop-agent
- Memorize: Hub-and-spoke pattern, why subagents don't inherit context, hooks vs prompts

### Week 2 — Claude Code + MCP
- Read: [Claude Code — CLAUDE.md and Memory](https://code.claude.com/docs/en/memory)
- Read: [Claude Code — Skills](https://code.claude.com/docs/en/skills)
- Read: [Claude Code — GitHub Actions CI/CD](https://code.claude.com/docs/en/github-actions)
- Read: [MCP — Tools](https://modelcontextprotocol.io/docs/concepts/tools)
- Do: Audit your own `CLAUDE.md` — is it project-level or user-level? Add `.claude/rules/` for Django-specific rules
- Memorize: CLAUDE.md 3-level hierarchy, `context: fork` skill option, `-p` flag for CI

### Week 3 — Prompt Engineering + Structured Output
- Read: [Prompt engineering guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview)
- Read: [Tool use](https://platform.claude.com/docs/en/build-with-claude/tool-use)
- Read: [Message Batches](https://platform.claude.com/docs/en/build-with-claude/message-batches)
- Do: Run `prompt_ab_test.py` — measure how few-shot examples improve receipt accuracy
- Do: Build a tool with JSON schema, use `tool_choice: "any"` to force structured output
- Memorize: When to use Batch API, tool_choice values, schema design rules

### Week 4 — Context Management + Full Practice Test
- Read: [Extended Thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)
- Do: Work through ALL 12+ example questions in paullarionov/claude-certified-architect/guide_en.MD
- Do: Take the practice test: [practical_test_en.html](https://github.com/paullarionov/claude-certified-architect/blob/main/practical_test_en.html)
- Review: All 10 exam question patterns above
- Memorize: Lost-in-the-middle mitigation, escalation triggers, error propagation structure

---

## Quick-Reference — Exam Day Cheat Sheet

**Agent loop completion:** `stop_reason == "end_turn"` only
**Subagent context:** must be explicitly passed — no automatic inheritance
**Hooks vs prompts:** hooks = deterministic; prompts = probabilistic
**Tool descriptions:** primary selection mechanism — be specific and distinct
**CLAUDE.md hierarchy:** user (~/.claude/) vs project (.claude/) vs directory
**Skills `context: fork`:** isolates skill output from main session
**CI non-interactive:** `claude -p "..."` (--print flag)
**Batch API:** 50% cheaper, up to 24h, no multi-turn tool use, non-blocking only
**tool_choice "any":** forces a tool call (guaranteed structured output)
**Lost-in-middle:** put key info at start and end; facts block persists through summarization
**Escalation:** explicit human request = immediate; sentiment/confidence = unreliable trigger
**Error propagation:** structured (type + query + partial + alternatives) beats generic status

---

## Readiness Checklist

**Domain 1 — Agent Architecture**
- [ ] Can draw the coordinator–subagent hub-and-spoke pattern
- [ ] Know why subagents don't inherit coordinator context
- [ ] Know when to use hooks vs prompt instructions
- [ ] Know all reliable and unreliable escalation triggers
- [ ] Understand fixed (prompt chaining) vs dynamic decomposition

**Domain 2 — Tool Design & MCP**
- [ ] Know what makes a good tool description
- [ ] Know all three `tool_choice` values and when to use each
- [ ] Know project vs user MCP server config (`.mcp.json` vs `~/.claude.json`)
- [ ] Know the four error categories and which are retryable
- [ ] Know what MCP resources are (vs tools)

**Domain 3 — Claude Code**
- [ ] Know the 3-level CLAUDE.md hierarchy
- [ ] Know `@path` syntax for modular imports
- [ ] Know `.claude/rules/` with path glob frontmatter
- [ ] Know when to use planning mode vs direct execution
- [ ] Know the `-p` flag and `--output-format json` for CI

**Domain 4 — Prompt Engineering**
- [ ] Know why few-shot beats vague instructions
- [ ] Know how to write explicit criteria (with DO and DO NOT sections)
- [ ] Know JSON schema design rules (nullable fields, "other" + "unclear" enums)
- [ ] Know when Batch API works and when it doesn't
- [ ] Know retry-with-feedback loop design

**Domain 5 — Context Management**
- [ ] Know the lost-in-the-middle effect and how to mitigate it
- [ ] Know the persistent "case facts" block pattern
- [ ] Know structured error propagation (type + query + partial + alternatives)
- [ ] Know claim → source provenance mapping
- [ ] Know scratchpad files and state persistence for crash recovery
