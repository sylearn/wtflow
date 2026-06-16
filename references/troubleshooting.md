# Worktrunk Troubleshooting

Use this when commands fail, shell integration does not change directories, hooks do not run, LLM commit messages fail, or `wt list` is slow.

## Shell Integration

Symptoms: `wt switch` prints target directory but the shell stays put, completions missing, or `wt config show` says integration is inactive.

Checks:

```bash
wt config show
type wt
```

Expected `type wt`: a shell function. If it shows a binary path, the wrapper is not loaded.

Fixes:

```bash
wt config shell install
source ~/.bashrc     # bash, adjust for shell
source ~/.zshrc      # zsh
```

Manual setup:

```bash
eval "$(wt config shell init bash)"
eval "$(wt config shell init zsh)"
wt config shell init fish | source
Invoke-Expression (& wt config shell init powershell | Out-String)
```

Common causes:

- Running `./path/to/wt` or `/usr/local/bin/wt` bypasses wrapper. Use bare `wt`.
- Running `git wt` bypasses wrapper. Use `wt`.
- Alias points to binary, e.g. `alias gwt="/usr/bin/wt"`. Change to `alias gwt="wt"`.
- Existing shell session predates installation. Restart terminal.
- IDE terminal sources different shell rc files.

For testing a dev build with shell integration:

```bash
export WORKTRUNK_BIN=./target/debug/wt
wt switch feature
```

## Hook Does Not Run

Checklist:

```bash
ls -la .config/wt.toml
wt hook show
wt hook show --expanded
wt -v hook pre-merge
```

Validate:

1. Hook type spelling is one of the ten hook names.
2. TOML parses.
3. Command works when run manually in the worktree.
4. Project commands were approved or `--yes` was used.
5. Background hook output was checked in `.git/wt/logs/`.

Move long-running blocking hooks to `post-*`:

```toml
pre-start = "npm install"
post-start = "npm run build"
```

## LLM Commit Generation Fails

Check config and installed tool:

```bash
wt config show
which claude codex opencode llm aichat jq 2>/dev/null
```

Test command directly:

```bash
echo "say hello" | <configured-command>
```

Common causes:

- CLI not installed.
- CLI not authenticated.
- API key missing.
- Model name unavailable.
- `jq` missing for Codex JSON extraction.
- TOML syntax error.
- Mutually exclusive template fields set together.

Use `wt step commit --dry-run` or `wt step squash --dry-run` to inspect rendered prompt and generated message.

## Alias Expands Same Branch In Every Worktree

Alias bodies render once at dispatch in the invoking worktree. A nested `wt step for-each` then receives baked values.

Bad:

```toml
[aliases]
show-branches = "wt step for-each -- echo {{ branch }}"
```

Good:

```toml
[aliases]
show-branches = "wt step for-each -- sh -c 'echo {% raw %}{{ branch }}{% endraw %}'"
```

Confirm with:

```bash
wt config alias dry-run show-branches
```

## `wt list` Times Out

If output names blocked tasks such as `working-tree-diff` or `working-tree-conflicts`, run Git status in that worktree:

```bash
cd <worktree>
time git --no-optional-locks status --porcelain
```

If fsmonitor daemon is wedged:

```bash
for pid in $(pgrep -f 'git fsmonitor--daemon'); do
  sock=$(lsof -p $pid 2>/dev/null | grep 'fsmonitor--daemon.ipc' | awk '{print $NF}' | head -1)
  printf "%6d  %s\n" "$pid" "$sock"
done
```

Worktrunk reaps daemons for removed worktrees during `wt remove`. A daemon serving a live worktree may need manual termination. To avoid the class of issue:

```bash
git config --global core.fsmonitor false
```

## Logs and Diagnostics

```bash
wt config state logs
wt config state logs --format=json
tail -5 .git/wt/logs/commands.jsonl | jq .
jq 'select(.exit != 0 and .exit != null)' .git/wt/logs/commands.jsonl
```

Run with `-vv` to create:

- `.git/wt/logs/trace.log`
- `.git/wt/logs/subprocess.log`
- `.git/wt/logs/diagnostic.md`

## Windows Notes

- Git for Windows is required because hooks execute through Git Bash even when the interactive shell is PowerShell.
- Windows Terminal owns `wt`; use `git-wt` unless the Windows Terminal alias is disabled.
- `wt switch` interactive picker is unavailable on Windows. Use `wt list` and `wt switch <branch>`.
- From Git Bash/MSYS2, PowerShell profile creation may be skipped. Run `wt config shell install powershell` explicitly.
