# Codex Port Work Package Checklist

**Assignee:** CH Lim
**Plan:** [docs/plans/2026-08-14-codex-port.md](../plans/2026-08-14-codex-port.md)
**Brainstorm:** [docs/brainstorming/codex-port.md](../brainstorming/codex-port.md)

## Branch 1: `feat/codex-skills-port` — Skills + $tapway umbrella

- [x] Task 1: Scaffold `codex/` directory structure (skills/, hooks/, templates/)
- [x] Task 2: Port 12 pipeline skills (normalized to Codex verbs)
- [x] Task 3: Port 12 quality/process/infra skills (+ codemax-gbrain env gate)
- [x] Task 4: Create the `$tapway` umbrella skill
- [x] Task 5: Create the `AGENTS.md` template

## Branch 2: `feat/codex-hooks-port` — Enforceable hooks

- [x] Task 6: Port 9 hook scripts (stdin-JSON adapted for Codex)
- [x] Task 7: Create `hooks.json` template (SessionStart/PreToolUse/PostToolUse)
- [x] Task 8: Installer (`install.sh` + `install.ps1`) → `.agents/skills/` + `.codex/` + `AGENTS.md`
- [x] Task 9: `codex/README.md` (command map, hook map, trust-review, plugin runbook)

## Parity test

- [x] `tests/test_codex_port.py` — 281 checks, all passing
- [x] Full suite regression check (other suites pass; `test_phase3_hooks.py` failure pre-existing on main, unrelated — touches `.claude-plugin/plugin.json` only)

## Gate

- [x] Pre-review-cleanup (no scaffolding placeholders leaked)
- [x] Self-review (bash -n on all hooks, stdin-JSON simulated, hooks.json.template valid JSON, `.git`-strip chained)
- [ ] PR opened → 🟢