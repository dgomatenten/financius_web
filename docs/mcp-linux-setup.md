# Linux MCP Setup

This repo includes a project-scoped `.mcp.json` with MCP servers for local repo access, local PostgreSQL inspection, GitHub access, browser automation, Docker inspection, and URL fetching:

- `filesystem-readonly`
- `postgres-readonly`
- `github`
- `playwright`
- `docker`
- `fetch-url`

The project config is now cross-platform: it uses `node` plus `scripts/mcp-launcher.js`, which dispatches to `npx` correctly on Linux and Windows.

## Prerequisites

- Node.js installed so `node` and `npx` are available on `PATH`
- Docker Engine or Docker Desktop installed and running if you want the Docker MCP server
- A Linux shell session that inherits your environment variables into VS Code

## Start Local PostgreSQL

From the repo root:

```bash
docker compose -f infra/compose/docker-compose.yml up -d db
```

The local PostgreSQL service is exposed on `localhost:5433`.

## Set The PostgreSQL MCP Connection String

Set the variable for the current shell session:

```bash
export MCP_POSTGRES_URL="postgresql://financius:financius_dev@localhost:5433/financius"
```

Persist it for future shells if needed by adding the same line to your shell profile, for example `~/.bashrc` or `~/.zshrc`.

Restart VS Code or reload the window if your MCP client does not pick up the new variable immediately.

## Set The GitHub Token

Set the variable for the current shell session:

```bash
export GITHUB_TOKEN="<your-github-personal-access-token>"
```

Persist it in your shell profile if needed.

Use a token with only the scopes you actually need.

## Verify Local Prerequisites

```bash
node --version
npx --version
docker info
```

For browser automation, install Playwright browsers if they are not already present:

```bash
npx -y playwright install chromium
```

## Verify The Repo MCP Config

```bash
python3 -m json.tool .mcp.json >/dev/null

node -e 'const fs=require("fs"); const json=JSON.parse(fs.readFileSync(".mcp.json","utf8")); const required=["filesystem-readonly","postgres-readonly","github","playwright","docker","fetch-url"]; const missing=required.filter((name)=>!json.mcpServers[name]); if (missing.length) { console.error(`Missing MCP servers: ${missing.join(", ")}`); process.exit(1); } console.log("ALL_SERVERS_PRESENT");'
```

## Expected Client Behavior

After VS Code restarts and the MCP-aware client loads the project config, it should discover:

- `filesystem-readonly`
- `postgres-readonly`
- `github`
- `playwright`
- `docker`
- `fetch-url`

Use read-only checks first:

- inspect repo files
- inspect Django models
- inspect PostgreSQL schema or non-sensitive rows
- inspect repository metadata, issues, or pull requests through GitHub MCP
- inspect local pages and UI behavior through Playwright MCP
- inspect local container, image, and compose state through Docker MCP
- fetch local or external HTTP content through the URL fetch MCP