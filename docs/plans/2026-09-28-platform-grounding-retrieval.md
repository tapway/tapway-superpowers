# Plan: Step 1.5 platform grounding — environment wiring

**Date:** 2026-09-28 · **Revision v4 (supersedes v3)**
**Records:** `2026-09-28-doubt-cycle-{1,2,3}-reconciliation.md` (all three cycles; v3 cited only cycle 1)

---

## Read this first: the premise of v1–v3 was false

v1–v3 planned to *wire Step 1.5 for real*. That is not the situation. `docs/plans/2026-09-21-platform-grounding-g1-g6.md`
has been on master throughout, marked **Status: implemented**, and the implementation is present:

| Claim in v1–v3 | Reality on master, measured 2026-09-28 |
|---|---|
| Step 1.5 needs wiring | **present in all three variants** — `skills/`, `hermes/skills/`, `codex/skills/` each contain Step 1.5, `Platform Context` and `Grounding:` |
| retrieval not wired | `hooks/pre-brainstorm-ground/` exists (lib + extractor + adapter) and `hermes/config.hooks.yaml:34` already points at it |
| *(not mentioned at all)* | `tests/test-phase-g.sh` and `tests/e2e-platform-grounding.sh` already exist |

The doubt gate could not catch this. Reviewers were given the artifact and its contract; the defect was in
the **premise**, not in the criteria. A premise check — *does this already exist?* — belongs before
planning, not after. That is the transferable lesson from this plan, and it cost three doubt cycles.

**So the remaining work is environment wiring, not design.** Nothing here rewrites Step 1.5.

## What is actually broken (each measured this session)

| Evidence | Command | Result |
|---|---|---|
| the E2E suite fails | `bash tests/e2e-platform-grounding.sh` | 3 failures — `pack build (python import)`, `UNKNOWN row should pass`, `real ADR citation should resolve` |
| …and it is **not** a regression | same command on clean `master` | **the same 3 failures** — pre-existing |
| the hook is configured but absent | `test -d ~/.hermes/agent-hooks` | absent, while `hermes/config.hooks.yaml:34` names `~/.hermes/agent-hooks/pre-brainstorm-ground.sh` |
| no CLI on this box | `python3 -m codemax.cli` | `ModuleNotFoundError`; no `~/.hermes/venvs/codemax-cli` |
| specs not wired | grep `TAPWAY_SPECS_DIR` over all 7 env files | unset everywhere |
| the gate is correctly off | grep `TAPWAY_BRAINSTORM_GATE` | absent everywhere — **and it must stay that way** (CH Lim: fail-closed gate is pilots-only; this repo is public) |

## Criteria hygiene (learned the hard way)

Two idioms must not appear in this plan's criteria, because each **fails in the state it is meant to
certify** — and both were caught in this plan set or in the sibling test the same day:

