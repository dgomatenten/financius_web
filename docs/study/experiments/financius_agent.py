"""
Experiment: Financius Spending Agent
Week 3 — Claude API & Tool Use

Claude uses a tool to call your live Financius API and answers
natural-language questions about your real spending data.

Setup:
    pip install anthropic requests
    export ANTHROPIC_API_KEY=sk-ant-...
    export FINANCIUS_TOKEN=<paste accessToken from browser localStorage>

Run:
    python3 docs/study/experiments/financius_agent.py
"""
import json
import os

import anthropic
import requests

API_BASE = "http://localhost:8001"
TOKEN = os.environ.get("FINANCIUS_TOKEN", "")

client = anthropic.Anthropic()

# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "list_receipts",
        "description": "Fetch receipts from the Financius API, newest first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max number of receipts to return (default 20, max 100)",
                },
            },
        },
    },
    {
        "name": "list_categories",
        "description": "Fetch all spending categories.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def _headers() -> dict:
    return {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


def call_tool(name: str, inputs: dict) -> str:
    if name == "list_receipts":
        limit = inputs.get("limit", 20)
        r = requests.get(f"{API_BASE}/api/v1/receipts/", headers=_headers(), params={"limit": limit})
        return json.dumps(r.json(), indent=2)

    if name == "list_categories":
        r = requests.get(f"{API_BASE}/api/v1/categories/", headers=_headers())
        return json.dumps(r.json(), indent=2)

    return f"Unknown tool: {name}"


# ── Agentic loop ──────────────────────────────────────────────────────────────

def ask(question: str) -> str:
    """Run a full tool-use loop and return Claude's final answer."""
    messages = [{"role": "user", "content": question}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            tools=TOOLS,
            messages=messages,
        )

        # Claude is done — return the text answer
        if response.stop_reason == "end_turn":
            return next(
                (b.text for b in response.content if hasattr(b, "text")),
                "(no text response)",
            )

        # Claude wants to use a tool
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [tool] {block.name}({block.input})")
                    result = call_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        break

    return "(unexpected stop reason)"


# ── Run it ────────────────────────────────────────────────────────────────────

QUESTIONS = [
    "How many receipts do I have in total? What is the average amount?",
    "What are my top 3 spending categories based on recent receipts?",
    "Is there anything unusual or surprising about my spending patterns?",
]

if __name__ == "__main__":
    if not TOKEN:
        print("Set FINANCIUS_TOKEN env var. Get it from browser:")
        print("  localStorage.getItem('accessToken')")
        raise SystemExit(1)

    for q in QUESTIONS:
        print(f"\nQ: {q}")
        print(f"A: {ask(q)}")
        print("-" * 60)
