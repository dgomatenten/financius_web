"""
Experiment: Model Comparison — Opus vs Sonnet vs Haiku
Week 4 — Model Families

Same prompt, three models. Compare speed, cost, and quality.
Demonstrates: model selection tradeoffs for real tasks.

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 docs/study/experiments/model_compare.py
"""
import time
import anthropic

client = anthropic.Anthropic()

MODELS = [
    ("claude-haiku-4-5-20251001", "Haiku 4.5"),
    ("claude-sonnet-4-6",         "Sonnet 4.6"),
    ("claude-opus-4-8",           "Opus 4.8"),
]

PROMPT = """I have these recent receipts:
- Whole Foods $47.23 — Groceries
- Uber $12.50 — Transport
- Netflix $15.99 — Entertainment
- CVS $23.40 — Health
- Chipotle $14.30 — Dining

Give me:
1. Total spent
2. Largest category
3. One concrete saving tip based on this data"""


def run_model(model_id: str, label: str) -> None:
    print(f"\n{'='*50}")
    print(f"Model: {label} ({model_id})")
    print("=" * 50)

    start = time.time()
    response = client.messages.create(
        model=model_id,
        max_tokens=512,
        messages=[{"role": "user", "content": PROMPT}],
    )
    elapsed = time.time() - start

    text = response.content[0].text
    tokens_in = response.usage.input_tokens
    tokens_out = response.usage.output_tokens

    print(f"Response ({elapsed:.1f}s | in={tokens_in} out={tokens_out} tokens):")
    print(text)


if __name__ == "__main__":
    print(f"Prompt:\n{PROMPT}\n")
    for model_id, label in MODELS:
        try:
            run_model(model_id, label)
        except Exception as e:
            print(f"\n{label}: ERROR — {e}")
