---
name: ponytail-audit
description: >
  Whole-repo audit for over-engineering. Like ponytail-review, but scans the
  entire codebase instead of a diff: a ranked list of what to delete, simplify,
  or replace with stdlib/native equivalents. Use when the user says "audit this
  codebase", "audit for over-engineering", "what can I delete from this repo",
  "find bloat", "ponytail-audit", or "/ponytail-audit". One-shot report, does
  not apply fixes.
license: MIT
version: 1.0.0
author: Tapway (ported to Hermes by limcheehow)
platforms: [linux, macos, windows]
upstream: https://github.com/dietrichgebert/ponytail
upstream-commit: e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156
metadata:
  hermes:
    tags: ["ponytail", "audit", "bloat", "dead-code"]
    related_skills: [ponytail, ponytail-review, ponytail-debt, ponytail-gain, ponytail-help]
---

ponytail-review, repo-wide. Scan the whole tree instead of a diff. Rank
findings biggest cut first.

## Tags

Same as ponytail-review:

- `delete:` dead code, unused flexibility, speculative feature. Replacement: nothing.
- `stdlib:` hand-rolled thing the standard library ships. Name the function.
- `native:` dependency or code doing what the platform already does. Name the feature.
- `yagni:` abstraction with one implementation, config nobody sets, layer with one caller.
- `shrink:` same logic, fewer lines. Show the shorter form.

## Hunt

Deps the stdlib or platform already ships, single-implementation interfaces,
factories with one product, wrappers that only delegate, files exporting one
thing, dead flags and config, hand-rolled stdlib.

## Output

One line per finding, ranked: `<tag> <what to cut>. <replacement>. [path]`.
End with `net: -<N> lines, -<M> deps possible.` Nothing to cut: `Lean already. Ship.`

## Boundaries

Scope: over-engineering and complexity only. Correctness bugs, security holes,
and performance are explicitly out of scope. Route them to a normal review
pass. Lists findings, applies nothing. One-shot.
"stop ponytail-audit" or "normal mode" to revert.

## Hermes port notes

Vendored verbatim from [ponytail](https://github.com/dietrichgebert/ponytail) (MIT, (c) 2026 DietrichGebert) at commit
`e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156`. Only the frontmatter was adapted for Hermes plus this notes section —
the rule text above is unmodified, so behaviour matches what was measured upstream.

- **Auto-triggering:** Hermes surfaces skills by description match, so this rule
  applies to coding tasks without being invoked. To pin it for a whole session,
  preload it explicitly: `hermes -s ponytail-audit ...` (Hermes Agent: `--skills ponytail-audit`).
- **No slash commands:** the upstream `/ponytail*` commands are Claude Code
  plugin commands. In Hermes, ask for the same thing in words ("review this diff
  for over-engineering") or preload the sibling skill explicitly.
- **Never a reason to skip gates:** the rule trades less code for more thinking,
  not for skipped tests. The Tapway pipeline (tdd, quality-gates, verification)
  still governs whether work is done.
