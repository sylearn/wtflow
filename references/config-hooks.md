# Worktrunk Config, Hooks, Templates, and State

Use this when editing `.config/wt.toml`, `~/.config/worktrunk/config.toml`, hook definitions, aliases, approvals, or state.

## Config Files

| File | Scope | Typical contents | Shared |
| --- | --- | --- | --- |
| `~/.config/worktrunk/config.toml` | Personal | worktree path, LLM command, user hooks, personal aliases | no |
| `.config/wt.toml` | Repository | team hooks, dev URL, project aliases, project prompt append | yes |
| system config | Organization | shared defaults | machine dependent |

Create and inspect:

```bash
wt config create
wt config create --project
wt config show
wt config show --full
```

## User Config Patterns

```toml
worktree-path = "{{ repo_path }}/../{{ repo }}.{{ branch | sanitize }}"

[commit.generation]
command = "MAX_THINKING_TOKENS=0 claude -p --no-session-persistence --model=haiku --tools='' --disable-slash-commands --setting-sources='' --system-prompt=''"

[list]
summary = false
full = false
branches = false
remotes = false
task-timeout-ms = 0
timeout-ms = 0

[commit]
stage = "all"

[merge]
squash = true
commit = true
rebase = true
remove = true
verify = true
ff = true

[remove]
delete-branch = true

[switch]
cd = true

[switch.picker]
pager = "delta --paging=never"

[step.copy-ignored]
exclude = []
```

Per-project user overrides:

```toml
[projects."github.com/user/repo"]
worktree-path = ".worktrees/{{ branch | sanitize }}"
list.full = true
merge.squash = false
remove.delete-branch = false
pre-start.env = "cp .env.example .env"
step.copy-ignored.exclude = [".repo-local-cache/"]
aliases.deploy = "make deploy BRANCH={{ branch }}"
```

Find the project identifier with `wt config show`.

## Project Config Patterns

```toml
pre-start = "npm ci"
post-start = "npm run dev"
pre-merge = "npm test"

[list]
url = "http://localhost:{{ branch | hash_port }}"

[forge]
platform = "github"
hostname = "github.example.com"

[commit.generation]
template-append = """
- Use conventional commits
- Reference related issue IDs when present
"""

[step.copy-ignored]
exclude = [".cache/", ".turbo/"]

[aliases]
deploy = "make deploy BRANCH={{ branch }}"
```

Only `template-append` is honored from project `[commit.generation]`. The LLM command and full prompt templates remain user config.

## Hook Types

| Event | Blocking | Background |
| --- | --- | --- |
| switch | `pre-switch` | `post-switch` |
| create/start | `pre-start` | `post-start` |
| commit | `pre-commit` | `post-commit` |
| merge | `pre-merge` | `post-merge` |
| remove | `pre-remove` | `post-remove` |

`pre-*` failures abort operations. `post-*` hooks run detached and log output.

`wt merge` hook order:

```text
pre-commit -> post-commit -> pre-merge -> pre-remove -> post-remove + post-merge
```

## Hook Forms

Single command:

```toml
pre-start = "npm install"
```

Concurrent commands:

```toml
[post-start]
server = "npm run dev"
watch = "npm run watch"
```

Pipeline:

```toml
[[post-start]]
install = "npm ci"

[[post-start]]
build = "npm run build"
server = "npm run dev"
```

Use pipelines only when later steps depend on earlier steps.

## Template Variables

| Group | Variables |
| --- | --- |
| active | `branch`, `worktree_path`, `worktree_name`, `commit`, `short_commit`, `upstream` |
| operation | `base`, `base_worktree_path`, `target`, `target_worktree_path`, `pr_number`, `pr_url` |
| repo | `repo`, `repo_path`, `owner`, `primary_worktree_path`, `default_branch`, `remote`, `remote_url` |
| exec | `cwd`, `hook_type`, `hook_name`, `args` |
| state | `vars.<key>` |

Bare variables refer to the branch the operation acts on. `base` and `target` provide the other side.

Use conditionals/defaults for optional values:

```toml
[pre-start]
sync = "{% if upstream %}git fetch && git rebase {{ upstream }}{% endif %}"

[post-start]
dev = "ENV={{ vars.env | default('development') }} npm start -- --port {{ vars.port | default('3000') }}"
```

Run with `-v` to see template variables.

## Filters and Functions

| Filter | Use |
| --- | --- |
| `sanitize` | Filesystem-safe branch name |
| `sanitize_db` | Database-safe identifier |
| `sanitize_hash` | Filesystem-safe plus collision-avoidance hash |
| `hash` | 3-character digest |
| `hash_port` | Deterministic port 10000-19999 |
| `dirname`, `basename` | Path manipulation |
| `codename(n)` | Friendly stable words |

Function:

```toml
[pre-start]
setup = "cp {{ worktree_path_of_branch('main') }}/config.local {{ worktree_path }}"
```

Do not quote template variables just for safety; Worktrunk shell-escapes rendered values.

## Approvals

Project hooks and aliases require approval on first run. User hooks and user aliases do not.

```bash
wt config approvals add
wt config approvals clear
wt config approvals clear --global
```

Commands must be re-approved if the template changes or the project moves. Use `--yes` for CI/noninteractive runs.

## State

```bash
wt config state default-branch
wt config state default-branch set main
wt config state default-branch clear
wt config state marker set "WIP"
wt config state vars set env=staging
wt config state vars set config='{"port": 3000}'
wt config state cache clear
wt config state logs --format=json
wt config state clear
```

State is stored in `.git/`, not tracked by Git. `state clear` removes Worktrunk repo state and caches, not config files.

## Environment Overrides

Config keys use kebab-case; env vars use `WORKTRUNK_` and double underscores for nested sections:

| Config | Env |
| --- | --- |
| `worktree-path` | `WORKTRUNK_WORKTREE_PATH` |
| `commit.generation.command` | `WORKTRUNK_COMMIT__GENERATION__COMMAND` |
| `commit.stage` | `WORKTRUNK_COMMIT__STAGE` |

Useful variables: `WORKTRUNK_BIN`, `WORKTRUNK_CONFIG_PATH`, `WORKTRUNK_PROJECT_CONFIG_PATH`, `WORKTRUNK_SYSTEM_CONFIG_PATH`, `WORKTRUNK_MAX_CONCURRENT_COMMANDS`, `NO_COLOR`, `CLICOLOR_FORCE`.
