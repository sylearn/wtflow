# Worktrunk Workflows

An Agent Skill for using [Worktrunk](https://worktrunk.dev) (`wt`) with Git worktrees, local automation, and parallel AI coding agents.

[简体中文](README.zh-CN.md)

## What This Is

Worktrunk already gives you the important primitives: create a worktree, switch into it, run hooks, merge it back, and clean it up. The hard part starts when an AI agent has to decide how those pieces should fit together in a real repository.

Should a hook live in `.config/wt.toml` or in `~/.config/worktrunk/config.toml`? Should dependency setup block `wt switch`, or run in the background? Is it safe to prune a worktree? Where should an LLM commit command go? How do you launch Claude, Codex, or another agent without mixing their changes in the same checkout?

This skill gives the agent those answers. It is a small knowledge pack: one entry file, focused references, and a repo probe script. The goal is not to wrap Worktrunk with another tool. The goal is to make the agent treat Worktrunk as a lifecycle system instead of a bag of commands.

## What It Helps Agents Do

- Inspect a repository before editing Worktrunk config.
- Pick the right config scope for team settings, personal settings, and temporary overrides.
- Design hooks for create, switch, commit, merge, and remove flows.
- Start one dev server per worktree with stable ports.
- Copy ignored caches when it saves time, without blindly copying everything.
- Launch multiple AI agents in isolated branches.
- Configure LLM-generated commit messages without putting private commands into project config.
- Use dry runs and previews before cleanup or destructive operations.
- Debug shell integration, hook failures, slow `wt list`, and agent plugin issues.

## Why Worktrunk Workflows Are Easy to Get Wrong

Plain Git worktrees are simple on paper. In daily use, the annoying parts are around the edges: directory naming, repeated setup, stale services, copied caches, branch cleanup, and remembering which worktree is safe to remove.

Worktrunk handles much of that lifecycle, but an agent still needs judgment. A bad answer can put a personal LLM command into shared project config, run a slow install as a blocking hook, leave background processes behind, or delete a branch before showing what would be removed.

This skill keeps those decisions explicit. It tells the agent to probe first, choose a reference file, design the workflow, preview risky commands, and validate the result with Worktrunk's own commands.

## See It In Action

One short demo is enough to show the main idea: the user describes the goal, and the agent handles the Worktrunk workflow underneath.

![Worktrunk Workflows demo](assets/demo.gif)

## Demo Prompts

Use these prompts after installing the skill. They are short on purpose: good demos should be easy to read while the agent is running.

### Set Up Worktrunk

```text
Set up Worktrunk for this repo and create a conservative .config/wt.toml.
Put dependency setup, quick checks, and pre-merge validation in the right lifecycle stages.
Explain the plan before editing files.
```

### Run AI Agents in Parallel

```text
Start two isolated branches:

- feature-code-review: ask Claude to do code review
- feature-docs: ask OpenCode to improve docs

Start the agents and tell me where each branch is running.
```

### Add a Dev Server Per Worktree

```text
Add a separate dev server for each branch.
Avoid port conflicts and make sure the server stops when the branch workspace is removed.
```

### Clean Up Safely

```text
Check which workspaces can be cleaned up.
Do not remove anything with uncommitted work or unclear status.
```

## Install

Clone this repository into the skills directory used by your agent.

```bash
git clone https://github.com/Sylearn/wtflow.git ~/.claude/skills/worktrunk-workflows
```

For Cursor, Codex, OpenCode, or other agents, put this folder wherever that agent loads skills from and reference `worktrunk-workflows`.

## Repository Layout

```text
SKILL.md                           # Entry point and operating rules
references/                        # Focused Worktrunk references
scripts/probe_worktrunk_project.py # Zero-dependency repo probe
agents/openai.yaml                 # OpenAI/Codex-style manifest
LICENSE                            # MIT license
```

## Verify Locally

```bash
python3 -m py_compile scripts/probe_worktrunk_project.py
python3 scripts/probe_worktrunk_project.py
uvx ruff check scripts/
```

## License

MIT © 2026 Sylearn
