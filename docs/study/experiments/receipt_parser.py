"""
Experiment: Structured Receipt Parser
Week 3 — Structured Output

Claude parses freeform receipt text into structured JSON.
Demonstrates: system prompts, structured output, temperature=0 for determinism.

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 docs/study/experiments/receipt_parser.py
"""
import json
import anthropic

client = anthropic.Anthropic()

SYSTEM = """You are a receipt parser. Given raw receipt text, extract the fields below.
Return ONLY valid JSON — no explanation, no markdown, no code fences.

Schema:
{
  "store": "string — store name",
  "date": "string — YYYY-MM-DD or null",
  "total": "number — total amount in dollars",
  "items": [{"name": "string", "price": "number"}],
  "category": "one of: Groceries, Dining, Transport, Health, Entertainment, Shopping, Utilities, Other"
}"""

RECEIPTS = [
    "Whole Foods Market  2026-01-15\nOrganic Milk $4.99\nBread $3.49\nApples $6.50\nTOTAL: $14.98",
    "UBER  Jan 20 2026  Trip to airport  $34.50",
    "Netflix monthly charge $15.99  01/25/2026",
    "CVS Pharmacy  Tylenol 8.99  Bandages 4.50  Total 13.49  Feb 1",
]

if __name__ == "__main__":
    for text in RECEIPTS:
        print(f"\nInput:\n{text}\n")
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            temperature=0,  # deterministic output — always the same for same input
            system=SYSTEM,
            messages=[{"role": "user", "content": text}],
        )
        try:
            parsed = json.loads(response.content[0].text)
            print(f"Parsed: {json.dumps(parsed, indent=2)}")
        except json.JSONDecodeError:
            print(f"Raw output (not JSON): {response.content[0].text}")
        print("-" * 60)
