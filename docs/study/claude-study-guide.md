# Claude Study Guide — Learning Through Financius

## Purpose

You are building Financius Web while simultaneously studying Claude AI.
This guide connects your daily development work to concrete Claude concepts,
so every coding session doubles as exam prep.

---

## What You Are Studying

The Anthropic Claude certification covers three overlapping areas:

| Area | What it tests |
|---|---|
| **Model knowledge** | What Claude can and cannot do, how it reasons, context window, model families |
| **Prompt engineering** | Writing clear instructions, few-shot examples, chain-of-thought, role prompting |
| **API & tool use** | Claude API calls, tool use, structured output, caching, streaming, agents |

Your Financius project is a live lab for all three.

---

## Your Lab — What You Have Running

| Component | Purpose as a study tool |
|---|---|
| Django backend at `http://localhost:8001` | Real API to call from Claude scripts |
| Postgres database (`localhost:5433`) | Real data (4 045 receipts, 50 categories) to query |
| Android Financius app | Real mobile client syncing to your Django API |
| Claude Code (this tool) | Claude's coding agent — study it by using it |
| 6-phase migration history | A full case study of AI-assisted software engineering |

---

## Daily Routine (30–60 min)

Structure every session the same way so learning compounds.

```
Day start
  ├── 5 min   Read one Claude concept (see weekly plan below)
  ├── 20 min  Work on Financius — use Claude Code actively
  │             Ask WHY Claude made each decision, not just accept the output
  ├── 10 min  Run one experiment from the experiment list
  └── 5 min   Write one note in docs/study/journal.md
                "What did Claude do well / struggle with today?"
```

---

## Weekly Study Plan

### Week 1 — Claude Code & Context

**Concept: How Claude Code works as an agent**

Claude Code is itself a Claude model with tools (Read, Edit, Bash, Agent, etc.).
Everything you do in this repo is Claude using tool use in real time.

| Day | Task | What to observe |
|---|---|---|
| Mon | Ask Claude to explain `ledger/views.py` | Watch it decide which files to read |
| Tue | Ask Claude to add a new field to `Receipt` model | Observe makemigrations flow |
| Wed | Run `/review` on your latest diff | Study how it structures its findings |
| Thu | Ask Claude to write a test you haven't written | Study the test strategy it chooses |
| Fri | Run `/qa` on `http://localhost:8001` | Watch it interact with your live app |

**Key questions to answer this week:**
- What is Claude's context window, and when does it get compressed in a long session?
- What are the 5 core tools Claude Code uses? (Read, Edit, Write, Bash, Agent)
- Why does Claude read a file before editing it?

---

### Week 2 — Prompt Engineering

**Concept: Instructions, roles, and few-shot examples**

Your `CLAUDE.md` and skills are live prompt engineering examples.

| Day | Task | What to observe |
|---|---|---|
| Mon | Read `CLAUDE.md` and `docs/claude-folder-guide.md` end to end | Notice what constraints shape behavior |
| Tue | Open `.claude/commands/django-new.md` — your `/django-new` skill | Identify: role, constraints, templates, checklist |
| Wed | Write a new skill: `.claude/commands/receipt-summary.md` | Practice writing system-level instructions |
| Thu | Compare two prompts: vague vs specific, observe output quality | |
| Fri | Add chain-of-thought to a prompt: "Think step by step before writing code" | |

**Exercises:**

1. **Role prompting** — Ask Claude: *"You are a senior Django security auditor. Review `accounts/views.py` for vulnerabilities."*
   Compare to asking without the role. Note the difference.

2. **Few-shot** — Show Claude 2 receipt examples, then ask it to normalize a 3rd. Observe pattern matching.

3. **Constraint injection** — Add a rule to `CLAUDE.md`: *"Never add comments to Python files."* Verify Claude follows it immediately.

---

### Week 3 — Claude API & Tool Use

**Concept: Calling Claude programmatically, tool use, structured output**

Use your live Financius API as the data source for Claude API experiments.

**Setup:**
```bash
pip install anthropic
export ANTHROPIC_API_KEY=your-key-here
```

**Exercise 1 — Basic API call:**
```python
import anthropic
client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "What is 2+2?"}]
)
print(message.content[0].text)
```

**Exercise 2 — Tool use with your Financius API:**

Write a Claude agent that can answer questions about your spending by calling your own API.

```python
import anthropic, requests

client = anthropic.Anthropic()
ACCESS_TOKEN = "your-token-from-login"

tools = [
    {
        "name": "get_receipts",
        "description": "Fetch receipts from the Financius API",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max receipts to return"},
            },
        },
    }
]

def call_tool(tool_name, tool_input):
    if tool_name == "get_receipts":
        r = requests.get(
            "http://localhost:8001/api/v1/receipts/",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            params={"limit": tool_input.get("limit", 10)},
        )
        return r.json()

messages = [{"role": "user", "content": "How much did I spend last month in total?"}]

while True:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )
    if response.stop_reason == "end_turn":
        print(response.content[0].text)
        break
    # Process tool calls
    tool_use = next(b for b in response.content if b.type == "tool_use")
    result = call_tool(tool_use.name, tool_use.input)
    messages.append({"role": "assistant", "content": response.content})
    messages.append({
        "role": "user",
        "content": [{"type": "tool_result", "tool_use_id": tool_use.id, "content": str(result)}],
    })
```

