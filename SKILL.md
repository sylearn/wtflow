---
name: worktrunk-workflows
description: Design, configure, operate, and troubleshoot Worktrunk (`wt`) workflows for Git worktrees. Use when setting up or modifying `.config/wt.toml` or `~/.config/worktrunk/config.toml`, adding hooks, aliases, LLM commit generation, per-worktree dev servers/databases/cache copying, agent handoffs for Claude Code/Codex/OpenCode, inspecting `wt list` state, running safe `wt switch`/`wt merge`/`wt remove` workflows, or debugging shell integration, approvals, logs, markers, vars, CI status, or Worktrunk command behavior.
license: MIT
---

# Worktrunk Workflows

## Operating Model

Treat Worktrunk as lifecycle orchestration around Git worktrees. Prefer designing a reversible workflow over emitting one-off commands.

Start every nontrivial task by building context:

1. Run `python3 <skill_dir>/scripts/probe_worktrunk_project.py [repo_path]` (the path defaults to the current directory) to build a JSON snapshot of the target repository. If not in a repo, use it to confirm that and stop before editing.
2. Inspect existing `.config/wt.toml`, `~/.config/worktrunk/config.toml` only when the task touches config. Preserve comments and existing structure.
3. Classify the task: command help, project hooks, user config, LLM commits, agent integration, recipe design, cleanup, or troubleshooting.
4. Load the smallest needed reference:
   - `references/command-reference.md` for `wt switch`, `list`, `merge`, `remove`, `step`.
   - `references/config-hooks.md` for config files, hooks, templates, approvals, state.
   - `references/recipes.md` for dev servers, databases, cache copying, tmux/cmux, Caddy, bare repos, agent handoffs.
   - `references/llm-agents.md` for LLM commit generation and Claude/Codex/OpenCode integration.
   - `references/troubleshooting.md` for shell integration, hook failures, LLM failures, slow `wt list`, Windows.

## Safety Rules

- Do not remove worktrees or branches unless the user explicitly asks for cleanup. Prefer `wt list` and dry runs first.
- Never use `wt remove --force`, `wt remove -D`, `wt step prune`, or `wt step relocate --clobber` without explicit intent and a clear preview.
- For user config (`~/.config/worktrunk/config.toml`), show the proposed change before editing unless the user directly asked you to make that exact change.
- Project config (`.config/wt.toml`) is versioned and can be edited proactively when the user asks to set up repo workflow automation.
- Validate hook commands exist before adding them. For npm scripts, inspect `package.json`; for Rust, inspect `Cargo.toml`; for Python, inspect `pyproject.toml` or task files.
- Warn before adding destructive hooks, network calls, privilege escalation, or commands that mutate production resources.
- Use `wt hook show --expanded`, `wt config alias dry-run`, `wt step copy-ignored --dry-run`, `wt step prune --dry-run`, or `wt step relocate --dry-run` when possible before recommending a risky command.

## Config Decision

Choose the target file by scope:

| Request | Put it in |
| --- | --- |
| Personal worktree path, LLM command, personal aliases, user hooks | `~/.config/worktrunk/config.toml` |
| Team setup hooks, dev server URL, copy-ignored excludes, team aliases | `.config/wt.toml` |
| Per-repository personal override | `[projects."<identifier>"]` inside user config |
| Temporary script or CI override | `WORKTRUNK_*` environment variable |

Use `wt config show` inside the repo to find config locations and the project identifier.

## Hook Design Heuristic

Pick hook timing by failure behavior and latency:

| Need | Hook |
| --- | --- |
| Must complete before the new worktree is usable | `pre-start` |
| Long setup, dev server, watcher, cache copy | `post-start` |
| Fast formatter, lint, typecheck before commit/squash | `pre-commit` |
| Expensive tests, builds, security checks before merge | `pre-merge` |
| Cleanup before files disappear | `pre-remove` |
| Stop external processes or remove external resources | `post-remove`, unless `wt step tether` is better |
| Deploy or notify after merge | `post-merge` |
| Update terminal/IDE/multiplexer state before navigation | `pre-switch` |
| Notify or record every switch result | `post-switch` |

Use a table for independent commands and `[[hook]]` pipeline blocks for dependency chains:

```toml
[pre-start]
env = "cp -n .env.example .env 2>/dev/null || true"

[[post-start]]
copy = "wt step copy-ignored"

[[post-start]]
install = "pnpm install"
server = "wt step tether -- pnpm dev -- --port {{ branch | hash_port }}"
```

## Workflow Patterns

### New project setup

1. Probe the repo.
2. Identify package manager and scripts.
3. Draft `.config/wt.toml` with conservative hooks:
   - dependency/env setup in `pre-start` or first `post-start` pipeline step
   - `wt step copy-ignored` in `post-start` if caches matter
   - `wt step tether` for dev servers
   - quick checks in `pre-commit`
   - expensive checks in `pre-merge`
   - `[list] url` when a stable local URL is useful
4. Validate commands directly or with package manager dry runs where available.
5. Run `wt hook show --expanded`.

### LLM commit setup

1. Detect installed tools: `which claude codex opencode llm aichat jq`.
2. Prefer the user's named tool. Otherwise choose an available fast text-only command.
3. Put `[commit.generation] command = "..."`
   in user config, not project config.
4. Use project `template-append` only for shared style rules.
5. Test with `wt step commit --dry-run` in a repo with changes, or at least pipe a small prompt into the configured command.

### Parallel agent workflow

Use `wt switch --create -x <agent>` for direct launches. Use tmux/zellij for background handoffs. For Claude Code, install the Worktrunk plugin if the user wants worktree isolation or `/wt-switch-create`.

```bash
wt switch --create -x claude feature-auth -- 'Implement auth flow'
```

### Merge workflow

Explain that `wt merge <target>` merges the current branch into target, not target into current. Default behavior is squash, rebase if needed, run hooks, fast-forward target, remove integrated worktree and branch.

Use flags intentionally:

- `--no-squash` to preserve commit history.
- `--no-commit` after manual commits with `wt step commit`.
- `--no-rebase` only when already rebased.
- `--no-remove` when the user wants to keep the worktree.
- `--no-ff` for a merge commit.

### Cleanup workflow

Before cleanup, show `wt list` or `wt list --full`. For bulk cleanup use:

```bash
wt step prune --dry-run
```

Only proceed with `wt step prune` after the user accepts the preview or explicitly requested bulk removal.

## Validation Checklist

After editing Worktrunk config:

1. Validate TOML syntax with a parser if available, or run `wt config show`.
2. Run `wt hook show --expanded` if hooks changed.
3. Run `wt config alias dry-run <name>` if aliases changed.
4. Run `wt step copy-ignored --dry-run` if copy rules changed.
5. For project hooks, mention first-run approval and `wt config approvals add` for CI/noninteractive contexts.
6. For `post-*` hooks, mention logs via `wt config state logs`.

## Answer Style

When giving the user commands, include where to run them and why. When editing config, summarize the behavior in lifecycle terms: create, switch, commit, merge, remove. Keep experimental commands labeled experimental.
