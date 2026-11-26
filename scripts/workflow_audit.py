#!/usr/bin/env python3
"""Server-side PR audit: no secrets, conventional commits, and a plan.

Runs inside the PR's checkout with full history. Reads GITHUB_EVENT_PATH.

A PR has a plan when it adds or updates a file in docs/plans/, or its
description carries a `Plan: docs/plans/<name>.md` line naming a plan that is
already on the target branch. Routine PRs need neither plan nor commit check;
the secret scan always runs.
"""
import json
import os
import re
import subprocess
import sys

PRODUCTION = ("master", "main", "prod")
CONVENTIONAL = re.compile(
    r"^(feat|fix|chore|docs|refactor|test|build|ci|perf|style|revert|wip)(\([^)]*\))?!?(:| )", re.I
)
SECRET = re.compile(
    r"AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{36}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"
)
PLAN_PATH = r"docs/plans/[\w./-]+\.md"
PLAN_LINE = re.compile(rf"^[ \t>*_-]*Plan[*_]*:[*_]*[^\n]*?({PLAN_PATH})", re.I | re.M)


def git(*args):
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, encoding="utf-8", errors="replace"
    ).stdout


def exists_on(ref, path):
    return subprocess.run(["git", "cat-file", "-e", f"{ref}:{path}"], capture_output=True).returncode == 0


def routine(pr, repository):
    """Why this PR needs no plan, or None. Forks never qualify."""
    head, base = pr["head"]["ref"], pr["base"]["ref"]
    user = pr["user"]["login"]
    if (pr["head"].get("repo") or {}).get("full_name") != repository:
        return None
    if head == "staging" and base in PRODUCTION:
        return "promotion"
    if head in PRODUCTION and base == "staging":
        return "sync back to staging"
    if head.startswith("chore/manifest-sync-") and user == "github-actions[bot]":
        return "release version sync"
    if user == "dependabot[bot]":
        return "dependency update"
    return None


def has_secret(base):
    diff = git("diff", f"{base}...HEAD", "--unified=0", "--", ".", ":!*.lock", ":!*.md")
    return any(
        line.startswith("+") and not line.startswith("+++") and SECRET.search(line)
        for line in diff.splitlines()
    )


def plan_error(base, branch, body):
    changed = git("diff", f"{base}...HEAD", "--name-status", "--diff-filter=ACMR").splitlines()
    if any(re.fullmatch(PLAN_PATH, line.split("\t")[-1]) for line in changed):
        return None
    linked = PLAN_LINE.findall(re.sub(r"<!--.*?-->", "", body, flags=re.S))
    if any(exists_on(base, path) for path in linked):
        return None
    if linked:
        return f"linked plan {linked[0]} is not on {branch}. Merge the plan first, or add it to this PR."
    return (
        "no plan. Add or update a file in docs/plans/, or put "
        "'Plan: docs/plans/<name>.md' in the PR description for a plan already merged."
    )


def main():
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as handle:
        event = json.load(handle)
    pr = event["pull_request"]
    branch = pr["base"]["ref"]
    base = f"origin/{branch}"
    errors = []

    if has_secret(base):
        errors.append("secret detected in an added line. Remove it, and rotate it if it was real.")

    reason = routine(pr, event["repository"]["full_name"])
    if reason:
        print(f"Routine PR ({reason}): plan and commit checks skipped.")
    else:
        subjects = git("log", f"{base}..HEAD", "--no-merges", "--format=%s").splitlines()
        bad = [s for s in subjects if not CONVENTIONAL.match(s)]
        if bad:
            errors.append("non-conventional commit(s): " + "; ".join(bad[:5]))
        missing = plan_error(base, branch, pr.get("body") or "")
        if missing:
            errors.append(missing)
        if not git("diff", f"{base}...HEAD", "--name-only", "--", "docs/").strip():
            print("::warning::no docs/ file changed. Update affected docs if behaviour changed.")

    for error in errors:
        print(f"::error::{error}")
    if not errors:
        print("Workflow audit passed.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
