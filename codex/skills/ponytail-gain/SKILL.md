---
name: ponytail-gain
description: >
  Show ponytail's measured impact as a compact scoreboard: less code, less
  cost, more speed, from the benchmark medians. One-shot display, not a
  persistent mode, and not a per-repo number. Trigger: /ponytail-gain,
  "ponytail gain", "what does ponytail save", "show ponytail impact",
  "ponytail scoreboard".
license: MIT
upstream: https://github.com/dietrichgebert/ponytail
upstream-commit: e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156
---

# Ponytail Gain

Display this scoreboard when invoked. One-shot: do NOT change mode, write flag
files, or persist anything.

The figures are the published benchmark medians (5 everyday tasks: email
validator, debounce, CSV sum, countdown timer, rate limiter; three models:
Haiku, Sonnet, Opus). They are measured, not computed from the current repo.
Source: `benchmarks/` and the README.

## Scoreboard

Render plain ASCII bars. The bar length shows the measured range; the label
carries the exact figure:

```
  ponytail gain                     benchmark median · 5 tasks · 3 models

  Lines of code   no-skill  ████████████████████  100%
                  ponytail  ██▌·················    6–20%   ▼ 80–94%
  Cost            no-skill  ████████████████████  100%
                  ponytail  █████▌··············   23–53%  ▼ 47–77%
  Speed           ponytail  ▸ 3–6× faster

  This repo:  /ponytail-debt  (shortcuts you deferred)
              /ponytail-audit (what's still cuttable)
```

## Honesty boundary

These are benchmark medians, not this repo. NEVER print a per-repo savings
number ("you saved X lines/tokens here"): the unbuilt version was never
written, so there is no real baseline to subtract from in a live repo. The
only real per-repo figures come from `/ponytail-debt` (a counted ledger), and
this card points there instead of inventing one.

## Boundaries

One-shot display. Edits nothing, changes no mode.
"stop ponytail" or "normal mode": revert.

## Codex notes

Vendored verbatim from [ponytail](https://github.com/dietrichgebert/ponytail) (MIT, (c) 2026 DietrichGebert) at commit
`e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156`. Only the frontmatter was adapted for Codex plus this notes section —
the rule text above is unmodified, so behaviour matches what was measured upstream.

- **Trigger:** reference it by name in your prompt (`$ponytail-gain`), or let it fire from
  the description. It is installed to `.agents/skills/` (user scope:
  `~/.agents/skills/`).
- **No slash commands:** the upstream `/ponytail*` commands are Claude Code plugin
  commands, which do not exist in Codex. Ask in words instead.
- **Never a reason to skip gates:** the rule trades less code for more thinking,
  not for skipped tests. The Tapway pipeline still governs whether work is done.
