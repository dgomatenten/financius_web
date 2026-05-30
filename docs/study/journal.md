# Study Journal

One entry per coding session. Focus on what Claude did — not just what you built.

---

## 2026-05-30

**Task:** Full Django migration (Phases 1–6) + local Docker deployment

**What Claude did well:**
- Held the full 6-phase migration plan in context across multiple sessions
- Diagnosed the `keys()` unhashable bug across 11 identical patterns in one pass
- Found that Flask stored `users.id` as email by reading the actual SQLite schema — didn't assume UUID

**What surprised me:**
- Claude proposed `wrap_werkzeug_hash` before I asked — it reasoned ahead to the password migration problem
- When the Docker container failed due to a DNS race, Claude explained the root cause (Docker restart + DNS timing) and wrote a retry loop, not just a workaround

**What Claude struggled with:**
- Needed correction when the Jinja2 `startswith()` syntax wasn't fully converted (left trailing `')`  characters)
- Required iterative fixes for the data migration — SQLite schema was different from assumptions (email PK, scrypt hashes, non-UUID refresh token IDs)

**Concept this connects to:**
- **Tool use:** Claude chose which files to read based on the error, not a fixed plan
- **Context management:** Session summaries preserved intent across context window resets
- **Prompt engineering:** CLAUDE.md constraints (envelope, type hints, no bare except) shaped every code output without repeating them

**One thing to experiment with:**
- Run `financius_agent.py` — ask Claude questions about my real spending data using the tool use loop I just learned to build
