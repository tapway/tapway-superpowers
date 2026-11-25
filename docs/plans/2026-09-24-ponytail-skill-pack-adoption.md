# Plan: Vendor the ponytail skill pack into tapway-superpowers

## Goal

Ship the token-saving `ponytail` rule set to the whole team as an installable part of
tapway-superpowers, in all three host trees, without silently changing the behaviour that was
measured. The pack is third-party (MIT), so provenance and licence must survive the port.

## Approach

Vendor the six upstream skills **verbatim** (rule text byte-for-byte) and adapt only:

1. **Frontmatter** — add `license: MIT`, `upstream`, `upstream-commit` to every skill; add the
   Hermes/Codex host conventions (`version`, `author`, `platforms`, `metadata.hermes.*`).
2. **An appended host-notes section** — how each host triggers the skill and how to preload it.
   The body above the notes is untouched, so the rule behaves as measured.

Descriptions are deliberately **not** rewritten per the usual `(Hermes port of ...)` suffix
convention: the description is the trigger, and altering it would change when the skill fires —
the one thing the A/B was measuring.

## Files

| Path | What |
|---|---|
| `skills/ponytail{,-review,-audit,-debt,-gain,-help}/SKILL.md` | Canonical, verbatim upstream + provenance |
| `hermes/skills/...` / `codex/skills/...` | Host ports (same body, adapted frontmatter + notes) |
| `skills/ponytail/LICENSE` | Upstream MIT licence (attribution) |
| `tests/test_ponytail_pack.py` | New parity + count-drift test (RED → GREEN) |
| `tests/test_hermes_install.py` | `EXPECTED` + `blocked` grow by 6 |
| `.claude-plugin/{plugin,marketplace}.json` | Register 6 skills; version 2.3.0 → 2.4.0 |
| `hermes/install.sh`, `codex/install.sh` | `SKILLS` arrays + count comments |
| `README.md`, `hermes/README.md`, `codex/README.md` | Counts, skill rows, attribution, measured impact |

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Rule text silently rewritten while porting → behaviour differs from what was measured | Parity test asserts every canonical body line survives in each host port |
| Counts drift across the six declaration points | Test cross-checks each declaration against the filesystem instead of hardcoding numbers |
| Third-party code presented as Tapway-authored | Verbatim `LICENSE`, per-skill `upstream`/`upstream-commit`, explicit README + CHANGELOG attribution |
| Hermes community installs break on guard triggers | Ports scrubbed of `CLAUDE.md` / `cat .env.example`; enforced by both test files |
| Vendored copy rots vs upstream | Upstream commit pinned in every skill for a future re-vendor diff |

## Success criteria

1. `python3 tests/test_ponytail_pack.py` exits 0, and exits non-zero when a vendored file is
   removed or a declared count goes stale (both directions proven).
2. `tests/test_hermes_install.py` passes with the pack in `EXPECTED` **and** `blocked`, so the
   guard-trigger scrub is enforced, not just documented.
3. Every upstream rule line is present in every host tree — i.e. the skill that was measured is
   the skill that ships.
4. Counts agree everywhere: 30 canonical / 31 Hermes / 30 + umbrella Codex.
5. PR passes `workflow-audit.yml` (conventional commits, this plan doc present, no secrets).

## Out of scope

- **`externalSkills` precedent:** this repo documents third-party skills (e.g. `code-refactor`)
  rather than vendoring them. This PR knowingly vendors instead, because vendoring gives the team
  a one-command install and makes the rule text reviewable in-tree — recorded for the reviewer.
- Rewriting the pack's Claude-native `/ponytail*` slash-command references (left verbatim; the
  host-notes section explains the Hermes/Codex equivalents).
- Re-running the A/B at n=5 for tighter error bars.
