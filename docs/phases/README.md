# Phase Docs

One doc per migration phase. Each doc is written as the phase progresses — not before,
not after. It is the source of truth for decisions made, schema divergences, and gotchas.

## Doc structure (copy for each new phase)

```markdown
# Phase N — <Title>

## Status
[ ] In progress | [ ] Complete | Date: YYYY-MM-DD

## Goal
One sentence.

## Models / Endpoints ported
| Flask | Django | Notes |
|---|---|---|

## Schema divergences
Any column renames, type changes, or dropped fields vs the SQLite schema.

## Decisions
Numbered list of non-obvious choices made and why.

## Test coverage
Links to test files written for this phase.

## Checklist
- [ ] Models migrated
- [ ] Migrations applied
- [ ] Unit tests passing
- [ ] Contract tests passing (if endpoints exist)
- [ ] Phase doc updated
```

## Phases

| Phase | Doc | Status |
|---|---|---|
| 1 — Django Scaffold | [phase-1-scaffold.md](phase-1-scaffold.md) | Complete |
| 2 — Port Models | [phase-2-models.md](phase-2-models.md) | Complete |
| 3 — Port Endpoints | [phase-3-endpoints.md](phase-3-endpoints.md) | Complete |
| 4 — Port Auth | [phase-4-auth.md](phase-4-auth.md) | Complete |
| 5 — Data Migration | [phase-5-data-migration.md](phase-5-data-migration.md) | Complete |
| 6 — Cut Over | [phase-6-cutover.md](phase-6-cutover.md) | Complete |
