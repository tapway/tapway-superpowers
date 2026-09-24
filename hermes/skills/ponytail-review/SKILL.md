---
name: ponytail-review
description: >
  Code review focused exclusively on over-engineering. Finds what to delete:
  reinvented standard library, unneeded dependencies, speculative abstractions,
  dead flexibility. One line per finding: location, what to cut, what replaces
  it. Use when the user says "review for over-engineering", "what can we
  delete", "is this over-engineered", "simplify review", or invokes
  /ponytail-review. Complements correctness-focused review, this one only
  hunts complexity.
license: MIT
version: 1.0.0
author: Tapway (ported to Hermes by limcheehow)
platforms: [linux, macos, windows]
upstream: https://github.com/dietrichgebert/ponytail
upstream-commit: e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156
metadata:
  hermes:
    tags: ["ponytail", "review", "over-engineering", "simplification"]
    related_skills: [ponytail, ponytail-audit, ponytail-debt, ponytail-gain, ponytail-help]
---

Review diffs for unnecessary complexity. One line per finding: location, what
to cut, what replaces it. The diff's best outcome is getting shorter.

## Format

`L<line>: <tag> <what>. <replacement>.`, or `<file>:L<line>: ...` for
multi-file diffs.

Tags:

- `delete:` dead code, unused flexibility, speculative feature. Replacement: nothing.
- `stdlib:` hand-rolled thing the standard library ships. Name the function.
- `native:` dependency or code doing what the platform already does. Name the feature.
- `yagni:` abstraction with one implementation, config nobody sets, layer with one caller.
- `shrink:` same logic, fewer lines. Show the shorter form.

## Examples

❌ "This EmailValidator class might be more complex than necessary, have you
considered whether all these validation rules are needed at this stage?"

✅ `L12-38: stdlib: 27-line validator class. "@" in email, 1 line, real validation is the confirmation mail.`

✅ `L4: native: moment.js imported for one format call. Intl.DateTimeFormat, 0 deps.`

✅ `repo.py:L88: yagni: AbstractRepository with one implementation. Inline it until a second one exists.`

✅ `L52-71: delete: retry wrapper around an idempotent local call. Nothing replaces it.`

✅ `L30-44: shrink: manual loop builds dict. dict(zip(keys, values)), 1 line.`

## Scoring

End with the only metric that matters: `net: -<N> lines possible.`

If there is nothing to cut, say `Lean already. Ship.` and stop.

## Boundaries

Scope: over-engineering and complexity only. Correctness bugs, security holes,
and performance are explicitly out of scope. Route them to a normal review
pass, not this one. A single smoke test or `assert`-based
self-check is the ponytail minimum, not bloat, never flag it for deletion.
Does not apply the fixes, only lists them.
"stop ponytail-review" or "normal mode": revert to verbose review style.

## Hermes port notes

Vendored verbatim from [ponytail](https://github.com/dietrichgebert/ponytail) (MIT, (c) 2026 DietrichGebert) at commit
`e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156`. Only the frontmatter was adapted for Hermes plus this notes section —
the rule text above is unmodified, so behaviour matches what was measured upstream.

- **Auto-triggering:** Hermes surfaces skills by description match, so this rule
  applies to coding tasks without being invoked. To pin it for a whole session,
  preload it explicitly: `hermes -s ponytail-review ...` (Hermes Agent: `--skills ponytail-review`).
- **No slash commands:** the upstream `/ponytail*` commands are Claude Code
  plugin commands. In Hermes, ask for the same thing in words ("review this diff
  for over-engineering") or preload the sibling skill explicitly.
- **Never a reason to skip gates:** the rule trades less code for more thinking,
  not for skipped tests. The Tapway pipeline (tdd, quality-gates, verification)
  still governs whether work is done.
