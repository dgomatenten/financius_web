"""
Experiment: Prompt A/B Test — Domain 2
Claude Certified Architect — Foundations

Compare vague vs. structured prompts on receipt categorization accuracy.
Demonstrates: role + task + format + examples vs. no structure.

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 docs/study/experiments/prompt_ab_test.py
"""
import json
import anthropic

client = anthropic.Anthropic()

# Ground truth for scoring
RECEIPTS_WITH_ANSWERS = [
    ("Whole Foods Market $47.23", "Groceries"),
    ("Uber ride to airport $34.50", "Transport"),
    ("Netflix monthly $15.99", "Entertainment"),
    ("CVS Pharmacy Tylenol $8.99", "Health"),
    ("Chipotle burrito $14.30", "Dining"),
    ("Amazon order $23.45", "Shopping"),
    ("Con Edison electric bill $112.00", "Utilities"),
    ("Target groceries $67.80", "Groceries"),
    ("Starbucks coffee $6.50", "Dining"),
    ("Lyft ride $12.00", "Transport"),
]

# ── Prompt A: vague ───────────────────────────────────────────────────────────
SYSTEM_A = "You help with finances."

def prompt_a(receipt: str) -> str:
    r = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=32,
        temperature=0,
        system=SYSTEM_A,
        messages=[{"role": "user", "content": f"What category is this? {receipt}"}],
    )
    return r.content[0].text.strip()

# ── Prompt B: structured ──────────────────────────────────────────────────────
SYSTEM_B = """You are a receipt categorizer for a personal finance app.

Assign exactly one category. Return ONLY the category name, nothing else.

Valid categories: Groceries, Dining, Transport, Health, Entertainment, Shopping, Utilities, Other

Examples:
- "Whole Foods $47" → Groceries
- "Uber ride $12" → Transport
- "Netflix $16" → Entertainment"""

def prompt_b(receipt: str) -> str:
    r = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=16,
        temperature=0,
        system=SYSTEM_B,
        messages=[{"role": "user", "content": receipt}],
    )
    return r.content[0].text.strip()


def score(predicted: str, expected: str) -> bool:
    return expected.lower() in predicted.lower()


if __name__ == "__main__":
    VALID = {"Groceries", "Dining", "Transport", "Health", "Entertainment", "Shopping", "Utilities", "Other"}

    print(f"{'Receipt':<40} {'Expected':<14} {'A (vague)':<20} {'B (structured)':<14}")
    print("-" * 90)

    a_correct = b_correct = 0
    for receipt, expected in RECEIPTS_WITH_ANSWERS:
        a_out = prompt_a(receipt)
        b_out = prompt_b(receipt)
        a_ok = score(a_out, expected)
        b_ok = score(b_out, expected)
        a_correct += a_ok
        b_correct += b_ok
        a_mark = "✓" if a_ok else "✗"
        b_mark = "✓" if b_ok else "✗"
        print(f"{receipt:<40} {expected:<14} {a_mark} {a_out[:17]:<18} {b_mark} {b_out}")

    n = len(RECEIPTS_WITH_ANSWERS)
    print(f"\nPrompt A (vague):      {a_correct}/{n} correct ({a_correct/n*100:.0f}%)")
    print(f"Prompt B (structured): {b_correct}/{n} correct ({b_correct/n*100:.0f}%)")
    print("\nKey lesson: role + valid categories + examples = dramatically better accuracy")
