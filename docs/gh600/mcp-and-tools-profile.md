# GH-600 Companion: MCP And Tools Profile (Financius Web)

## Objective

Define a practical tool strategy for GH-600 Domain 2 (Implement tool use and environment interaction), mapped to current repo controls and CI.

This document covers:
- tool inventory and risk classification
- recommended MCP profile for this repository
- allow-list guidance and approval paths
- traceability and rollback expectations

---

## Current Tooling Baseline In Repo

Primary controls already in place:
- `.claude/settings.json`
- `.github/workflows/ci.yml`
- `scripts/run_services.sh`
- `infra/compose/docker-compose.yml`
- `infra/docker/backend.Dockerfile`

Current posture highlights:
- explicit allow rules for common dev tasks (git, python, pytest, ruff, docker)
- explicit deny rules for high-risk destructive actions
- CI pipeline with lint, tests, docker build, deploy trigger
- local service lifecycle script with safe cleanup checks

---

## Tool Risk Classification

## Class A: Read-only (auto allowed)
Examples:
- file discovery and search
- reading docs and source files
- static analysis without mutation

Expected controls:
- no write access
- no deploy capability
- no secret exposure in outputs

## Class B: Local mutation (auto allowed with constraints)
Examples:
- editing source files
- running lint/test commands
- building local docker image

Expected controls:
- require test/lint pass before handoff
- preserve audit trail in PR/commit history
- do not modify unrelated files

## Class C: Environment-impacting (human approval)
Examples:
- database migrations on shared/prod environments
- deployment triggers
- infrastructure changes

Expected controls:
- explicit human approval step
- rollback plan captured before execution
- post-action validation evidence required

## Class D: Irreversible/high-risk (human approval + dual check)
Examples:
- force push
- destructive data deletion
- credential/secret rotation in production

Expected controls:
- blocked by default where possible
- two-person review for execution
- incident-ready audit log

---

## Proposed .mcp.json Profile (Repo Standard)

Create a project-scoped `.mcp.json` with minimal-read-first defaults.

Recommended starter profile:

```json
{
  "mcpServers": {
    "filesystem-readonly": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "env": {
        "MCP_MODE": "readonly"
      }
    }
  }
}
```

Implementation notes:
- keep first server read-oriented to reduce blast radius
- add mutating MCP tools only after guardrail matrix is approved
- pin server package versions once validated in CI

---

## MCP Allow-List Policy

Each MCP server/tool entry should include:
- purpose
- data scope
- write capability (yes/no)
- approval class (A/B/C/D)
- owner

Suggested policy table format:

| MCP Server | Scope | Write Access | Class | Owner | Notes |
|---|---|---|---|---|---|
| filesystem-readonly | repo files | no | A | platform/devex | starter baseline |

Approval rule:
- any new Class C or D tool requires PR approval from maintainer + security reviewer.

---

## CI Validation For MCP Configuration

Add a lightweight validation job in CI to enforce:
1. `.mcp.json` exists.
2. JSON is syntactically valid.
3. required keys are present (`mcpServers`).
4. blocked patterns are absent (unsafe command or unrestricted writes for default profile).

Example check command pattern:

```bash
python -m json.tool .mcp.json >/dev/null
```

Optional stronger validation:
- custom script in `scripts/` that enforces policy keys and class labels.

---

## Execution Safety Paths

## Retry policy
- transient tool failures: retry with bounded attempts and short backoff
- validation failures: do not retry; correct inputs first

## Rollback policy
- capture touched files list before automated edits
- for DB/infra actions, define rollback command before execution
- for deploy actions, retain last known good image/tag

## Escalation policy
Escalate to human when:
- mutation touches secrets/auth/deployment resources
- action is irreversible or compliance-sensitive
- repeated failures indicate context drift or unclear requirements

---

## Traceability And Accountability

Required evidence artifacts per execution cycle:
1. plan summary (goal, scope, constraints)
2. tools used and commands executed
3. validation results (lint/tests/build)
4. unresolved risks and escalation decisions
5. rollback readiness note

These can be attached in PR description or in a `docs/gh600` run log.

---

## Quick Adoption Checklist

1. Create `.mcp.json` with one read-only server.
2. Add CI validation for `.mcp.json` syntax and required fields.
3. Classify each enabled tool into A/B/C/D.
4. Require approvals for Class C/D additions.
5. Record tool usage and validation evidence in each substantial change.

This completes a GH-600-aligned foundation for tool use and environment interaction.
