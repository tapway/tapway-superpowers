# Plan: Make brainstorming Step 1.5 retrieve for real

> **Revision v2 — post doubt-cycle-1.** v1 returned 15 findings, all Actionable; each fix is
> marked `⟨F#⟩`. Record: `docs/plans/2026-09-28-doubt-cycle-1-reconciliation.md`.

Implements `docs/brainstorming/platform-grounding-retrieval.md` (Option A: retrieval on, gate OFF).
**Companion:** `docs/plans/2026-09-21-platform-grounding-g1-g6.md` (upstream feature).

## Goal

Turn Step 1.5's UNKNOWN rows into real answers **for the areas that can be grounded** — component roles,
platform ADR ids and the constitution — by wiring the existing `codemax` CLI on this host, without moving
the owner's launcher and without enabling the fail-closed gate, which the documented rollout reserves for
pilots.

## Approach

1. **Collision-managed CLI.** `⟨F2⟩` Installing the package **does** create a `codemax` console script in
   the venv's own `bin/` (`[project.scripts]`, reproduced empirically). The protection is that **the venv is never activated and its `bin/` never precedes `~/.local/bin` on PATH**; the venv's
   `bin/codemax` existing is the *expected* state, asserted as such. **Every command in this plan and in the
   skill text uses the venv's own interpreter**, `~/.hermes/venvs/codemax-cli/bin/python -m codemax.cli …`
   — the bare `python -m codemax.cli` form **fails** (`ModuleNotFoundError: No module named 'codemax'`),
   because the venv is never activated and the system interpreter has no `codemax`. `⟨F-c2⟩`
2. **Pin the ref, assert the subgroup.** `⟨F13⟩` `tapway/codemax` master moves and the `platform-context`
   group arrived only with **PR #104**. Record the resolved SHA and assert the subgroup (`--help` on the
   group exits 0) — the top-level `--help` exits 0 regardless.
3. **The benefit is bounded by the data.** `⟨F1⟩` `⟨F9⟩` Both real catalogs carry `provides: []` /
   `consumes: []` on every component, so a pack exposes **zero contracts**, and the renderer emits
   contract citation-form ids, never the literal `catalog:`. The criterion becomes "the pack compiles and
   lists component roles + ADR ids + constitution"; contracts and ownership are **not** claimed.
4. **Fix every copy a writer can serve.** `⟨F3⟩` The served copy is the **root tree**, not only
   `profiles/*`; and cron `9486afce96d1` (`codemax-skills-weekday-sync`, enabled, `0 9 * * 1-5`) reinstalls
   `brainstorming` from repo source through `hermes/install.sh`, whose `install_local` does `rm -rf` then
   `cp -a`. The three repo trees are therefore **in scope**, or the fix is reverted every weekday.
5. **Offline is tested, not asserted.** `⟨F8⟩` The build runs with the network interface down and the
   result is recorded; the two steps that genuinely need the network (the private clone; the pip install)
   are named with their fallbacks.
6. **Gate stays OFF by decision** — `TAPWAY_BRAINSTORM_GATE` unset **and** `~/.hermes/agent-hooks/`
   absent, both asserted `⟨F12⟩`.

## Files

| Path | What |
|---|---|
| `~/tapway-codemax/` | **CREATE** — clone at a **recorded SHA** `⟨F13⟩` |
| `~/.hermes/venvs/codemax-cli/` | **CREATE** — venv (expect `bin/codemax`) `⟨F2⟩` |
| `~/platform-specs-local/` | **CREATE** — clone of `tapway/platform-specs`, read-only |
| `skills/`, `hermes/skills/`, `codex/skills/` → `brainstorming/SKILL.md` | **MODIFY** (3 repo trees) — so the weekday cron distributes the fix instead of reverting it `⟨F3⟩` |
| `brainstorming/SKILL.md` × 7 installed copies | **MODIFY** — working command + corrected note `⟨F7⟩` |
| `.env` × 7 (6 profiles + `~/.hermes/.env`) | **MODIFY** — non-empty `TAPWAY_SPECS_DIR` `⟨F6⟩` `⟨F7⟩` |
| `~/.hermes/profiles/codemax/skills/software-development/hermes-flow-pipeline/SKILL.md` | **MODIFY** — wiring + gate-off decision |
| `docs/plans|checklists/2026-09-28-platform-grounding*.md` | **CREATE** |

