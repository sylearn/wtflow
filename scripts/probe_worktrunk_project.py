#!/usr/bin/env python3
"""Probe a repository for Worktrunk workflow design.

Outputs JSON with repo, Worktrunk, package-manager, and suggested hook data.
No third-party dependencies.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def run(cmd: list[str], cwd: Path, timeout: float = 5.0) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "ok": proc.returncode == 0,
            "code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except FileNotFoundError:
        return {"ok": False, "code": None, "stdout": "", "stderr": "command not found"}
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "code": None,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": f"timeout after {timeout}s",
        }


def read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def which_many(names: list[str]) -> dict[str, str | None]:
    return {name: shutil.which(name) for name in names}


def detect_package_manager(root: Path) -> str | None:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "package-lock.json").exists():
        return "npm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        return "bun"
    if (root / "package.json").exists():
        return "npm"
    return None


def node_install_command(pm: str | None) -> str | None:
    if pm == "pnpm":
        return "pnpm install"
    if pm == "npm":
        return "npm ci"  # use npm install if no lockfile
    if pm == "yarn":
        return "yarn install --frozen-lockfile"
    if pm == "bun":
        return "bun install --frozen-lockfile"
    return None


def node_run(pm: str, script: str) -> str:
    if pm == "npm":
        return f"npm run {script}"
    return f"{pm} run {script}"


def detect_node(root: Path) -> dict[str, Any]:
    pkg = read_json(root / "package.json")
    if not isinstance(pkg, dict):
        return {"present": False}
    scripts = pkg.get("scripts") if isinstance(pkg.get("scripts"), dict) else {}
    pm = detect_package_manager(root)
    hooks: list[dict[str, str]] = []
    install = node_install_command(pm)
    if install:
        if pm == "npm" and not (root / "package-lock.json").exists():
            install = "npm install"
        hooks.append({"hook": "pre-start", "name": "deps", "command": install})
    if pm and "dev" in scripts:
        hooks.append({
            "hook": "post-start",
            "name": "server",
            "command": f"wt step tether -- {node_run(pm, 'dev')} -- --port {{{{ branch | hash_port }}}}",
        })
    for script in ("lint", "typecheck", "format:check"):
        if pm and script in scripts:
            hooks.append({"hook": "pre-commit", "name": script.replace(":", "-"), "command": node_run(pm, script)})
    for script in ("test", "build"):
        if pm and script in scripts:
            hooks.append({"hook": "pre-merge", "name": script, "command": node_run(pm, script)})
    return {"present": True, "package_manager": pm, "scripts": scripts, "suggested_hooks": hooks}


def detect_rust(root: Path) -> dict[str, Any]:
    if not (root / "Cargo.toml").exists():
        return {"present": False}
    hooks = [
        {"hook": "post-start", "name": "copy", "command": "wt step copy-ignored"},
        {"hook": "pre-commit", "name": "fmt", "command": "cargo fmt --check"},
        {"hook": "pre-commit", "name": "clippy", "command": "cargo clippy -- -D warnings"},
        {"hook": "pre-merge", "name": "test", "command": "cargo test"},
    ]
    return {"present": True, "suggested_hooks": hooks}


def detect_python(root: Path) -> dict[str, Any]:
    present = any((root / name).exists() for name in ("pyproject.toml", "requirements.txt", "uv.lock", "poetry.lock"))
    if not present:
        return {"present": False}
    hooks: list[dict[str, str]] = []
    if (root / "uv.lock").exists() or (root / "pyproject.toml").exists():
        hooks.append({"hook": "pre-start", "name": "sync", "command": "uv sync"})
    elif (root / "requirements.txt").exists():
        hooks.append({"hook": "pre-start", "name": "deps", "command": "python -m pip install -r requirements.txt"})
    if (root / "pyproject.toml").exists():
        hooks.extend([
            {"hook": "pre-commit", "name": "ruff", "command": "ruff check ."},
            {"hook": "pre-commit", "name": "format", "command": "ruff format --check ."},
            {"hook": "pre-merge", "name": "test", "command": "pytest"},
        ])
    return {"present": True, "suggested_hooks": hooks}


def main() -> int:
    cwd = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path.cwd()
    git_root_result = run(["git", "rev-parse", "--show-toplevel"], cwd)
    root = Path(git_root_result["stdout"]).resolve() if git_root_result["ok"] else cwd

    git = {
        "is_repo": git_root_result["ok"],
        "root": str(root) if git_root_result["ok"] else None,
        "branch": run(["git", "branch", "--show-current"], root)["stdout"] if git_root_result["ok"] else None,
        "remotes": run(["git", "remote", "-v"], root)["stdout"].splitlines() if git_root_result["ok"] else [],
        "status_short": run(["git", "status", "--short"], root, timeout=10)["stdout"] if git_root_result["ok"] else None,
    }

    wt_path = shutil.which("wt") or shutil.which("git-wt")
    wt = {"available": bool(wt_path), "path": wt_path, "version": None, "config_show_ok": False}
    if wt_path:
        version = run([wt_path, "--version"], root)
        wt["version"] = version["stdout"] or version["stderr"]
        config_show = run([wt_path, "config", "show"], root, timeout=10)
        wt["config_show_ok"] = config_show["ok"]
        wt["config_show_preview"] = "\n".join((config_show["stdout"] or config_show["stderr"]).splitlines()[:40])

    node = detect_node(root)
    rust = detect_rust(root)
    python = detect_python(root)
    suggested_hooks = []
    for section in (node, rust, python):
        suggested_hooks.extend(section.get("suggested_hooks", []))

    files = {
        "project_config": str(root / ".config" / "wt.toml") if (root / ".config" / "wt.toml").exists() else None,
        "worktreeinclude": str(root / ".worktreeinclude") if (root / ".worktreeinclude").exists() else None,
        "package_json": (root / "package.json").exists(),
        "cargo_toml": (root / "Cargo.toml").exists(),
        "pyproject_toml": (root / "pyproject.toml").exists(),
        "taskfile": any((root / name).exists() for name in ("Taskfile.yml", "Taskfile.yaml")),
        "justfile": any((root / name).exists() for name in ("Justfile", "justfile")),
        "makefile": any((root / name).exists() for name in ("Makefile", "makefile")),
    }

    result = {
        "cwd": str(cwd),
        "git": git,
        "worktrunk": wt,
        "tools": which_many(["git", "wt", "git-wt", "gh", "glab", "jq", "tmux", "zellij", "docker", "caddy", "claude", "codex", "opencode", "gemini", "uv", "ruff", "pytest"]),
        "files": files,
        "node": node,
        "rust": rust,
        "python": python,
        "suggested_hooks": suggested_hooks,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
