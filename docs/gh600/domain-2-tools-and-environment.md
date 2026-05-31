# Domain 2: Tool Use And Environment Interaction

## Why This Domain Matters

GH-600 gives the most weight to tool use and environment interaction because most agent failures are not model failures first. They are usually tool-selection failures, permission failures, environment-scoping mistakes, or missing rollback and escalation rules.

In this repo, Domain 2 is grounded in real operational controls rather than theory:
- `.claude/settings.json` defines an allow-list and deny-list for command execution
- `.github/workflows/ci.yml` constrains execution inside CI
- Docker files define a portable environment boundary
- service scripts define local lifecycle behavior

---

## What GH-600 Is Testing

You should be able to explain and apply these ideas:
- why an agent should choose the smallest sufficient tool for a task
- how to scope tools to a repo, branch, machine, or CI job
- when a tool should be autonomous versus approval-gated
- how retries differ from rollback
- when repeated failures indicate context drift instead of transient errors

This domain is not only about using tools. It is about building a safe tool policy around them.

---

## Repo Mapping

### `.claude/settings.json`

This file is the clearest Domain 2 artifact in the repo.

What it teaches:
- tool permissions are explicit, not implied
- deny rules exist for obviously dangerous actions such as force-push and catastrophic deletes
- environment variables shape execution context
- hooks can enforce post-edit checks

What to notice:
- many allow rules still reflect legacy Flask-era commands
- environment keys currently include `FLASK_APP` and `FLASK_ENV`, which is useful as a study example of configuration drift during a migration
- a policy file can itself become stale, which is an important GH-600 lesson

### `.github/workflows/ci.yml`

This workflow shows environment interaction under CI constraints.

What it teaches:
- CI is a controlled execution environment, not just a test runner
- jobs form an approval path in code: lint, then tests, then docker build, then deploy
- environment variables are injected per job rather than hardcoded into source
- deployment is separated from earlier validation work

### `infra/compose/docker-compose.yml` and `infra/docker/backend.Dockerfile`

These files show another kind of environment boundary: containerized portability.

What they teach:
- the runtime should be reproducible across local and hosted environments
- the environment contract should be versioned and inspectable

---

## Worked Example: Reading The Repo's Tool Policy Correctly

A weak reading of `.claude/settings.json` is: "the repo allows git, python, pytest, docker, and some scripts."

A GH-600-quality reading is more precise:
1. the file defines allowed command families, which is a least-privilege control
2. the deny rules carve out a smaller safe subset even inside a generally allowed tool family
3. the environment block influences behavior and can become outdated
4. the hook block shows how a system can automatically validate edits after a mutating action

That last point matters. Tool use is not just the command itself. It also includes the validation behavior attached to the command.

---

## The Current MCP State In This Repo

The repo now has a project `.mcp.json`.

Current state:
- `filesystem-readonly` is the Phase 1 baseline
- `postgres-readonly` is the Phase 2 expansion
- `github` is the Phase 3 expansion
- `playwright`, `docker`, and `fetch-url` extend the repo into browser, runtime, and HTTP inspection
- all configured servers should still be treated as least-privilege and scope-limited
- PostgreSQL access stays environment-driven through `MCP_POSTGRES_URL`
- GitHub access stays environment-driven through `GITHUB_TOKEN`

Why that matters for study:
- GH-600 expects you to understand tool configuration, not just local shell commands
- MCP now exists here as a real control surface rather than a hypothetical gap
- the study question becomes whether the current MCP expansion is still least-privilege and well-governed

How to reason about it:
- start with read-only filesystem access
- add read-only database inspection only after the first baseline is in place
- add GitHub access only with minimal token scope and a clear collaboration use case
- add Playwright for browser validation, not as an excuse to skip narrow local checks
- add Docker access only if you can classify which container operations are read-only versus environment-impacting
- add fetch-url for low-risk content inspection, not as a substitute for a full mutation-capable API client
- document scope, write capability, owner, and approval class for each server
- treat any future mutation-capable server as a separate risk decision

---

## Common Failure Modes

### Tool overreach
The agent uses a mutating or broad-scope tool when a read-only one would have been sufficient.

### Environment confusion
The workflow assumes local behavior and CI behavior are identical when they are not.

### Retry misuse
A command is retried even though the failure is clearly caused by missing config or permissions.

### Policy drift
The allow-list still describes an older architecture, so the tool policy and the system reality diverge.

---

## What Good Looks Like In An Exam Answer

If asked how to improve this repo's tool strategy, a strong answer would say:
- keep the current `.mcp.json` read-oriented
- classify each enabled MCP server by risk and owner
- review GitHub token scope as part of the MCP threat model
- separate Playwright and fetch inspection use cases from Docker runtime-control use cases
- update stale policy entries that still assume Flask-first execution
- add CI validation for MCP config now that the file exists
- require explicit escalation rules before any future write-capable MCP addition

That answer is stronger than simply saying, "add MCP support," because it ties tool choice to risk and validation.

---

## Self-Check

1. Why is a deny-list still useful even when an allow-list exists?
2. What is the difference between a transient tool failure and a context/config failure?
3. Why is a read-only MCP server the right first addition here?
4. What evidence in the repo shows that CI is part of the tool-control plane?

---

## Next Steps

- Run [labs/lab-tools-and-environment.md](labs/lab-tools-and-environment.md)
- Review [mcp-and-tools-profile.md](mcp-and-tools-profile.md)
- Compare `.claude/settings.json` with the repo's current Django-first architecture and note where policy drift exists