#!/usr/bin/env python3
"""
Wiki-vs-repo doc routing step validation suite (TDD).

RED:  Run before implementation — these assertions fail.
GREEN: Run after implementation — all assertions pass.

The tapway-superpowers pipeline routes each document a plan produces to either
the shared wiki/brain or the repo's own docs. That decision is a step in the
writing-plans skill (after the plan, alongside the GitHub-issue step), and it
must gracefully handle users who DON'T use CodeMAX and users with read-only
access — neither should ever block the pipeline.

Assertions:
  [1] 7b (GitHub issue, after plan) present in BOTH writing-plans copies.
  [2] Wiki-vs-repo routing step present in BOTH writing-plans copies.
  [3] No-CodeMAX guard: routing step is skippable (CODEMAX_ENABLED) and falls
      back to repo-docs only — never blocks, never errors.
  [4] Read-only guard: routing proceeds or records without write; pipeline
      continues to the next step regardless.
  [5] codemax-gbrain (both copies) tells the agent to route before sync.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PASS: list[str] = []
FAIL: list[str] = []


def check(cond: bool, label: str) -> None:
    if cond:
        PASS.append(label)
        print(f"  PASS  {label}")
    else:
        FAIL.append(label)
        print(f"  FAIL  {label}")


def read(*rel: str) -> str | None:
    p = os.path.join(ROOT, *rel)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return f.read()


def main() -> int:
    print("=" * 68)
    print("WIKI-VS-REPO ROUTING STEP — VALIDATION SUITE")
    print("=" * 68)

    wp = {
        "claude": read("skills", "writing-plans", "SKILL.md"),
        "hermes": read("hermes", "skills", "writing-plans", "SKILL.md"),
    }
    cg = {
        "claude": read("skills", "codemax-gbrain", "SKILL.md"),
        "hermes": read("hermes", "skills", "codemax-gbrain", "SKILL.md"),
    }

    # --- [1] 7b GitHub-issue step present in BOTH copies ---------------------
    print("\n[1] writing-plans: 7b GitHub-issue step (after plan) in both copies")
    for which, txt in wp.items():
        check(txt is not None, f"writing-plans {which} exists")
        if txt:
            check("7b" in txt and "GitHub issue" in txt,
                  f"writing-plans {which} has 7b GitHub-issue step")
            check("after" in txt and ("before execution" in txt or "before executing" in txt),
                  f"writing-plans {which} 7b is timed after plan, before execution")

    # --- [2] wiki-vs-repo routing step in BOTH copies ------------------------
    print("\n[2] writing-plans: wiki-vs-repo routing step in both copies")
    ROUTING = ("wiki" in (wp["claude"] or "") and "repo" in (wp["claude"] or "")) \
        if wp["claude"] else False
    for which, txt in wp.items():
        check(txt is not None and "wiki" in txt and "repo" in txt.lower(),
              f"writing-plans {which} mentions wiki + repo routing")
        check(txt is not None and ("route" in txt.lower() or "where should this document live" in txt),
              f"writing-plans {which} has a routing step heading")

    # --- [3] No-CodeMAX guard (skip / repo-docs only, never blocks) ----------
    print("\n[3] No-CodeMAX guard: skippable + repo-docs fallback, never blocks")
    for which, txt in wp.items():
        if not txt:
            continue
        check("CODEMAX_ENABLED" in txt or "CODEMAX" in txt,
              f"{which}: routing step gated on CodeMAX (skippable)")
        check("repo docs" in txt.lower() or "repo-docs" in txt.lower(),
              f"{which}: repo-docs is a valid fallback for non-CodeMAX users")
        check("skip" in txt.lower() or "no CodeMAX" in txt.lower() or "not use CodeMAX" in txt.lower(),
              f"{which}: non-CodeMAX users skip the wiki step entirely")

    # --- [4] Read-only guard (never blocks the pipeline) ---------------------
    print("\n[4] Read-only guard: routing continues without write access")
    for which, txt in wp.items():
        if not txt:
            continue
        check("read-only" in txt.lower() or "read only" in txt.lower(),
              f"{which}: handles read-only wiki access")
        val = txt.lower()
        check("continue" in val or "proceed" in val or "never block" in val or "next step" in val,
              f"{which}: read-only never blocks, pipeline continues")

    # --- [5] codemax-gbrain routes before sync -------------------------------
    print("\n[5] codemax-gbrain: route before sync (both copies)")
    for which, txt in cg.items():
        if not txt:
            continue
        check("push" in txt.lower() and ("route" in txt.lower() or "wiki" in txt.lower()),
              f"codemax-gbrain {which}: push step references wiki-vs-repo routing")
        check("sync" in txt.lower(),
              f"codemax-gbrain {which}: references gbrain sync")

    print("\n" + "=" * 68)
    print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
    print("=" * 68)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
