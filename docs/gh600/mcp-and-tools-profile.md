# GH-600 Companion: MCP And Tools Profile (Financius Web)

## Objective

Define a practical tool strategy for GH-600 Domain 2 (Implement tool use and environment interaction), mapped to current repo controls and CI.

This document covers:
- tool inventory and risk classification
- recommended MCP profile for this repository
- allow-list guidance and approval paths
- traceability and rollback expectations

## What GH-600 Is Testing Here

This document is useful for study only if you connect policy to judgment.

For GH-600, this domain is testing whether you can:
- choose the smallest safe tool for the task
- classify tools by risk and environment impact
- distinguish retry from rollback and escalation
- describe why a read-only-first tool posture reduces blast radius

The repo already demonstrates most of this through `.claude/settings.json`, CI, and the project-scoped `.mcp.json`. The useful study question is no longer whether MCP should exist here, but whether the configured MCP surface is appropriately minimal and risk-classified.

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

Study note:
- the repo now has a minimal MCP baseline with read-only filesystem and PostgreSQL-oriented data access
- `.claude/settings.json` also contains legacy Flask-era environment values, which makes it a useful example of policy drift during a migration

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

## Worked Repo Classification

Use the repo's current workflows to practice classification:

| Action | Suggested Class | Why |
|---|---|---|
| reading source files and tests | A | no mutation and no environment impact |
| editing docs or code locally | B | local mutation with narrow blast radius |
| running local `pytest` or `ruff` | B | mutates no source but does affect execution state and evidence |
| running a real migration on shared data | C | environment-impacting and requires rollback thinking |
| deploy trigger or secret rotation | D | production-adjacent and not safely autonomous |

This table matters because GH-600 questions often hide the real problem inside an apparently simple tool action. The right answer usually depends on risk class, not only task intent.

---

## Current .mcp.json Profile

The repo now has a project-scoped `.mcp.json` with minimal-read-first defaults.

Current profile:

```json
{
  "mcpServers": {
    "filesystem-readonly": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "@modelcontextprotocol/server-filesystem", "."],
      "env": {
        "MCP_MODE": "readonly"
      }
    },
    "postgres-readonly": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "@modelcontextprotocol/server-postgres", "%MCP_POSTGRES_URL%"]
    },
    "github": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "%GITHUB_TOKEN%"
      }
    }
  }
}
```

Implementation notes:
- the first server remains read-oriented to reduce blast radius
- the second server expands into read-oriented database inspection without adding write capability
- the third server adds GitHub context access for repository metadata and collaboration state
- `cmd /c npx` is used because this repo is being worked from Windows
- `MCP_POSTGRES_URL` stays environment-driven to match repo configuration principles
- `GITHUB_TOKEN` stays environment-driven so credentials are not committed into project config

Why this is a good current baseline:
- it improves inspectability without immediately granting write power
- it adds direct visibility into the repo's target PostgreSQL architecture
- it adds repository and workflow context without introducing local filesystem writes
- it keeps secrets and endpoints out of versioned config
- it still follows the GH-600 pattern of starting with minimum viable capability rather than maximum convenience

## Worked MCP Approval Scenario

Scenario:
- a contributor wants to add a filesystem tool with write access so an agent can edit files directly through MCP

Good GH-600 response:
1. reject it as the first MCP addition
2. require a risk classification and owner
3. require justification for why existing local editing paths are insufficient
4. require updated approval rules in the guardrails matrix before adoption

Reason:
- the repo already has mutation paths through existing tooling, so the first MCP server should optimize visibility and control, not expand write scope without need

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
| postgres-readonly | configured Postgres database | no | A | platform/devex | requires `MCP_POSTGRES_URL` in env |
| github | repository metadata and GitHub operations allowed by token scope | no by default study assumption | A/B depending on granted token scope | platform/devex | requires `GITHUB_TOKEN` in env |

Approval rule:
- any new Class C or D tool requires PR approval from maintainer + security reviewer.

Suggested learner exercise:
- take three existing tools in this repo and write their owner, scope, write capability, and approval class as if they were MCP entries

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

Why CI validation matters for GH-600:
- tool configuration is part of the system architecture
- if policy artifacts are not validated, they drift into documentation rather than control
- CI is the cleanest place to prove the tool contract is being enforced consistently

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

## Worked Decision Example

Bad decision:
- add a mutation-capable MCP server because it seems faster than the current local edit workflow

Stronger decision:
- keep the first MCP server read-only, use existing local mutation tools for edits, and require evidence that an additional write-capable server solves a real problem that cannot be handled safely another way

That second answer is stronger because it ties tool expansion to risk and necessity.

---

## Traceability And Accountability

Required evidence artifacts per execution cycle:
1. plan summary (goal, scope, constraints)
2. tools used and commands executed
3. validation results (lint/tests/build)
4. unresolved risks and escalation decisions
5. rollback readiness note

These can be attached in PR description or in a `docs/gh600` run log.

## Self-Check

1. Why is a read-only MCP server the right first addition here?
2. What turns a tool policy file into an actual control surface instead of documentation only?
3. When should a failing tool action be retried versus escalated?
4. Why is policy drift inside `.claude/settings.json` a useful GH-600 study example?

---

## Quick Adoption Checklist

1. Keep `.mcp.json` read-oriented unless the guardrail policy expands deliberately.
2. Add CI validation for `.mcp.json` syntax and required fields.
3. Set `MCP_POSTGRES_URL` and `GITHUB_TOKEN` through environment configuration, not in version control.
4. Classify each enabled MCP server into A/B/C/D.
5. Treat GitHub token scope as part of the risk classification, not just the server name.
6. Require approvals for any future Class C/D additions.
7. Record tool usage and validation evidence in each substantial change.

This completes a GH-600-aligned foundation for tool use and environment interaction.
