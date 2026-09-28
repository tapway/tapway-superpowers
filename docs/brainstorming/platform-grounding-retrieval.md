# Brainstorm: Making brainstorming Step 1.5 retrieve for real

- **Date:** 2026-09-28
- **Status:** Proposed (awaiting plan)
- **Author:** flow-decide run, codemax profile
- **Companion docs:** `docs/plans/2026-09-21-platform-grounding-g1-g6.md` (the feature this completes on
  the host side)

## 1. Problem restated

`brainstorming` v1.3.0 mandates **Step 1.5 — Platform Context (MANDATORY, fail-closed)** before any
option is generated. On this host the retrieval **cannot run at all**, so every brainstorm doc carries
`UNKNOWN (not retrieved: …)` rows. The step is mandatory by discipline and unenforceable in practice.

**User-facing goal:** `/flow-decide` Step 2 reasons from the platform-wide design (contracts, ownership,
ADRs, data model, dependency direction) instead of filling UNKNOWN rows. **Narrowed in doubt cycle 1:** it cannot ground everything claimed below —
every component in both real catalogs carries `provides: []` / `consumes: []`, so a compiled pack exposes
zero contracts and no contract-derived citation can resolve. What is groundable is shown in §5.

**Scope locked via interview:**
- Retrieval **on**; the fail-closed gate stays **OFF**, respecting the documented rollout decision.
- The `~/.local/bin/codemax` launcher wrapper is **not** to be moved or shadowed.

## 2. Current state (grounded survey)

| Fact | Measured value |
|---|---|
| The CLI | `tapway/codemax` → `src/codemax/cli.py`; `[project.scripts] codemax = "codemax.cli:cli"`; PR **#104 merged 2026-09-20**; TDD suite `tests/test_platform_context_cli.py` |
| CLI surface | `platform-context build --specs-dir <dir> --platform <p>`; `check --specs-dir … --doc <md>`; `check --all-repos` |
| Spec repo | `tapway/platform-specs` — **private**, ~5KB, `CODEMAX.md` `README.md` `SCHEMA.md` `constitution.md` `platforms/` |
| Name collision | `~/.local/bin/codemax` is a **hermes wrapper** (`exec hermes -p codemax "$@"`), not the CLI |
| `TAPWAY_SPECS_DIR` | unset in every profile `.env`; hook default is `~/platform-specs-local` |
| Gate hook | `hermes/agent-hooks/pre-brainstorm-ground.{sh,-lib.sh}` + `extract-post-text.py` exist in-repo and are **pure bash + python3** (no CLI dependency); `~/.hermes/agent-hooks/` **does not exist** |
| Documented rollout | *"Gate stays OFF by default in this public repo (`TAPWAY_BRAINSTORM_GATE=1` enables; per-repo adapters enable it for pilots)"*; pilots = `samurai-inspector#52`, `city-terra#204`; *"Fleet-wide enablement after pilot feedback"* (decided by CH Lim) |
| Honesty patch already applied | the installed v1.3.0 carries a **Box reality** note stating no gate fires here — this doc must not quietly contradict it |
| **Where the served copy actually lives** | the **root/default tree** (`~/.hermes/skills/tapway/brainstorming/SKILL.md`) — note ×2, bare command ×3. A `profiles/*`-only file set misses it |
| **A weekly writer overwrites it** | cron `9486afce96d1` `codemax-skills-weekday-sync` (**enabled**, `0 9 * * 1-5`) → repo `hermes/install.sh`, whose `install_local` does `rm -rf "$dest"` then `cp -a`. Repo source `skills/brainstorming/SKILL.md` still has the bare command ×3 |
| **Dependency drift** | the venv resolves `hermes-agent` from PyPI (newest release **0.19.0**) while this box runs **0.21.5+3840**; codemax's pyproject says the 0.21 line is required for parent-gate semantics |

**Two separable halves.** The **gate** needs no CLI and could be enabled today; the **retrieval** needs
the CLI. This doc scopes both deliberately and independently.

## 3. Options

### A. Retrieval only, gate OFF (recommended)
Dedicated venv with `tapway/codemax` installed; clone `tapway/platform-specs`; export a **non-empty**
`TAPWAY_SPECS_DIR` per profile; call **`python -m codemax.cli platform-context build …`**; leave
`TAPWAY_BRAINSTORM_GATE` unset.
**Corrected in doubt cycle 1 — the collision claim was false.** Installing the package **does** create a
`codemax` console script, inside the venv's own `bin/` (`[project.scripts] codemax = "codemax.cli:cli"`;
reproduced empirically against a scoped copy). The protection is therefore not "no script exists" but
**"that venv is never activated and its `bin/` never precedes `~/.local/bin` on PATH"** — otherwise
`codemax --resume` would silently run the Python CLI instead of the owner's Hermes session picker. The
venv's `bin/codemax` is therefore asserted to **exist as expected**, not treated as a failure.
- **Platform Fit:** `UNKNOWN (not retrieved: platform pack unavailable — `codemax platform-context` is not installed on this host and `tapway/platform-specs` is not cloned. Retrieval is the subject of the companion brainstorm `platform-grounding-retrieval.md`.)`
- **Grounding:** `UNKNOWN (not retrieved: platform pack unavailable — `codemax platform-context` is not installed on this host and `tapway/platform-specs` is not cloned. Retrieval is the subject of the companion brainstorm `platform-grounding-retrieval.md`.)`
- **Pros:** removes the UNKNOWN rows that are *groundable* — component roles, platform ADR ids and the
  constitution (NOT contracts or ownership: both real catalogs carry `provides: []` / `consumes: []`);
  zero deviation from the documented rollout; reversible (a clone and a venv).
