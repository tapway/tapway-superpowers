---
name: ponytail-debt
description: >
  Harvest every `ponytail:` comment in the codebase into a debt ledger, so the
  deliberate shortcuts and deferrals ponytail leaves behind get tracked instead
  of rotting into "later means never". Use when the user says "ponytail debt",
  "/ponytail-debt", "what did ponytail defer", "list the shortcuts", "ponytail
  ledger", or "what did we mark to do later". One-shot report, changes nothing.
license: MIT
version: 1.0.0
author: Tapway (ported to Hermes by limcheehow)
platforms: [linux, macos, windows]
upstream: https://github.com/dietrichgebert/ponytail
upstream-commit: e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156
metadata:
  hermes:
    tags: ["ponytail", "tech-debt", "deferral", "ledger"]
    related_skills: [ponytail, ponytail-review, ponytail-audit, ponytail-gain, ponytail-help]
---

Every deliberate ponytail shortcut is marked with a `ponytail:` comment naming
its ceiling and upgrade path. This collects them into one ledger so a deferral
can't quietly become permanent.

## Scan

Grep the repo for comment markers, skipping `node_modules`, `.git`, and build
output:

`grep -rnE '(#|//) ?ponytail:' .`  (add other comment prefixes if your stack uses them)

Each hit is one ledger row. The comment prefix keeps prose that merely mentions
the convention out of the ledger.

## Output

One row per marker, grouped by file:

`<file>:<line>, <what was simplified>. ceiling: <the limit named>. upgrade: <the trigger to revisit>.`

The convention is `ponytail: <ceiling>, <upgrade path>`, so pull the ceiling
and the trigger straight from the comment. Want an owner per row too? add
`git blame -L<line>,<line>`.

Flag the rot risk: any `ponytail:` comment that names no upgrade path or
trigger gets a `no-trigger` tag, those are the ones that silently rot.

End with `<N> markers, <M> with no trigger.` Nothing found: `No ponytail: debt. Clean ledger.`

## Boundaries

Reads and reports only, changes nothing. To persist it, ask and it writes the
ledger to a file (e.g. `PONYTAIL-DEBT.md`). One-shot. "stop ponytail-debt" or
"normal mode" to revert.

## Hermes port notes

Vendored verbatim from [ponytail](https://github.com/dietrichgebert/ponytail) (MIT, (c) 2026 DietrichGebert) at commit
`e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156`. Only the frontmatter was adapted for Hermes plus this notes section —
the rule text above is unmodified, so behaviour matches what was measured upstream.

- **Auto-triggering:** Hermes surfaces skills by description match, so this rule
  applies to coding tasks without being invoked. To pin it for a whole session,
  preload it explicitly: `hermes -s ponytail-debt ...` (Hermes Agent: `--skills ponytail-debt`).
- **No slash commands:** the upstream `/ponytail*` commands are Claude Code
  plugin commands. In Hermes, ask for the same thing in words ("review this diff
  for over-engineering") or preload the sibling skill explicitly.
- **Never a reason to skip gates:** the rule trades less code for more thinking,
  not for skipped tests. The Tapway pipeline (tdd, quality-gates, verification)
  still governs whether work is done.
