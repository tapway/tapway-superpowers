# Phase 3 — Enforceable Hooks: Progress + Dependency Gates

**Date:** 2026-08-09
**Status:** Approved
**Release target:** v1.5.0

---

## 1. Problem

The tapway-superpowers hooks (pre-bash-safety, pre-commit-secrets, post-write-lint,
session-start, post-commit-release-note) **never worked**. Three confirmed root causes:

1. **`.claude-plugin/plugin.json` declares `"hooks": []`** — the plugin manifest never
   wires `hooks/hooks.json`, so no hook registers at install time.
2. **`exit 1` instead of `exit 2`** for PreToolUse blocking — Claude Code treats exit 1 as
   a *non-blocking error* and proceeds. Only exit 2 blocks. (Official docs: "Only exit
   code 2 blocks the action.")
3. **Hermes port has zero enforcement** — it ships skill files only. Hermes enforcement uses
   a different mechanism entirely (shell hooks in `config.yaml` with a JSON wire protocol,
   or Python plugin `pre_tool_call` hooks). None exists in the repo.

## 2. Goals

- **Repair** the existing hooks so they actually block (wire manifest + exit 2).
- **Add Gate 1 — progress quality gate**: lint + format + typecheck + coverage at commit
  time, blocking on failure.
- **Add Gate 2 — dependency audit**: supply-chain vulnerability scan (osv-scanner / npm
  audit / pip-audit), blocking.
- **Per-platform enforcement**: Claude Code PreToolUse hooks + git pre-commit backstop;
  Hermes shell hooks + skill gates.

## 3. Architecture

### Gate 1 — Progress quality gate (blocks on failure)

| Layer | Claude Code | Hermes |
|---|---|---|
| Agent-native | `PreToolUse` hook on `git commit *` → `exit 2` | Shell hook `pre_tool_call` matching `terminal` → `{"decision":"block"}` |
| Backstop | Git `pre-commit` hook (committed file, installed via setup-project) | Same git `pre-commit` hook — platform-agnostic |
| Skill gate | covered by hook | `verification` + `pr` skills: run checks before done |

### Gate 2 — Dependency audit (CI + pre-commit)

| Tool | Ecosystem |
|---|---|
| `osv-scanner` | All (19+ lockfile formats) |
| `npm audit` | JS/TS |
| `pip-audit` | Python |

Enforced at: CI quality-gate workflow (blocking) + pre-commit hook (fast local) +
`dependency-audit` skill (remediation).

## 4. Components

### Claude plugin
| File | Purpose |
|---|---|
| `.claude-plugin/plugin.json` (fix) | Wire all hooks into the manifest |
| `hooks/hooks.json` (fix) | Correct PreToolUse/PostToolUse semantics |
| `hooks/pre-commit-gate/pre-commit-gate.sh` | NEW — lint+format+typecheck+coverage, exit 2 |
| `hooks/dependency-audit/dependency-audit.sh` | NEW — osv/npm-audit/pip-audit, exit 2 on critical |
| `hooks/pre-bash-safety/pre-bash-safety.sh` (fix) | exit 1 → exit 2 |
| `hooks/pre-commit-secrets/pre-commit-secrets.sh` (fix) | exit 1 → exit 2 |
| `hooks/pre-commit/git-pre-commit.sh` | NEW — committed backstop, installed by setup-project |
| `.github/workflows/quality.yml` | Add dependency-audit step |

### Hermes port
| File | Purpose |
|---|---|
| `hermes/config.hooks.yaml` | NEW — shell-hook config (pre_tool_call blocking) |
| `hermes/skills/verification/SKILL.md` | Add commit-gate step |
| `hermes/skills/pr/SKILL.md` | Add verification-before-commit gate |
| `hermes/skills/dependency-audit/SKILL.md` | NEW — remediation skill |
| `hermes/skills/setup-project/SKILL.md` | Install git pre-commit backstop |

### TDD
- `tests/test_phase3_hooks.py` — asserts plugin.json wires hooks, exit 2 semantics,
  Hermes shell-hook config valid, skill gates present.

## 5. Scope Guardrails

- **In scope:** repair existing hooks + the two gates with per-platform enforcement.
- **Out of scope:** other Phase 4 items (a11y, perf, incident-runbook) — separate phase.
- All hooks remain **non-blocking on errors** (never crash the agent) — only the intended
  gate blocks.

## 6. Verification

- Fixed hooks actually block (failing lint → commit rejected)
- Hermes shell hooks load
- Dependency audit catches a known vulnerable package
- 3 existing TDD suites (e2e/quality/phase2) + new phase3 suite green

## 7. Release

- v1.5.0 (feat: new hooks + repair)