Save this as `docs/study/experiments/financius_agent.py`.

**Exercise 3 — Structured output:**
```python
import anthropic, json

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    system="You are a receipt parser. Return JSON only: {category, amount, date}",
    messages=[{"role": "user", "content": "Whole Foods $47.23 on Jan 15"}],
)
data = json.loads(response.content[0].text)
print(data)
```

**Key concepts to understand this week:**
- `stop_reason`: `"end_turn"` vs `"tool_use"` — what each means in an agentic loop
- `max_tokens`: What happens if you set it too low?
- Difference between `system` prompt and `messages[0]`

---

### Week 4 — Model Families, Safety & Certification Review

**Concept: Claude model family, capabilities, safety principles**

| Model | Use case | Speed/Cost |
|---|---|---|
| `claude-opus-4-8` | Complex reasoning, long documents, hard tasks | Slower, higher cost |
| `claude-sonnet-4-6` | Balanced — daily coding, API calls (this is what Claude Code uses) | Medium |
| `claude-haiku-4-5` | Fast, cheap — classification, simple extraction | Fastest, lowest cost |

**Exercise — Model comparison:**
Take one of your receipts and ask all three models to categorize it.
Compare speed, accuracy, and verbosity.

**Safety concepts to review:**
- Constitutional AI — how Claude learns values
- Harmlessness, helpfulness, honesty (HHH)
- What Claude refuses and why
- How to write prompts that are clear about intent (so Claude doesn't refuse legitimate tasks)

**Certification review checklist:**
- [ ] Can I explain the difference between a system prompt and a human turn?
- [ ] Can I implement a tool use loop from scratch?
- [ ] Do I know what `temperature` does and when to set it to 0?
- [ ] Can I explain prompt caching and why it reduces cost?
- [ ] Do I know the context window size for each model?
- [ ] Can I describe 3 real-world use cases where Claude outperforms a simpler approach?

---

## Experiments Library

Save all experiments in `docs/study/experiments/`. Run them against your live app.

| File | What it does |
|---|---|
| `financius_agent.py` | Agentic loop querying your Financius API |
| `receipt_parser.py` | Structured JSON extraction from receipt text |
| `sync_analyzer.py` | Claude explains your sync_events table patterns |
| `budget_advisor.py` | Claude generates budget advice from your real spending |
| `model_compare.py` | Same prompt across opus/sonnet/haiku — compare outputs |

---

## Study Journal

Keep a running log in `docs/study/journal.md`. One entry per session:

```markdown
## 2026-05-30

**Task:** Added email to JWT payload

**What Claude did well:**
- Found both call sites without being told
- Knew to check the refresh token path too

**What surprised me:**
- Claude read session.js before editing it even though I didn't ask

**Concept this connects to:**
- Tool use — Claude decides what to read based on the task, not just what I mention
- Context: it kept the 6-phase migration context without me repeating it

**One thing I'd test differently:**
- Try the same task with a more vague prompt and see if it still finds both call sites
```

---

## Connecting Android + Web to Claude Study

Your Android Financius app syncing to your Django backend is itself a study topic.

| Sync scenario | Claude concept to explore |
|---|---|
| Android sends a batch of receipts | Multi-turn tool use — process each receipt one call at a time |
| Category suggestion for a new shop | Retrieval-augmented generation — give Claude your category list as context |
| Anomaly detection in spending | Chain-of-thought — ask Claude to reason step by step before flagging |
| Auto-classify an uncategorized receipt | Few-shot — show 3 examples of category assignments, then ask for the 4th |

---

## Key Resources

| Resource | Why it matters |
|---|---|
| [Anthropic docs — Tool use](https://docs.anthropic.com/en/docs/tool-use) | Required for the API exercises above |
| [Anthropic docs — Prompt engineering](https://docs.anthropic.com/en/docs/prompt-engineering) | Covers all prompting techniques tested in certification |
| [Anthropic docs — Models overview](https://docs.anthropic.com/en/docs/about-claude/models) | Model names, context windows, pricing |
| Your `docs/phases/` folder | Case study: 6 phases of AI-assisted Django migration |
| Your `.claude/commands/django-new.md` | Real example of a well-engineered skill/prompt |

---

## Progress Tracker

```
Week 1 — Claude Code & Context         [ ] Mon [ ] Tue [ ] Wed [ ] Thu [ ] Fri
Week 2 — Prompt Engineering            [ ] Mon [ ] Tue [ ] Wed [ ] Thu [ ] Fri
Week 3 — Claude API & Tool Use         [ ] Mon [ ] Tue [ ] Wed [ ] Thu [ ] Fri
Week 4 — Models, Safety & Review       [ ] Mon [ ] Tue [ ] Wed [ ] Thu [ ] Fri

Certification readiness:
  [ ] Completed financius_agent.py experiment
  [ ] Completed receipt_parser.py experiment
  [ ] Completed model_compare.py experiment
  [ ] Wrote 20+ journal entries
  [ ] Can explain tool use loop without notes
  [ ] Reviewed all Anthropic prompt engineering docs
```