- **Cons:** Step 1.5 remains discipline-enforced, not gate-enforced, so the Box reality note stays true
  and must be kept in sync instead of deleted.
- **Complexity:** Low-Medium.

### B. Retrieval + gate ON here
As A, plus `hermes/agent-hooks/` installed, `config.hooks.yaml` wired with matcher
`terminal|write_file|patch`, and `TAPWAY_BRAINSTORM_GATE=1`.
- **Platform Fit:** `UNKNOWN (not retrieved: platform pack unavailable — `codemax platform-context` is not installed on this host and `tapway/platform-specs` is not cloned. Retrieval is the subject of the companion brainstorm `platform-grounding-retrieval.md`.)`
- **Grounding:** `UNKNOWN (not retrieved: platform pack unavailable — `codemax platform-context` is not installed on this host and `tapway/platform-specs` is not cloned. Retrieval is the subject of the companion brainstorm `platform-grounding-retrieval.md`.)`
- **Pros:** makes "fail-closed" literal on this box; the Box reality note could be corrected.
- **Cons:** **contradicts a documented decision** — enablement was scoped to two pilot repos, fleet-wide
  only after pilot feedback. It also makes every brainstorm-doc write on this box refusable, including
  writes made during unrelated work.
- **Complexity:** Medium.

### C. Status quo (UNKNOWN rows forever)
- **Pros:** no work; nothing can break.
- **Cons:** the mandate stays vacuous; UNKNOWN rows per doc train readers to ignore the section.
- **Complexity:** None.

### D. Revert brainstorming to v1.2.0 (no Step 1.5)
- **Pros:** removes a step that cannot execute.
- **Cons:** throws away the upstream intent and diverges every profile from the pack — the next upgrade
  re-introduces it; loses the routing/ownership questions that are useful even when unanswered.
- **Complexity:** Low.

**Rejected because collision:** putting the venv's `bin/` on PATH. That is what shadows the owner's
launcher — the installation itself is harmless while the venv stays off PATH and unactivated.
`python -m codemax.cli` is the same code path the project's own test uses.
**Rejected because it contradicts a decision, not a gap:** enabling the gate repo-wide on this Mac as the
*default* outcome (option B). The rollout doc is explicit; overriding it must be an owner decision, stated
as an override, not folded in as a side effect of "wiring Step 1.5".

## 4. Evaluation

| Option | Fixes the complaint | Matches documented rollout | Reversible | Risk |
|---|---|---|---|---|
| **A** | **Yes** | **Yes** | Yes | Low |
| B | Yes + enforcement | **No — override** | Yes | Medium |
| C | No | Yes | n/a | Low |
| D | No (deletes the feature) | Yes | Yes | Low |

## 5. Recommendation

**Option A.** Additionally: **update the installed Box reality note** to say retrieval is wired and the
gate is still off-by-decision — an honest note that outlives its facts is the same failure as a false
claim, and the note currently says the command "does not exist".

**Assumptions that would change this recommendation:**
- If `tapway/codemax` requires `hermes-agent>=0.19.0` in a way that conflicts with the installed Hermes
  version, the venv isolates it — but if the CLI turns out to need a running codemax service, retrieval
  becomes a service dependency and this plan stops being low-complexity.
- If the owner wants pilot-grade enforcement on this box, option B becomes correct — but only via an
  explicit override recorded in the plan.

## 6. Save output

This file.

## 7. Hand off

`writing-plans` → `docs/plans/2026-09-28-platform-grounding-retrieval.md`.

## Red flags

- ❌ Installing the `codemax` console script and breaking the owner's launcher
- ❌ Claiming the gate is enforced while `TAPWAY_BRAINSTORM_GATE` is unset
- ❌ Leaving a Box reality note on disk that describes a state that no longer exists
- ❌ Pushing to `tapway/platform-specs` — it is referenced **read-only**

## 8. Doubt cycle 1 corrections

Revised after the Step 4 gate returned 48 findings across the three plans
(`docs/plans/2026-09-28-doubt-cycle-1-reconciliation.md`). Changes here are limited to statements that
were **false on this machine** or that inverted the pack's own rules; each was re-measured before it was
written. Findings that are plan-level (criteria shape, scope, ordering) are fixed in the plan, not here.
