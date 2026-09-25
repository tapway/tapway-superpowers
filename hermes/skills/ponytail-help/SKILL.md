---
name: ponytail-help
description: >
  Quick-reference card for all ponytail modes, skills, and commands.
  One-shot display, not a persistent mode. Trigger: /ponytail-help,
  "ponytail help", "what ponytail commands", "how do I use ponytail".
license: MIT
version: 1.0.0
author: Tapway (ported to Hermes by limcheehow)
platforms: [linux, macos, windows]
upstream: https://github.com/dietrichgebert/ponytail
upstream-commit: e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156
metadata:
  hermes:
    tags: ["ponytail", "help", "reference"]
    related_skills: [ponytail, ponytail-review, ponytail-audit, ponytail-debt, ponytail-gain]
---

# Ponytail Help

Display this reference card when invoked. One-shot, do NOT change mode,
write flag files, or persist anything.

## Levels

| Level | Trigger | What change |
|-------|---------|-------------|
| **Lite** | `/ponytail lite` | Build what's asked, name the lazier alternative in one line. |
| **Full** | `/ponytail` | The ladder enforced: YAGNI → stdlib → native → one line → minimum. Default. |
| **Ultra** | `/ponytail ultra` | YAGNI extremist. Deletion before addition. Challenges requirements before building. |

Level sticks until changed or session end.

## Skills

| Skill | Trigger | What it does |
|-------|---------|--------------|
| **ponytail** | `/ponytail` | Lazy mode itself. Simplest solution that works. |
| **ponytail-review** | `/ponytail-review` | Over-engineering review: `L42: yagni: factory, one product. Inline.` |
| **ponytail-audit** | `/ponytail-audit` | Whole-repo over-engineering audit: ranked list of what to delete. |
| **ponytail-debt** | `/ponytail-debt` | Harvest `ponytail:` shortcut comments into a tracked ledger. |
| **ponytail-gain** | `/ponytail-gain` | Measured-impact scoreboard: less code, less cost, more speed. |
| **ponytail-help** | `/ponytail-help` | This card. |

Codex uses `@ponytail`, `@ponytail-review`, and `@ponytail-help`; Claude Code
and OpenCode use the slash-command forms above (OpenCode ships all six as
slash commands).

## Deactivate

Say "stop ponytail" or "normal mode". Resume anytime with `/ponytail`.
`/ponytail off` also works.

## Configure Default Mode

Default mode = `full`, auto-active every session. Change it:

**Environment variable** (highest priority):
```bash
export PONYTAIL_DEFAULT_MODE=ultra
```

**Config file** (`~/.config/ponytail/config.json`, Windows: `%APPDATA%\ponytail\config.json`):
```json
{ "defaultMode": "lite" }
```

Set `"off"` to disable auto-activation on session start, activate manually
with `/ponytail` when wanted.

Resolution: env var > config file > `full`.

## Update

Enable auto-update once: open `/plugin`, go to Marketplaces, pick ponytail, Enable auto-update. Claude Code then pulls new versions at startup (run `/reload-plugins` when it prompts). Manual refresh: `/plugin marketplace update ponytail` then `/reload-plugins`.

If `/plugin` is not recognized, your Claude Code is out of date. Update it (`npm install -g @anthropic-ai/claude-code@latest`, or `brew upgrade claude-code`) and restart. Other hosts use their own update flow.

## More

Full docs + examples: https://github.com/DietrichGebert/ponytail

## Hermes port notes

Vendored verbatim from [ponytail](https://github.com/dietrichgebert/ponytail) (MIT, (c) 2026 DietrichGebert) at commit
`e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156`. Only the frontmatter was adapted for Hermes plus this notes section —
the rule text above is unmodified, so behaviour matches what was measured upstream.

- **Auto-triggering:** Hermes surfaces skills by description match, so this rule
  applies to coding tasks without being invoked. To pin it for a whole session,
  preload it explicitly: `hermes -s ponytail-help ...` (Hermes Agent: `--skills ponytail-help`).
- **No slash commands:** the upstream `/ponytail*` commands are Claude Code
  plugin commands. In Hermes, ask for the same thing in words ("review this diff
  for over-engineering") or preload the sibling skill explicitly.
- **Never a reason to skip gates:** the rule trades less code for more thinking,
  not for skipped tests. The Tapway pipeline (tdd, quality-gates, verification)
  still governs whether work is done.
