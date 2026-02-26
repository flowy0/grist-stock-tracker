# Kimi Code Agent Configuration

This folder contains custom agent configurations for the Grist Stock Tracker project.

## Quick Start

### Use the Developer Agent

```bash
# Start Kimi with the project-specific agent
kimi --agent-file .kimi/agent.yaml

# Or from any directory
kimi --agent-file /path/to/grist-stock-tracker/.kimi/agent.yaml
```

## Configuration Files

| File | Purpose |
|------|---------|
| `agent.yaml` | Main developer agent configuration |
| `system-prompt.md` | System prompt with project context |
| `subagents/reviewer.yaml` | Code review specialist subagent |
| `subagents/tester.yaml` | Test generation specialist subagent |

## Available Subagents

### 1. Code Reviewer

Use when you want a focused code review:

```
Can you review the code in scripts/csv_import_helper.py using the reviewer subagent?
```

The AI will spawn the `reviewer` subagent which will:
- Check type hints, error handling, logging
- Verify UV usage
- Check medallion architecture compliance
- Provide a quality rating (A-F)

### 2. Test Generator

Use when you need test cases written:

```
Please generate tests for the functions in scripts/price_updater.py using the tester subagent.
```

The AI will spawn the `tester` subagent which will:
- Generate pytest test cases
- Cover happy paths and edge cases
- Aim for >80% coverage
- Follow project testing conventions

## Tool Permissions

This developer agent has access to:

| Tool | Access | Purpose |
|------|--------|---------|
| `Shell` | ✅ Yes | Run docker-compose, uv, git commands |
| `ReadFile` | ✅ Yes | Read source files |
| `WriteFile` | ✅ Yes | Create new files |
| `StrReplaceFile` | ✅ Yes | Edit existing files |
| `Glob/Grep` | ✅ Yes | Search files |
| `SearchWeb` | ✅ Yes | Look up documentation |
| `FetchURL` | ✅ Yes | Read API docs |
| `Task` | ✅ Yes | Spawn subagents |
| `SetTodoList` | ✅ Yes | Track tasks |
| `ReadMediaFile` | ❌ No | Not needed for this project |

## Security Notes

### File Access Restriction

This agent is configured to **only access files within the project directory** (`${KIMI_WORK_DIR}`).

**Enforced via system prompt:**
- ✅ Allowed: Relative paths like `scripts/file.py`, `samples/data.csv`
- ❌ Forbidden: Absolute paths outside working directory
- ❌ Forbidden: Parent directory traversal like `../`

**Important Limitations:**
1. Kimi Code does not have a technical enforcement mechanism to block file access outside the working directory
2. The AI can still technically access files with absolute paths (e.g., `/Users/other/file.txt`)
3. **User approval is the safeguard** - you will be prompted to approve any file operation

**Best Practices:**
- Always review the file path before approving write operations
- If the AI suggests accessing files outside the project, deny the operation
- Copy any needed external files into the project directory first

### Other Security Measures

1. **Approvals Required**: All file writes and shell commands require user approval (unless in YOLO mode)

2. **Subagents are Sandboxed**: Subagents run in isolated contexts and cannot spawn other subagents

3. **Review Subagent is Read-Only**: The `reviewer` subagent cannot write files or run commands - it only reads and reports

## Customization

### Temporarily Disable a Tool

Edit `agent.yaml` and add to `exclude_tools`:

```yaml
exclude_tools:
  - "kimi_cli.tools.shell:Shell"  # Block shell commands
```

### Change System Prompt

Edit `system-prompt.md` to modify the AI's behavior and context.

### Add More Subagents

1. Create a new file in `subagents/` (e.g., `documenter.yaml`)
2. Add to `agent.yaml` under `subagents:`
3. Use via Task tool

## Troubleshooting

### Agent file not found

```bash
# Make sure you're in the project root
cd /path/to/grist-stock-tracker
kimi --agent-file .kimi/agent.yaml
```

### Changes not taking effect

```bash
# Reload configuration within Kimi
/reload
```

### Switch back to default agent

```bash
# Start without --agent-file flag
kimi
```

## See Also

- [Kimi Code Agents Documentation](https://moonshotai.github.io/kimi-cli/en/customization/agents.md)
- [Project AGENTS.md](../AGENTS.md) - Project technical documentation
- [Implementation Todo](../docs/implementation-todo.md) - Development checklist
