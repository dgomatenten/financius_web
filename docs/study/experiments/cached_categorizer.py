"""
Experiment: Prompt Caching — Domain 6
Claude Certified Architect — Foundations

Demonstrates prompt caching on a shared system prompt + category list.
Compare cache miss (call 1) vs. cache hit (call 2+) token counts.

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 docs/study/experiments/cached_categorizer.py
"""
import anthropic

client = anthropic.Anthropic()

CATEGORIES = """
Groceries: supermarkets, food stores, Whole Foods, Trader Joe's, Costco, Aldi
Dining: restaurants, cafes, fast food, Chipotle, Starbucks, Uber Eats, DoorDash
Transport: Uber, Lyft, gas stations, parking, public transit, taxis
Health: pharmacies, doctors, dentists, hospitals, CVS, Walgreens, gyms
Entertainment: movies, concerts, Netflix, Spotify, video games, Amazon Prime
Shopping: clothing, electronics, Amazon, Target, department stores
Utilities: electricity, water, internet, phone bills, insurance
Other: anything not matching the above categories
"""

FEW_SHOT = """
Examples:
Input: Whole Foods Market $47.23
Output: {"category":"Groceries","confidence":0.97}

Input: Uber ride $12.50
Output: {"category":"Transport","confidence":0.99}

Input: Netflix $15.99
Output: {"category":"Entertainment","confidence":0.99}

Input: CVS Pharmacy $23.40
Output: {"category":"Health","confidence":0.85}
"""

SYSTEM_TEXT = (
    "You are a receipt categorizer for a personal finance app.\n"
    "Assign exactly one category to each receipt.\n"
    "Return JSON only: {\"category\": \"...\", \"confidence\": 0.0-1.0}\n"
    "No explanation, no markdown.\n\n"
    "## Categories\n" + CATEGORIES + "\n"
    "## Examples\n" + FEW_SHOT
)

RECEIPTS = [
    "Trader Joe's $34.12",
    "Lyft to downtown $18.75",
    "Chipotle $14.30",
    "Amazon Prime $14.99",
    "Walgreens $28.50",
]


def categorize(receipt: str, call_num: int) -> None:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",  # cheapest — good for high-volume classification
        max_tokens=64,
        temperature=0,
        system=[
            {
                "type": "text",
                "text": SYSTEM_TEXT,
                "cache_control": {"type": "ephemeral"},
                # ↑ This block is cached after the first call.
                # The block must be >= 1024 tokens to qualify.
                # TTL: 5 minutes (ephemeral).
            }
        ],
        messages=[{"role": "user", "content": receipt}],
    )

    usage = response.usage
    cached = getattr(usage, "cache_read_input_tokens", 0)
    print(
        f"Call {call_num}: {receipt!r:35s} → {response.content[0].text}\n"
        f"         input={usage.input_tokens} output={usage.output_tokens} "
        f"cache_read={cached} cache_write={getattr(usage, 'cache_creation_input_tokens', 0)}"
    )


if __name__ == "__main__":
    system_tokens = len(SYSTEM_TEXT) // 4  # rough estimate: 1 token ≈ 4 chars
    print(f"System prompt ≈ {system_tokens} tokens (need ≥ 1024 to cache)\n")
    print("First call = cache MISS (system prompt is written to cache)")
    print("Later calls = cache HIT (system prompt served from cache at ~10% cost)\n")

    for i, receipt in enumerate(RECEIPTS, start=1):
        categorize(receipt, i)

    print("\nKey insight:")
    print("  Call 1: cache_write > 0, cache_read = 0  → MISS, block stored")
    print("  Call 2+: cache_write = 0, cache_read > 0 → HIT, 90% cheaper on input")
