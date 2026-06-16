# Worktrunk Command Reference

Use this when the user asks how to run core `wt` commands or when a workflow depends on exact command behavior.

## Global Options

| Option | Meaning |
| --- | --- |
| `-C <path>` | Run command as if started in `path` |
| `--config <path>` | Use a specific user config file |
| `-v` | Show info logs and template variables |
| `-vv` | Also write debug trace, raw subprocess output, and diagnostic files under `.git/wt/logs/` |
| `-y`, `--yes` | Skip approval prompts |

## `wt switch`

Switch to a worktree or create one when needed. This navigates between worktree directories rather than switching branches in place.

```bash
wt switch feature-auth
wt switch -
wt switch --create new-feature
wt switch --create hotfix --base production
wt switch --create fix --base=@
wt switch pr:123
wt switch https://github.com/owner/repo/pull/123
```

Creation sequence:

1. `pre-switch` blocks.
2. Worktree is created at configured path.
3. Shell changes directory.
4. `pre-start` blocks.
5. `post-start` and `post-switch` run in background.

Key options:

| Option | Meaning |
| --- | --- |
| `-c`, `--create` | Create new branch |
| `-b`, `--base <BASE>` | Base branch or shortcut |
| `-x`, `--execute <CMD>` | Run command after switching |
| `--clobber` | Remove stale non-worktree path at target |
| `--no-cd` | Do not change parent shell directory |
| `--branches` | Picker includes branches without worktrees |
| `--remotes` | Picker includes remote branches |
| `--no-hooks` | Skip hooks |
| `--format json` | Structured output |

Shortcuts: `^` default branch, `@` current branch/worktree, `-` previous worktree, `pr:N` PR branch, `mr:N` MR branch.

PR/MR resolution needs `gh` for GitHub, `glab` for GitLab, `tea` for Gitea experimental, or `az` for Azure DevOps experimental.

## `wt list`

List worktrees, branch state, remote divergence, and optional CI/LLM data.

```bash
wt list
wt list --full
wt list --branches --full
wt list --remotes
wt list --format=json
```

`--full` adds network/LLM columns: CI status, diff since merge-base, and LLM branch summaries.

Important symbols:

| Symbol | Meaning |
| --- | --- |
| `@` | Current worktree |
| `^` | Default branch |
| `+` | Staged files |
| `!` | Modified unstaged files |
| `?` | Untracked files |
| `x` or conflict symbol in UI | Merge conflicts |
| `/` | Branch without worktree |
| `_` | Same commit as default branch and clean |
| `-` in default-branch state | Same commit as default branch with uncommitted changes |
| `subsumed/integrated` symbol | Content integrated into default branch or target |
| `up` / `down` arrows | Ahead/behind default branch or remote |
| `locked` symbol | Locked worktree |
| `.` placeholder | Loading, timeout, or stale data |

JSON queries:

```bash
wt list --format=json | jq -r '.[] | select(.is_current) | .path'
wt list --format=json | jq '.[] | select(.working_tree.modified)'
wt list --format=json | jq '.[] | select(.operation_state == "conflicts")'
wt list --format=json | jq '.[] | select(.main.ahead > 0) | .branch'
wt list --format=json | jq '.[] | select(.main_state == "integrated" or .main_state == "empty") | .branch'
```

## `wt merge`

Merge current branch into target. This direction differs from `git merge`: `wt merge main` means "merge current branch into main".

```bash
wt merge
wt merge develop
wt merge --no-remove
wt merge --no-squash
wt merge --no-ff
wt merge --no-commit
```

Default pipeline:

1. Commit or prepare changes.
2. Squash since target into one commit.
3. Rebase onto target if behind.
4. Run `pre-merge`.
5. Fast-forward target, or create merge commit with `--no-ff`.
6. Run `pre-remove`.
7. Remove worktree and integrated branch unless disabled.
8. Run `post-remove` and `post-merge` in background.

Key options:

| Option | Meaning |
| --- | --- |
| `--no-squash` | Preserve commit history |
| `--no-commit` | Do not commit/squash; requires clean tree |
| `--no-rebase` | Do not rebase before merge |
| `--no-remove` | Keep worktree after merge |
| `--no-ff` | Create merge commit |
| `--stage all\|tracked\|none` | Control staging before commit/squash |
| `--no-hooks` | Skip hooks |
| `--format json` | Structured output |

## `wt remove`

Remove worktree and delete branch when safely integrated. Defaults to current worktree.

```bash
wt remove
wt remove feature-branch
wt remove old-feature another-branch
wt remove --no-delete-branch feature-branch
wt remove -D experimental
```

Safe branch deletion handles same-commit, ancestor, empty diff, matching tree, merge-adds-nothing, and patch-id match cases. This supports squash and rebase workflows.

Force flags:

| Option | Scope | Use |
| --- | --- | --- |
| `--force`, `-f` | Worktree | Delete dirty worktree |
| `--force-delete`, `-D` | Branch | Delete unintegrated branch |
| `--no-delete-branch` | Branch | Keep branch |
| `--foreground` | Removal | Wait for full deletion |

Detached HEAD worktrees must be removed by path.

## `wt step`

Use individual building blocks for manual review or automation.

| Command | Purpose | Stability |
| --- | --- | --- |
| `commit` | Stage and commit with LLM-generated message | stable |
| `squash` | Squash commits since target | stable |
| `rebase` | Rebase onto target | stable |
| `push` | Fast-forward target to current branch | stable |
| `diff` | Show all changes since branching, including untracked | stable |
| `copy-ignored` | Copy gitignored files between worktrees | stable |
| `eval` | Evaluate template expression | experimental |
| `for-each` | Run command in every worktree | experimental |
| `promote` | Swap branch into main worktree | experimental |
| `prune` | Remove worktrees merged into default branch | experimental |
| `relocate` | Move worktrees to expected paths | experimental |
| `tether` | Run process and kill process tree when worktree disappears | experimental |

Useful commands:

```bash
wt step commit --dry-run
wt step squash --stage=none
wt step rebase develop
wt step push --no-ff
wt step diff -- --stat
wt step copy-ignored --dry-run
wt step prune --dry-run
wt step eval '{{ branch | hash_port }}'
wt step for-each -- sh -c 'git status --short'
wt step tether -- npm run dev
```

## `wt hook`

Run or inspect configured hooks.

```bash
wt hook show
wt hook show --expanded
wt hook pre-merge
wt hook pre-merge test
wt hook pre-merge user:
wt hook pre-merge project:
wt hook pre-merge user:test
wt hook pre-start --branch=feature/test
wt hook pre-merge -- --extra args
```

## `wt config`

```bash
wt config shell install
wt config create
wt config create --project
wt config show
wt config show --full
wt config approvals add
wt config approvals clear
wt config alias show
wt config alias dry-run deploy -- --env=staging
wt config state default-branch
wt config state cache clear
wt config state logs --format=json
wt config state marker set "WIP"
wt config state vars set env=staging
```
