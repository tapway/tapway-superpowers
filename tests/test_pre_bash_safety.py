#!/usr/bin/env python3
"""
pre-bash-safety — behavioural suite (Claude hook and Codex copy).

Drives each hook exactly the way the harness does: the tool call as JSON on
stdin, nothing in argv. The Claude hook used to read "$1", so it passed every
command; the first check below is that regression.

Run: python3 tests/test_pre_bash_safety.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS = {
    "claude": ROOT / "hooks" / "pre-bash-safety" / "pre-bash-safety.sh",
    "codex": ROOT / "codex" / "hooks" / "pre-bash-safety.sh",
}

PASS: list[str] = []
FAIL: list[str] = []


def check(cond: bool, label: str) -> None:
    (PASS if cond else FAIL).append(label)
    print(f"  {'PASS' if cond else 'FAIL'}  {label}")


def run(hook: Path, command: str, cwd: Path, env: dict | None = None) -> int:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    full_env = {k: v for k, v in os.environ.items() if k != "ALLOW_PROD"}
    full_env.update(env or {})
    r = subprocess.run(["bash", str(hook)], input=payload, text=True,
                       capture_output=True, cwd=cwd, env=full_env, timeout=30)
    return r.returncode


BLOCK_ANYWHERE = [
    "git push --force origin feat/x",
    "git push -f origin feat/x",
    "git push -uf origin feat/x",
    "git push --force-with-lease origin feat/x",
    "git push origin feat/x --force",
    "DATABASE_URL=postgres://u@prod-db:5432/app alembic upgrade head",
    "DATABASE_URL=$PROD_DATABASE_URL psql",
    "DATABASE_URL=\"$PROD_URL\" alembic upgrade head",
    "docker compose -f docker-compose.prod.yml up -d",
    "docker-compose --env-file production.env up",
    "./deploy.sh --production",
    "git -C . push --force",
    "git push origin +feat/x",
    "git push origin feat/x \\\n  --force",
    "git push origin feat/x\\\n--force-with-lease",
]
ALLOW_ON_FEATURE = [
    "git push -u origin feat/x",
    "git push origin feat/x-fix",
    "git push origin fix/flaky-test",
    "git push --follow-tags origin feat/x",
    "git push --no-verify origin feat/x",
    "git commit -m 'feat: x'",
    "git reset --hard HEAD~1",
    "DATABASE_URL=postgres://u@db:5432/products psql -c 'select 1'",
    "docker compose logs product-api",
    "docker compose run --rm reproduce-bug",
    "npm install --production",
    "npm ci --production",
    "yarn install --production",
    "ls -la",
    "",
    "git push -u origin feat/x && rm -rf dist",
    "git push && tail -f app.log",
    "git push origin feat/x && docker compose -f x.yml up -d",
    "grep -n image docker-compose.prod.yml",
    "ls docker-compose.prod.yml",
    "cat docker-compose.yml | grep -n prod",
    "docker compose -f docker-compose.prod.yml ps",
    "docker compose -f docker-compose.prod.yml logs --tail 50",
    "next build --production",
    "git log --oneline --grep commit",
]
BLOCK_ON_MAIN = [
    "git commit -m 'feat: x'",
    "git reset --hard HEAD~1",
]

print("=" * 68)
print("PRE-BASH-SAFETY — BEHAVIOURAL SUITE (stdin JSON, like the harness)")
print("=" * 68)

with tempfile.TemporaryDirectory() as tmp:
    repo = Path(tmp)
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-q", "--allow-empty", "-m", "init"], check=True)
    subprocess.run(["git", "-C", str(repo), "switch", "-q", "-c", "feat/x"], check=True)

    for name, hook in HOOKS.items():
        print(f"\n[{name}] {hook.relative_to(ROOT)}")
        check("$1" not in hook.read_text().split("\n", 10)[-1] or name == "codex",
              f"{name}: does not read the command from $1")
        check(run(hook, "git push --force origin feat/x", repo) == 2,
              f"{name}: regression — a force-push sent as stdin JSON is blocked")
        for cmd in BLOCK_ANYWHERE:
            check(run(hook, cmd, repo) == 2, f"{name}: blocks {cmd!r}")
        for cmd in ALLOW_ON_FEATURE:
            check(run(hook, cmd, repo) == 0, f"{name}: allows {cmd!r} on a feature branch")
        subprocess.run(["git", "-C", str(repo), "switch", "-q", "main"], check=True)
        for cmd in BLOCK_ON_MAIN:
            check(run(hook, cmd, repo) == 2, f"{name}: blocks {cmd!r} on main")
        subprocess.run(["git", "-C", str(repo), "switch", "-q", "feat/x"], check=True)
        check(run(hook, "docker compose -f docker-compose.prod.yml up -d", repo, {"ALLOW_PROD": "1"}) == 0,
              f"{name}: ALLOW_PROD=1 lets a deliberate prod command through")
        for bad in ["not json", "[]", '{"tool_input": null}', '{"tool_input": "git push -f"}',
                    '{"tool_input": {"command": 3}}']:
            r = subprocess.run(["bash", str(hook)], input=bad, text=True, capture_output=True, cwd=repo)
            check(r.returncode == 2 and "refusing to guess" in r.stderr,
                  f"{name}: unreadable payload {bad!r} blocks (fails closed, no silent exit 0)")
        r = subprocess.run(["bash", str(hook)], input="", text=True, capture_output=True, cwd=repo)
        check(r.returncode == 0, f"{name}: an empty stdin (no tool call) passes")
        r = subprocess.run(["/bin/bash", str(hook)], input='{"tool_input": {"command": "ls"}}',
                           text=True, capture_output=True, cwd=repo, env={"PATH": "/nonexistent"})
        check(r.returncode == 2 and "python3 is required" in r.stderr, f"{name}: no python3 blocks")
        # Worktree regression: the harness starts the hook in the main checkout
        # (on main) while the command runs in a worktree on a feature branch.
        wt = repo.parent / (repo.name + "-wt-" + name)
        if not wt.exists():
            subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", "-b",
                            "feat/wt-" + name, str(wt)], check=True)
        subprocess.run(["git", "-C", str(repo), "switch", "-q", "main"], check=True)

        def run_cwd(command: str, payload_cwd: str | None, style: str = "claude") -> int:
            if style == "hermes":
                # Hermes: {tool_name, args: {command, workdir}}
                args = {"command": command}
                if payload_cwd is not None:
                    args["workdir"] = payload_cwd
                body = {"tool_name": "Bash", "args": args}
            else:
                body = {"tool_name": "Bash", "tool_input": {"command": command}}
                if payload_cwd is not None:
                    body["cwd"] = payload_cwd
            return subprocess.run(["bash", str(hook)], input=json.dumps(body), text=True,
                                  capture_output=True, cwd=repo).returncode

        wt_s, repo_s = wt.as_posix(), repo.as_posix()
        check(run_cwd("git commit -m x", wt_s) == 0,
              f"{name}: commit allowed when payload cwd is a worktree on a feature branch")
        check(run_cwd("git reset --hard HEAD~1", wt_s) == 0,
              f"{name}: hard reset allowed when payload cwd is a worktree on a feature branch")
        check(run_cwd(f"cd {wt_s} && git commit -m x", None) == 0,
              f"{name}: commit allowed after `cd <worktree> &&`")
        check(run_cwd(f"git -C {wt_s} commit -m x", None) == 0,
              f"{name}: commit allowed with `git -C <worktree>`")
        check(run_cwd("git commit -m x", repo_s) == 2,
              f"{name}: commit still blocked when payload cwd is on main")
        check(run_cwd(f"cd {repo_s} && git commit -m x", wt_s) == 2,
              f"{name}: commit blocked after `cd` from a worktree into a main checkout")
        check(run_cwd(f"git -C {repo_s} commit -m x", wt_s) == 2,
              f"{name}: commit blocked with `git -C <main checkout>` from a worktree")
        check(run_cwd(f"(cd {wt_s} && git commit -m x)", None) == 0,
              f"{name}: commit allowed inside a subshell `(cd <worktree> && ...)`")
        check(run_cwd(f"git -C {repo_s} reset --hard HEAD~1", wt_s) == 2,
              f"{name}: hard reset blocked with `git -C <main checkout>` from a worktree")
        check(run_cwd("git commit -m x", wt_s, style="hermes") == 0,
              f"{name}: commit allowed when the Hermes payload carries args.workdir")
        check(run_cwd("git commit -m x", None) == 2,
              f"{name}: no payload cwd falls back to the hook's own directory (main)")
        subprocess.run(["git", "-C", str(repo), "switch", "-q", "feat/x"], check=True)

        flat = '{"command": "git push --force origin feat/x"}'
        check(subprocess.run(["bash", str(hook)], input=flat, text=True, capture_output=True,
                             cwd=repo).returncode == 2, f"{name}: a flat (Codex-style) payload is read too")

claude_text = HOOKS["claude"].read_text()
check('COMMAND="$1"' not in claude_text, "claude hook no longer assigns COMMAND from $1")
check("hook_payload.sh\"" not in claude_text and ". \"$(dirname" not in claude_text,
      "claude hook parses the payload itself (the adapter maps garbage to an empty call)")
header = lambda p: p.read_text()[p.read_text().index("SEGMENTS_PY="):p.read_text().index("# The rules below")]  # noqa: E731
check(header(HOOKS["claude"]) == header(HOOKS["codex"]), "Claude and Codex copies read the payload the same way")
rules = lambda p: p.read_text()[p.read_text().index("# The rules below"):]  # noqa: E731
check(rules(HOOKS["claude"]) == rules(HOOKS["codex"]), "Claude and Codex copies carry identical rules")

print("\n" + "=" * 68)
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
print("=" * 68)
sys.exit(1 if FAIL else 0)
