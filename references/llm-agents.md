# LLM Commits and Agent Integration

Use this when setting up commit message generation, branch summaries, Worktrunk plugins, Claude Code worktree isolation, statusline, or parallel agent workflows.

## LLM Commit Generation

Worktrunk builds a prompt from a template, pipes it to an external command, and reads the commit message from stdout.

It is used by:

- `wt merge`
- `wt step commit`
- `wt step squash`
- `wt list --full` branch summaries when enabled
- `wt switch` picker summary tab when enabled

Configure the command in user config:

```toml
[commit.generation]
command = "..."
```

Do not put the LLM command in `.config/wt.toml`; it depends on the developer's local tools and credentials.

## Supported Command Patterns

Model names below are examples and age quickly; substitute a current fast, text-only model available from your provider.

Claude Code:

```toml
[commit.generation]
command = "MAX_THINKING_TOKENS=0 claude -p --no-session-persistence --model=haiku --tools='' --disable-slash-commands --setting-sources='' --system-prompt=''"
```

Codex:

```toml
[commit.generation]
command = "codex exec -m gpt-5.4-mini -c model_reasoning_effort='low' -c system_prompt='' --sandbox=read-only --json - | jq -sr '[.[] | select(.item.type? == \"agent_message\")] | last.item.text'"
```

OpenCode:

```toml
[commit.generation]
command = "opencode run -m anthropic/claude-haiku-4.5 --variant fast"
```

llm:

```toml
[commit.generation]
command = "llm -m claude-haiku-4.5"
```

aichat:

```toml
[commit.generation]
command = "aichat -m claude:claude-haiku-4.5"
```

If no LLM is configured, Worktrunk falls back to deterministic messages based on changed filenames.

## Branch Summaries

Enable in user config:

```toml
[list]
summary = true
```

Requires `[commit.generation] command`. Summaries are cached until the branch diff changes. They appear in `wt list --full` and in the `wt switch` picker summary preview.

## Prompt Customization

Prefer `template-append` for normal customization.

User style:

```toml
[commit.generation]
template-append = """
- Explain the rationale in the body when the change is material
"""
```

Project style:

```toml
# .config/wt.toml
[commit.generation]
template-append = """
- Use conventional commits
- Reference related issue IDs when present
"""
```

Project `template-append` requires approval before its rendered text is sent to the LLM.

Use full templates only when necessary. Commit template variables include `git_diff`, `git_diff_stat`, `branch`, `repo`, `recent_commits`, `user_guidance`, and `project_guidance`. Squash templates also get `commit_details` and `target_branch`.

## Agent Plugin Installation

Claude Code:

```bash
wt config plugins claude install
```

Manual equivalent:

```bash
claude plugin marketplace add max-sixty/worktrunk
claude plugin install worktrunk@worktrunk
```

Codex:

```bash
wt config plugins codex install
```

Then run `/plugins` in Codex and install Worktrunk from the marketplace.

Manual equivalent:

```bash
codex plugin marketplace add max-sixty/worktrunk
```

OpenCode:

```bash
wt config plugins opencode install
```

This writes the activity tracking plugin under OpenCode's global plugin directory.

## Capability Matrix

| Capability | Claude Code | Codex | OpenCode |
| --- | --- | --- | --- |
| Configuration skill | yes | yes | no |
| Activity tracking in `wt list` | yes | no | yes |
| Worktree isolation | yes | no | no |
| `/wt-switch-create` | yes | no | no |

Codex lacks activity tracking because its hooks do not provide a turn-end event.

## Claude Code Worktree Isolation

Claude Code can run agents in isolated worktrees. The Worktrunk plugin routes `WorktreeCreate` and `WorktreeRemove` through:

```bash
wt switch --create ...
wt remove ...
```

This preserves Worktrunk path templates, hooks, and lifecycle management for agent-created worktrees.

## `/wt-switch-create`

Claude Code only:

```text
/wt-switch-create [<branch>] [<repo>] [-- <task>]
```

It creates or re-enters a Worktrunk worktree, switches the Claude session working directory into it, and runs the task there. If branch is omitted, the command can infer it from the task.

## Claude Statusline

Add to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "wt list statusline --format=claude-code"
  }
}
```

This statusline may fetch CI status from the network. Use it for async statuslines, not synchronous shell prompts.

## Parallel Agent Launches

Direct:

```bash
wt switch --create -x claude feature-auth -- 'Implement auth flow'
wt switch --create -x codex feature-tests -- 'Write API tests'
```

Detached with tmux:

```bash
tmux new-session -d -s feature-auth "wt switch --create feature-auth -x claude -- 'Implement auth flow'"
```

Detached with zellij:

```bash
zellij run -- wt switch --create feature-auth -x claude -- 'Implement auth flow'
```