**6 profiles + the root tree** (`~/.hermes/skills/` + `~/.hermes/profiles/{architect,builder,codemax,decider,doubter,planner}/skills/`) = the 7 skill trees

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| **A weekday cron rewinds the working checkout** | `codemax-skills-sync.sh:50` runs `git reset -q --hard origin/master` in `~/tapway-superpowers` whenever master's tip moves. **This branch is not on origin/master**, so an unpushed commit is destroyed and the tree reverts. The plan set itself and (for the grounding plan) the repo-tree edits are exposed. Owner decision required: push/merge the branch, or exclude the repo from that cron. Until then the plan set is backed up outside the repo at `~/.hermes/profiles/codemax/backups/flow-plans-<ts>/`. |
| The launcher is shadowed | Never activate the venv; never PATH its `bin/`; assert `~/.local/bin/codemax` sha256 unchanged `⟨F2⟩` |
| The weekday cron reverts the fix | Repo trees edited in the same change; a criterion re-greps after a simulated install `⟨F3⟩` |
| `hermes-agent` drift (venv 0.19.0 vs box 0.21.5+3840) | Recorded; only the `platform-context` path is exercised `⟨F14⟩` |
| The CLI needs a service | Stop condition: the build must succeed with the interface down `⟨F8⟩` |
| Writing to the shared specs repo | Read-only by policy + an assertion that no push occurred |
| `TAPWAY_SPECS_DIR` set to empty | Criterion requires non-empty and equal to the clone path `⟨F6⟩` |

## Tasks

| # | Task | Verifiable success criterion |
|---|---|---|
| 1 | Clone specs at a usable shape | `test -f ~/platform-specs-local/constitution.md` **and** `test -f ~/platform-specs-local/platforms/samurai-v2/catalog.yaml` `⟨F11⟩` |
| 2 | Clone + pin codemax | `git -C ~/tapway-codemax rev-parse HEAD` recorded in this plan as evidence `⟨F13⟩` |
| 3 | Venv + install | `~/.hermes/venvs/codemax-cli/bin/python -m codemax.cli platform-context --help` exits 0 (the **subgroup**) `⟨F13⟩` |
| 4 | Build offline | with the network down, `platform-context build` writes a pack; assert it contains ADR ids + component roles **and** that `'catalog:' in idx` is **False** `⟨F1⟩` |
| 5 | Fail-closed proof | `check` exits **0** on a grounded doc and **non-zero** on an ungrounded one — both directions executed |
| 6 | Wire the env | all **7** files hold a **non-empty** `TAPWAY_SPECS_DIR` equal to the clone path; `grep -c` = 1 each `⟨F6⟩` |
| 7 | Rewrite both commands | `grep -c 'venvs/codemax-cli/bin/python -m codemax.cli'` ≥ 2; `grep -c 'codemax platform-context'` = **0** (catches the `check` twin). Run each as `test "$(grep -c …)" -eq 0` — the bare `grep -c` exits 1 when the count is 0, i.e. it reports failure when the file is *correct* `⟨F5⟩` `⟨F-c2⟩` |
| 8 | Correct the note, decidably | per copy: `grep -q 'retrieval is wired'` **and** `! grep -q 'does not exist'` `⟨F4⟩` |
| 9 | Prove the cron carries it — **safely** | **Do not** set a scratch `HERMES_HOME`: `resolve_hermes_home` (install.sh:87-107) prefers `hermes config path`, so a scratch value is **ignored** and the live 31 skill dirs are `rm -rf`'d and recopied — and `hermes bundles create … --force` is rewritten. Use `HERMES_DRY_RUN=1` to prove the source path resolves, then assert on `hermes/skills/brainstorming/SKILL.md` **directly** rather than via an install run `⟨F3⟩` `⟨F-c2⟩` |
| 10 | Assert the gate stayed off | `TAPWAY_BRAINSTORM_GATE` absent from all 7 env files **and** `test ! -d ~/.hermes/agent-hooks` `⟨F12⟩` |

## Success criteria

1. A pack is produced **with the network down**, and the assertion matches the renderer's real shape (ADR
   ids + roles; `'catalog:' in idx` is False) `⟨F1⟩` `⟨F8⟩`.
2. `check` proven to fail on an ungrounded doc and pass on a grounded one.
3. `~/.local/bin/codemax` sha256 unchanged; the venv's `bin/codemax` **exists** and is documented as
   expected `⟨F2⟩`.
4. All three repo trees **and** all 7 installed copies carry the working command, and the simulated install
   proves the weekday cron distributes rather than reverts it `⟨F3⟩`.
5. Every "does not exist" claim about retrieval is gone from every copy — checked as a negative grep `⟨F4⟩`.
6. `TAPWAY_SPECS_DIR` non-empty in 7 files; `TAPWAY_BRAINSTORM_GATE` in none; `~/.hermes/agent-hooks` absent.
7. The plan's own claim is bounded to what the data supports: roles + ADR ids + constitution `⟨F9⟩`.

## Out of scope

- Enabling `TAPWAY_BRAINSTORM_GATE` here (pilots-only by decision; needs an explicit owner override).
- Installing the gate hooks at all.
- Writing to `tapway/platform-specs`, or authoring new specs.
- **Grounding contracts or ownership** — the catalogs carry none `⟨F9⟩`.
- Changing the skill's normative Step 1.5 requirement (host-specific command + note only).
