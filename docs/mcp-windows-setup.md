# Windows MCP Setup

This repo includes a project-scoped `.mcp.json` with MCP servers for local repo access, local PostgreSQL inspection, GitHub access, browser automation, Docker inspection, and URL fetching:

- `filesystem-readonly`
- `postgres-readonly`
- `github`
- `playwright`
- `docker`
- `fetch-url`

Use this note when running the project from Windows with VS Code and GitHub Copilot.

## Prerequisites

- Node.js installed on Windows so `npx` is available
- Docker Desktop installed on Windows and running
- WSL 2 available for the Docker backend

## Start Local PostgreSQL

From the repo root:

```powershell
docker compose -f infra/compose/docker-compose.yml up -d db
```

The local PostgreSQL service is exposed on `localhost:5433`.

## Set the PostgreSQL MCP Connection String

Set the connection string for the current PowerShell session:

```powershell
$env:MCP_POSTGRES_URL = "postgresql://financius:financius_dev@localhost:5433/financius"
```

Persist it for future Windows terminals if needed:

```powershell
setx MCP_POSTGRES_URL "postgresql://financius:financius_dev@localhost:5433/financius"
```

If you use `setx`, restart VS Code after setting the variable.

## Set the GitHub Token

Set the GitHub token for the current PowerShell session:

```powershell
$env:GITHUB_TOKEN = "<your-github-personal-access-token>"
```

Persist it for future Windows terminals if needed:

```powershell
setx GITHUB_TOKEN "<your-github-personal-access-token>"
```

Use a token with only the scopes you actually need. If you use `setx`, restart VS Code after setting the variable.

## Verify Local Prerequisites

```powershell
node --version
npx --version
docker info
```

For browser automation, install Playwright browsers if they are not already present:

```powershell
npx -y playwright install chromium
```

## Verify the Repo MCP Config

```powershell
$json = Get-Content .mcp.json | ConvertFrom-Json
if (
  $null -ne $json.mcpServers.'filesystem-readonly' -and
  $null -ne $json.mcpServers.'postgres-readonly' -and
  $null -ne $json.mcpServers.'github' -and
  $null -ne $json.mcpServers.'playwright' -and
  $null -ne $json.mcpServers.'docker' -and
  $null -ne $json.mcpServers.'fetch-url'
) {
  Write-Output "ALL_SERVERS_PRESENT"
} else {
  Write-Error "Expected MCP servers missing"
}
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