- **Whitespace.** BSD/macOS `wc -l` pads its output (`"       1"`), so `grep -q '^1$'` never matches there.
  Strip it: `$(… | wc -l | tr -d '[:space:]')`. The phase-g drift guard had exactly this bug and reported
  failure on every macOS run regardless of state (fixed in PR #38).
- **`set -e` safety.** `grep -c` exits 1 when the count is 0, so `n=$(… | grep -c X)` aborts a `set -e`
  script in exactly the passing state. Wrap in `|| true`, or use `test "$(… | grep -c X || true)" -eq 0`.

## Tasks

Every criterion is shell-decidable. Items marked *(guard)* already hold and cannot fail from this work;
they are pins, not evidence, and are counted as such.

| # | Task | Criterion |
|---|---|---|
| 1 | Create the venv | `python3 -m venv ~/.hermes/venvs/codemax-cli`, then `~/.hermes/venvs/codemax-cli/bin/python -c 'import sys;assert sys.version_info>=(3,11)'` exits 0. This box is 3.12.8 and `tapway/codemax` declares `requires-python >=3.11` |
| 2 | Install codemax — **v3's command is broken** | v3 said `pip install --no-build-isolation ~/tapway-codemax`. That fails: a fresh venv has no `setuptools`, and with isolation off setuptools is never fetched, so the build backend is unavailable (`BackendUnavailable`). Use `~/.hermes/venvs/codemax-cli/bin/pip install ~/tapway-codemax` (isolation **on**, so the backend is fetched). Offline fallback: `…/pip install -U setuptools` first, *then* the no-isolation form. Criterion: `~/.hermes/venvs/codemax-cli/bin/python -c 'import codemax'` exits 0 |
| 3 | Assert the CLI surface | `~/.hermes/venvs/codemax-cli/bin/python -m codemax.cli platform-context --help` exits 0 (the **subgroup**, and the **venv's** interpreter — never a bare `$PY`, which was undefined in v3, and never bare `python`, since the venv's `bin/` is deliberately off PATH) |
| 4 | Clone the specs **read-only** | `~/platform-specs-local` contains BOTH `constitution.md` and `platforms/samurai-v2/catalog.yaml`. **Never push to this repo** |
| 5 | Wire `TAPWAY_SPECS_DIR` | non-empty and equal to the clone path in each env file the skill reads: `test "$(grep -c '^TAPWAY_SPECS_DIR=.' <f>)" -eq 1` per file, with the file list enumerated, not implied |
| 6 | **Build the pack and fix the three failing E2E assertions** | `bash tests/e2e-platform-grounding.sh` → **0 failures** (currently 3, same 3 on master). See the decision below |
| 7 | Correct the stale skill note | per copy: `test "$(grep -c 'retrieval is wired' <f> || true)" -ge 1` and `test "$(grep -c 'does not exist' <f> || true)" -eq 0` — `|| true` because `grep -c` exits 1 when the count is 0, which aborts a `set -e` harness in the passing state. **Read the anchor coupling immediately below before editing** |
| 8 | Record the hook decision | *(guard)* `test ! -d ~/.hermes/agent-hooks` still true, and `hermes/config.hooks.yaml:34` still names it. The hook is **deliberately not installed**: the gate is pilots-only, and creating this dir here would arm a public repo |
| 9 | Keep the gate off | *(guard)* `TAPWAY_BRAINSTORM_GATE` absent from all 7 env files AND `test ! -d ~/.hermes/agent-hooks` |
| 10 | Record the launcher baseline | `shasum -a 256 ~/.local/bin/codemax` = `08f16040b18cd8c33a0edddb3df5d525d5eb80a0f5c7fe23bc846eef60230a54`. v3 asserted "unchanged" against a baseline it never recorded, so the criterion was undecidable |
| 11 | Record the decision in the pipeline skill | the wiring + gate-off decision appears in **all 7 trees** that carry `hermes-flow-pipeline/SKILL.md` (measured: architect, builder, codemax, decider, doubter, planner, root — v3 said "4 trees" in prose while naming 5, and gave no task) |
| 12 | Durability | the repo-tree edits survive only if **merged**: `git ls-tree origin/master <edited path>` succeeds. `~/.hermes/scripts/codemax-skills-sync.sh:50` hard-resets this repo's checked-out branch to `origin/master` on the weekday tick, so a committed-but-unmerged edit is rewound and `install_local` reinstalls the old text over the served copy |

### Task 7's anchor coupling — do not skip this

`~/.hermes/scripts/tapway-v240-sync.sh` is the document merge-safe sync for this tree, and it **fails
closed on literal anchors**:

- lines 84–86 define `ANCHOR_A` (the upstream sentence that mentions `codemax platform-context check`)
- lines 91–93 define `ANCHOR_B` (the `codemax platform-context build --specs-dir …` block)
- lines 98–100: if either count is wrong → `print('BOXNOTE-DELTA-FAILED …'); sys.exit(3)`
- lines 175–179: `rm -rf "$dest/$name"; cp -a "$UP/$name" "$dest/$name"` before `apply_boxnote`
- lines 142–144: the classifier keys on the literal phrase `Box reality`

**Consequence, verified:** v1–v3's requirement that `codemax platform-context` occur **0** times would zero
ANCHOR_B, trip the guard, and leave the skill at upstream v1.3.0 — the version that still asserts the
pre-tool hook will block the write. The one edit this plan exists to make would have been blocked by the
plan's own guard.

Criterion: after the note edit, `bash ~/.hermes/scripts/tapway-v240-sync.sh` (**dry-run by default**)
still classifies the skill as KEEP, not FLAG. Either keep the anchors or update them in the same change.

### The one genuine design question left (task 6)

The E2E failure `UNKNOWN row should pass` is not environment noise — it is a real contradiction:

- the skill **mandates** `UNKNOWN (not retrieved: …)` rows when the pack is unavailable
  (`brainstorming/SKILL.md`: "every option in the doc must carry an UNKNOWN (not retrieved: …) row")
- the checker's `_resolve_ref` splits every comma-separated value after a `Grounding:` line and appends
  anything not in `pack.ownership`/`pack.adr_ids` to `unresolved` → the UNKNOWN text lands in `unresolved`
  → `passed=False`

So on a host with no pack, every document the skill instructs an agent to write is **rejected by the
checker**. Either the checker must accept the documented UNKNOWN form, or the mandated form is wrong.
**Decide which is the bug and say so in the PR** — do not relax the test to make it green. The other two
failures (`pack build`, `real ADR citation`) are expected to resolve from tasks 1–5.

## Success criteria

1. `bash tests/e2e-platform-grounding.sh` → 0 failures, from 3 (failable; the current state is RED)
2. `~/.hermes/venvs/codemax-cli/bin/python -m codemax.cli platform-context build --specs-dir ~/platform-specs-local --platform samurai-v2` produces a pack whose output contains ≥1 ADR id and **no** `catalog:` (both catalogs carry `provides: []`, so a catalog citation can never resolve)
3. the checker passes an ADR-id-only doc **and fails** an ungrounded doc — fail-closed proven in both directions
4. the UNKNOWN-row question is decided in writing, with the affected assertion either fixed at its source or the skill text corrected
5. `TAPWAY_SPECS_DIR` non-empty in every env file the skill reads; `TAPWAY_BRAINSTORM_GATE` absent everywhere *(guard)*
6. the sync script still classifies the skill KEEP after the note edit
7. `~/.local/bin/codemax` sha256 matches the recorded baseline *(guard)*
8. the change is **merged** to master, not merely committed

## Files

| Path | Action |
|---|---|
| `~/.hermes/venvs/codemax-cli/` | create |
| `~/platform-specs-local/` | clone (read-only source) |
| `~/.hermes/profiles/*/.env` + `~/.hermes/.env` | set `TAPWAY_SPECS_DIR` — enumerate the exact files actually read |
| `tapway-superpowers` skill trees: `skills/`, `hermes/skills/`, `codex/skills/` for `brainstorming` | **MODIFY** the stale note, keeping the sync script's anchors |
| `hermes-flow-pipeline/SKILL.md` — **all 7 trees** | **MODIFY** — wiring + gate-off decision |
| `tapway/codemax` `platform_spec.py` | **only if** task 6 decides the checker is at fault |

## Risks

| Risk | Mitigation |
|---|---|
| A fix becomes the defect — three cycles running, most cycle-3 findings were caused by cycle-2 fixes | Every criterion re-run by execution, not inspection; whitespace and `set -e` idioms banned above |
| Arming a public repo with a fail-closed gate | Task 8/9 are guards: the hook dir does not exist and the env var is absent |
| The sync script fails closed and reverts the skill | Task 7's anchor criterion |
| The weekday cron rewinds committed-but-unmerged work | Task 12 |
| `~/.local/bin/codemax` console-script collision | Never activate the venv or put its `bin/` on PATH; call via the absolute interpreter (task 3) |

## Out of scope

- Rewriting Step 1.5 (already implemented — this is the whole point of v4)
- Enabling the gate, or installing hooks, outside a pilot repo
- Writing to `tapway/platform-specs`
- The Claude Code plugin clones under `~/.claude/plugins/` (three copies, including the versioned cache)
- `e2e` assertions unrelated to grounding
