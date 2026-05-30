# Getting Started — How to Use Both Study Guides

## The Two Guides

| Guide | Purpose |
|---|---|
| [`claude-study-guide.md`](claude-study-guide.md) | Daily habit framework — journal + experiments |
| [`certified-architect-foundations.md`](certified-architect-foundations.md) | Exam roadmap — domain by domain prep for the certification |

Run them **in parallel**, not sequentially.

---

## You've Already Completed Weeks 1–2

The 6-phase Django migration you just finished covers the first two weeks of the general guide without you realizing it.

| General guide week | What it covers | Your status |
|---|---|---|
| Week 1 — Claude Code & Context | Watch Claude read files, use tools, manage context | ✅ Done — 6-phase migration, /review, /django-new |
| Week 2 — Prompt Engineering | Read CLAUDE.md, study skills, write a skill | ✅ Done — wrote django-new.md, live-edited CLAUDE.md |
| Week 3 — Claude API & Tool Use | Call API, build tool use loop | ← **Start here** |
| Week 4 — Models, Safety, Review | Model comparison, safety concepts | Next |

---

## How to Use Both Guides Together

```
Daily (30 min)                        Weekly (focused study)
──────────────────────────────        ──────────────────────────────────
claude-study-guide.md                 certified-architect-foundations.md

Morning: pick one experiment          Follow the 4-week exam schedule
Evening: write one journal entry      Domain by domain, in order
```

---

## Concrete Starting Sequence

### Day 1 — Write your first journal entry
Open [`journal.md`](journal.md) and document the Django migration experience.
You lived through Weeks 1–2 of the general guide — capture it now while it's fresh.
The migration gave you direct experience with tool use loops, context management, and
agentic patterns. That is 40% of the exam already.

### Day 2 — Run the prompt A/B test
```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python3 docs/study/experiments/prompt_ab_test.py
```
Write what you observed in the journal. This covers exam Domain 4 (Prompt Engineering) hands-on.

### Day 3–4 — Read the Agent SDK docs
This is your biggest gap. You've seen Claude Code *use* tools, but the exam tests whether
you can *design* multi-agent systems with `AgentDefinition`, hooks, and the `Task` tool.
These are not covered by your migration experience yet.

- [Claude Agent SDK — Overview](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Claude Agent SDK — Hooks](https://platform.claude.com/docs/en/agent-sdk/hooks)
- [Claude Agent SDK — Subagents](https://platform.claude.com/docs/en/agent-sdk/subagents)

### Day 5 — Run the caching experiment + read MCP docs
```bash
python3 docs/study/experiments/cached_categorizer.py
```
Then read the MCP docs. You already have `.mcp.json` awareness from the project — extend it.

- [Model Context Protocol — Tools](https://modelcontextprotocol.io/docs/concepts/tools)
- [MCP — Resources](https://modelcontextprotocol.io/docs/concepts/resources)

### Day 6–7 — Take the practice test
Take the community practice test to find your weak domains before planning the rest of the month:
[practical_test_en.html](https://github.com/paullarionov/claude-certified-architect/blob/main/practical_test_en.html)

The practice test results tell you which of the 5 domains needs more study time.
Adjust the 4-week schedule in `certified-architect-foundations.md` accordingly.

---

## Summary

- **Do NOT** start `claude-study-guide.md` from Week 1 — you've already done it.
- **Do** use `claude-study-guide.md` as a daily ritual: one experiment + one journal entry per session.
- **Do** follow `certified-architect-foundations.md` domain by domain for the exam.
- **Start today** with the journal entry — the migration is your Week 1–2 material.
- **Biggest gap:** Agent SDK (AgentDefinition, hooks, Task tool) — read those docs first.
