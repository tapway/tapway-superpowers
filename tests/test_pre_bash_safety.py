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
        r = subprocess.run(["bash", str(hook)], input="not json", text=True, capture_output=True, cwd=repo)
        check(r.returncode == 0, f"{name}: unreadable payload is ignored (tool-guard fails closed on it)")

claude_text = HOOKS["claude"].read_text()
check('COMMAND="$1"' not in claude_text, "claude hook no longer assigns COMMAND from $1")
check("hook_payload.sh" in claude_text, "claude hook uses the shared payload adapter")
rules = lambda p: p.read_text()[p.read_text().index("# The rules below"):]  # noqa: E731
check(rules(HOOKS["claude"]) == rules(HOOKS["codex"]), "Claude and Codex copies carry identical rules")

print("\n" + "=" * 68)
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
print("=" * 68)
sys.exit(1 if FAIL else 0)
