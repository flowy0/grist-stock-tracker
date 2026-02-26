# GitHub MCP Server Setup

This guide explains how to set up the GitHub MCP server for Kimi Code to enable native GitHub operations (create PRs, list issues, etc.).

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated
- Node.js/npm (for npx-based MCP servers)

## Setup Options

### Option 1: Using GitHub's Official MCP Server (Recommended)

GitHub provides an official MCP server via GitHub Copilot:

```bash
# Add the GitHub MCP server using stdio transport
kimi mcp add --transport stdio github -- npx -y @github/mcp-server@latest
```

Or with a GitHub token:

```bash
# Get your GitHub token from https://github.com/settings/tokens
export GITHUB_TOKEN="your-github-token"

kimi mcp add --transport stdio github -- npx -y @github/mcp-server@latest --token "$GITHUB_TOKEN"
```

### Option 2: Using Third-Party GitHub MCP Server

Community-maintained GitHub MCP server:

```bash
# Add using npx
kimi mcp add --transport stdio github -- npx -y @modelcontextprotocol/server-github
```

With personal access token:

```bash
kimi mcp add --transport stdio github \
  --env "GITHUB_PERSONAL_ACCESS_TOKEN=your-token" \
  -- npx -y @modelcontextprotocol/server-github
```

### Option 3: Using Local Installation

If you have the MCP server installed locally:

```bash
# Clone and install the GitHub MCP server
git clone https://github.com/github/github-mcp-server.git
cd github-mcp-server
npm install
npm run build

# Add to Kimi
kimi mcp add --transport stdio github -- node /path/to/github-mcp-server/dist/index.js
```

## Configuration File

After adding the server via command line, Kimi stores the configuration in `~/.kimi/mcp.json`.

Example configuration (auto-generated):

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@github/mcp-server@latest"],
      "env": {
        "GITHUB_TOKEN": "your-token"
      }
    }
  }
}
```

## Verify Setup

```bash
# List configured MCP servers
kimi mcp list

# Test the GitHub connection
kimi mcp test github
```

## Using GitHub MCP in Kimi

Once configured, start Kimi with the MCP config:

```bash
# Load MCP configuration
kimi --agent-file .kimi/agent.yaml

# Or explicitly specify MCP config
kimi --agent-file .kimi/agent.yaml --mcp-config-file ~/.kimi/mcp.json
```

### Available GitHub Tools

With the GitHub MCP server, the agent can:

- **Create Pull Requests**: `github_create_pull_request`
- **List Pull Requests**: `github_list_pull_requests`
- **Get PR Details**: `github_get_pull_request`
- **Create Issues**: `github_create_issue`
- **List Issues**: `github_list_issues`
- **Add Comments**: `github_add_comment`
- **Search Code**: `github_search_code`
- **Get File Contents**: `github_get_file_contents`
- **List Branches**: `github_list_branches`
- **Create Branch**: `github_create_branch`

### Example Usage

```
Create a PR from the current feature branch to dev with title "feat: add CSV import"
```

The agent will use the GitHub MCP tool:
```python
# The AI will call something like:
github_create_pull_request(
    owner="your-username",
    repo="grist-stock-tracker",
    title="feat: add CSV import",
    body="Implements bronze to silver layer transformation",
    head="feature/csv-import",
    base="dev"
)
```

## Troubleshooting

### "Command not found" error

Make sure `npx` is available:
```bash
which npx
npm --version
```

### Authentication issues

Ensure your GitHub token has the required scopes:
- `repo` - Full control of private repositories
- `workflow` - Update GitHub Action workflows

Create a token at: https://github.com/settings/tokens

### MCP server not connecting

```bash
# Check server status
kimi mcp list

# Test the server
kimi mcp test github

# View logs (if available)
kimi mcp logs github
```

### Remove and re-add

```bash
# Remove existing configuration
kimi mcp remove github

# Re-add with correct settings
kimi mcp add --transport stdio github -- npx -y @github/mcp-server@latest
```

## Alternative: Use GitHub CLI Directly

If MCP setup is complex, the agent can use `gh` CLI directly via shell commands:

```bash
# These work without MCP:
gh pr create --title "feat: ..." --body "..." --base dev
gh pr list
gh issue create --title "Bug: ..." --body "..."
```

The `git` subagent in this project uses `gh` CLI for PR creation.

## Security Notes

1. **Token Storage**: GitHub tokens in MCP config are stored in `~/.kimi/mcp.json` - ensure this file has proper permissions (600)

2. **Token Scope**: Use minimal required scopes. For PR creation, `repo` scope is sufficient

3. **Approval Required**: All MCP operations require user approval (unless in YOLO mode)

4. **No Commit on Fail**: If MCP operations fail, the agent falls back to `gh` CLI commands

## Project-Specific MCP Config

To use a project-local MCP configuration:

```bash
# Create local config
kimi --mcp-config-file .kimi/mcp.json --agent-file .kimi/agent.yaml
```

This loads `.kimi/mcp.json` which can extend or override global config.
