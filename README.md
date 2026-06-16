# wtflow

An [Agent Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) that teaches AI coding agents how to drive [Worktrunk](https://worktrunk.dev) (`wt`): create isolated worktrees, wire up hooks and dev servers, run several agents in parallel, and merge or clean up safely.

[简体中文](README.zh-CN.md)

![wtflow demo](assets/demo.gif)

## What it is

`wt` already does the mechanics: create a worktree, switch into it, run hooks, merge it back, clean it up. What it doesn't decide for you is *how to combine those pieces in a real repo* — where a hook belongs, whether setup should block `wt switch`, when a worktree is safe to delete, or how to keep two agents from editing the same checkout.

`wtflow` is that decision layer. It's a knowledge pack for the agent — not a new CLI and not a wrapper around `wt`. The agent reads it and uses Worktrunk correctly instead of guessing commands.

Concretely, it helps an agent:

- put config in the right place — project `.config/wt.toml` vs personal `~/.config/worktrunk/config.toml`
- pick the right hook for setup, dev servers, checks, merges, and cleanup
- run multiple agents (Claude Code, Codex, OpenCode) in isolated branches without collisions
- set up LLM-generated commit messages, keeping private commands out of shared config
- preview or dry-run anything destructive before it runs
- debug shell integration, hook failures, and slow `wt list`

## Prerequisites

1. **Worktrunk (`wt`)** — this skill operates `wt`, so install it first and enable shell integration:

   ```bash
   # macOS / Linux
   cargo install worktrunk && wt config shell install
   # macOS (Homebrew)
   brew install worktrunk && wt config shell install
   # Windows (winget installs it as `git-wt`)
   winget install max-sixty.worktrunk && git-wt config shell install
   ```

   See the [Worktrunk install guide](https://worktrunk.dev) for other methods.

2. **An AI agent that supports skills** — Claude Code, Cursor, Codex, or OpenCode.
3. **Git** — Worktrunk runs on top of Git worktrees.
4. **Python 3.8+** — only needed by the repo probe script (the agent runs it for you).

## Install

Clone the repo into the skills directory your agent loads from:

```bash
# Claude Code (personal, all projects)
git clone https://github.com/sylearn/wtflow.git ~/.claude/skills/worktrunk-workflows

# Claude Code (single project)
git clone https://github.com/sylearn/wtflow.git .claude/skills/worktrunk-workflows
```

For Cursor, Codex, or OpenCode, put the folder wherever that agent discovers skills and reference it as `worktrunk-workflows`. Update with `git pull`.

## Usage

Describe the goal in plain language — you don't need to know the `wt` commands. Examples:

**Set up Worktrunk for a repo**

```text
Set up Worktrunk for this repo and create a conservative .config/wt.toml.
Put dependency setup, quick checks, and pre-merge validation in the right stages.
Explain the plan before editing files.
```

**Run agents in parallel**

```text
Start two isolated branches:
- feature-code-review: ask Claude to do code review
- feature-docs: ask OpenCode to improve docs
Start the agents and tell me where each branch is running.
```

**A dev server per branch**

```text
Add a separate dev server for each branch.
Avoid port conflicts, and stop the server when the branch workspace is removed.
```

**Clean up safely**

```text
Check which workspaces can be cleaned up.
Don't remove anything with uncommitted work or unclear status.
```

## How it works

When the skill activates, the agent follows a fixed loop:

1. **Probe** the repo with `scripts/probe_worktrunk_project.py` to learn the package manager, available tools, and existing config.
2. **Classify** the task and load only the relevant file from `references/`.
3. **Design** the config or commands, and preview anything risky before applying it.
4. **Validate** with `wt hook show --expanded`, `wt config alias dry-run`, or `--dry-run` steps.

## Project structure

```text
wtflow/
├── SKILL.md                          # Entry point: operating model, safety rules, decision tables
├── references/
│   ├── command-reference.md          # wt switch / list / merge / remove / step / hook / config
│   ├── config-hooks.md               # Config files, hooks, templates, filters, approvals, state
│   ├── recipes.md                    # Dev servers, databases, cache, tmux, Caddy, bare repos
│   ├── llm-agents.md                 # LLM commit generation + Claude / Codex / OpenCode
│   └── troubleshooting.md            # Shell integration, hooks, LLM, slow list, Windows
├── scripts/
│   └── probe_worktrunk_project.py    # Zero-dependency repo probe → JSON + suggested hooks
├── agents/
│   └── openai.yaml                   # OpenAI / Codex skill manifest
├── README.md
├── README.zh-CN.md
└── LICENSE
```

`SKILL.md` stays short and routes to `references/`, so the agent loads only what a task needs.

## Development

Run the probe directly, and check the script before sending a PR:

```bash
python3 scripts/probe_worktrunk_project.py            # probe current repo
python3 scripts/probe_worktrunk_project.py /path/repo # probe another repo
python3 -m py_compile scripts/probe_worktrunk_project.py
uvx ruff check scripts/
```

## License

MIT © 2026 Sylearn

## Acknowledgments

Shared with the [LINUX DO](https://linux.do) community. Thanks for the support and feedback.
