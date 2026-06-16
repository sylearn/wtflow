# Worktrunk Recipes

Use this for practical workflow design. Adjust commands to the repo's package manager and validated scripts.

## New Worktree Plus Agent

```bash
alias wsc='wt switch --create --execute=claude'
wsc new-feature
wsc feature -- 'Fix GH #322'
```

Direct:

```bash
wt switch --create -x claude feature-auth -- 'Implement auth flow'
wt switch --create -x codex feature-tests -- 'Write API tests'
```

## Dev Server Per Worktree

```toml
[post-start]
server = "wt step tether -- npm run dev -- --port {{ branch | hash_port }}"

[list]
url = "http://localhost:{{ branch | hash_port }}"
```

Use `wt step tether` so the process tree is killed when the worktree is removed.

If package manager differs:

```toml
[post-start]
server = "wt step tether -- pnpm dev -- --port {{ branch | hash_port }}"
```

## Database Per Worktree

```toml
[[post-start]]
set-vars = """
wt config state vars set \
  container='{{ repo }}-{{ branch | sanitize }}-postgres' \
  port='{{ ('db-' ~ branch) | hash_port }}' \
  db_url='postgres://postgres:dev@localhost:{{ ('db-' ~ branch) | hash_port }}/{{ branch | sanitize_db }}'
"""

[[post-start]]
db = """
docker run -d --rm \
  --name {{ vars.container }} \
  -p {{ vars.port }}:5432 \
  -e POSTGRES_DB={{ branch | sanitize_db }} \
  -e POSTGRES_PASSWORD=dev \
  postgres:16
"""

[pre-remove]
db-stop = "docker stop {{ vars.container }} 2>/dev/null || true"
```

Use a different hash seed for database ports, such as `('db-' ~ branch)`, to avoid colliding with dev server ports.

## Eliminate Cold Starts

```toml
[post-start]
copy = "wt step copy-ignored"
```

If installation depends on copied files:

```toml
[[post-start]]
copy = "wt step copy-ignored"

[[post-start]]
install = "pnpm install"
```

Limit copied files:

```text
# .worktreeinclude
.env
node_modules/
target/
```

Exclude more:

```toml
[step.copy-ignored]
exclude = [".cache/", ".turbo/"]
```

Notes:

- Rust `target/` benefits strongly from reflink copying.
- Node `node_modules/` can be copied or symlinked if no native dependencies.
- Python virtualenvs often contain absolute paths; prefer `uv sync`.

## Progressive Validation

```toml
[[pre-commit]]
lint = "npm run lint"
typecheck = "npm run typecheck"

[[pre-merge]]
test = "npm test"
build = "npm run build"
```

Put fast feedback in `pre-commit`; put expensive guarantees in `pre-merge`.

## Target-Specific Post-Merge

```toml
post-merge = """
if [ {{ target }} = main ]; then
    npm run deploy:production
elif [ {{ target }} = staging ]; then
    npm run deploy:staging
fi
"""
```

`post-merge` runs in the target worktree if it exists; otherwise it runs in the primary worktree.

## Agent Handoff

tmux:

```bash
tmux new-session -d -s fix-auth-bug "wt switch --create fix-auth-bug -x claude -- \
  'Find the session timeout config and extend it to 24 hours.'"
```

zellij:

```bash
zellij run -- wt switch --create fix-auth-bug -x claude -- \
  'Find the session timeout config and extend it to 24 hours.'
```

## Tmux Session Per Worktree

```toml
[pre-start]
tmux = """
S={{ branch | sanitize }}
W={{ worktree_path }}
tmux new-session -d -s "$S" -c "$W" -n dev
tmux split-window -h -t "$S:dev" -c "$W"
tmux split-window -v -t "$S:dev.0" -c "$W"
tmux split-window -v -t "$S:dev.2" -c "$W"
tmux send-keys -t "$S:dev.1" 'npm run backend' Enter
tmux send-keys -t "$S:dev.2" 'claude' Enter
tmux send-keys -t "$S:dev.3" 'npm run frontend' Enter
tmux select-pane -t "$S:dev.0"
echo "Session '$S' - attach with: tmux attach -t $S"
"""

[pre-remove]
tmux = "tmux kill-session -t {{ branch | sanitize }} 2>/dev/null || true"
```

Attach immediately:

```bash
wt switch --create feature -x tmux -- attach -t '{{ branch | sanitize }}'
```

## Caddy Subdomain Routing

Use when cookies/CORS need hostnames like `feature.myproject.localhost`.

```toml
[post-start]
server = "wt step tether -- npm run dev -- --port {{ branch | hash_port }}"
proxy = """
  curl -sf --max-time 0.5 http://localhost:2019/config/ || caddy start
  curl -sf http://localhost:2019/config/apps/http/servers/wt || \
    curl -sfX PUT http://localhost:2019/config/apps/http/servers/wt -H 'Content-Type: application/json' \
      -d '{"listen":[":8080"],"automatic_https":{"disable":true},"routes":[]}'
  curl -sf -X DELETE http://localhost:2019/id/wt:{{ repo }}:{{ branch | sanitize }} || true
  curl -sfX PUT http://localhost:2019/config/apps/http/servers/wt/routes/0 -H 'Content-Type: application/json' \
    -d '{"@id":"wt:{{ repo }}:{{ branch | sanitize }}","match":[{"host":["{{ branch | sanitize }}.{{ repo }}.localhost"]}],"handle":[{"handler":"reverse_proxy","upstreams":[{"dial":"127.0.0.1:{{ branch | hash_port }}"}]}]}'
"""

[pre-remove]
proxy = "curl -sf -X DELETE http://localhost:2019/id/wt:{{ repo }}:{{ branch | sanitize }} || true"

[list]
url = "http://{{ branch | sanitize }}.{{ repo }}.localhost:8080"
```

## Manual Commit Messages

Use editor instead of LLM:

```toml
[commit.generation]
command = '''f=$(mktemp); printf '\n\n' > "$f"; sed 's/^/# /' >> "$f"; ${EDITOR:-vi} "$f" < /dev/tty > /dev/tty; grep -v '^#' "$f"'''
```

Or wrap as a personal alias while keeping LLM default:

```toml
[aliases]
mc = '''WORKTRUNK_COMMIT__GENERATION__COMMAND='f=$(mktemp); printf "\n\n" > "$f"; sed "s/^/# /" >> "$f"; ${EDITOR:-vi} "$f" < /dev/tty > /dev/tty; grep -v "^#" "$f"' wt merge'''
```

## Bare Repository Layout

```bash
git clone --bare <url> myproject/.git
cd myproject
wt switch main
```

Recommended project-specific user config:

```toml
[projects."github.com/myorg/myrepo"]
worktree-path = "{{ repo_path }}/../{{ branch | sanitize }}"
```

Then project config must be created from an actual worktree:

```bash
cd myproject/main
wt config create --project
```
