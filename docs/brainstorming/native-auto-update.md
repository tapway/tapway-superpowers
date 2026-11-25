# Brainstorm: Native auto-update on Claude Code and Hermes

- **Date:** 2026-11-25
- **Status:** Accepted — implemented by issue [#67](https://github.com/tapway/tapway-superpowers/issues/67)
- **Author:** CH Lim

## 1. Problem

Every user who installs `tapway-superpowers` or `tapway-skills` should receive
updates through the mechanism their harness already has. The update must not
depend on this server, a personal cron, or a human merging a PR.

**Done means:** a fresh install is the only manual step. After that, a nightly
release reaches Claude Code and Hermes Agent without user action, and a mirror
that falls behind is reported rather than silently stale.

## 2. Harness capabilities (measured 2026-11-25)

### Claude Code

- Both repos already ship `.claude-plugin/plugin.json` +
  `.claude-plugin/marketplace.json`; no packaging change is needed.
- Background plugin auto-update exists but is **off by default for third-party
  marketplaces**. It is enabled per user (`"autoUpdate": true` on the
  `extraKnownMarketplaces` entry, or the `/plugin` → Marketplaces toggle) or by
  an admin through managed settings. It runs after the first message, with a
  random delay up to ten minutes, and applies on `/reload-plugins` or the next
  launch.
- An update lands only when the plugin's **computed version changes**. A pinned
  `version` in `plugin.json` is the normal way the version stays the same across
  commits — committing without a bump ships nothing.

### Hermes Agent

- Native unattended updates are `plugins.auto_apply` (off by default), checked
  every `plugins.auto_update_check_hours` (default 24); new code loads in new
  sessions. `hermes plugins auto-update on` is the switch.
- The update path requires a **git-class install**: the plugin directory must
  contain `.git`. A **subdirectory** source
  (`tapway/tapway-superpowers/hermes/plugin`) is published as a copy without
  `.git`; `check-updates` then reports `drift` and `update` refuses. Reproduced
  on a clean `HERMES_HOME` with the current build.
- A repo whose **root is the plugin** installs with `.git`, reports class `git`
  and `up to date`, and therefore auto-applies. That is the required shape.
- Root-packaging the whole repo fails the install scanner: `codex/`, `hooks/`,
  `tests/` and skill scripts produce a **dangerous** verdict that `--force`
  cannot override (measured: 335 findings here, 1405 in `tapway-skills`).
- `hermes skills tap` + `hermes skills update` exist, but are per-skill hub
  installs with a lockfile and **no auto-apply**. `hermes/install.sh` copies
  files with provenance `local` and is never updatable.
- Plugin skills are namespaced (`tapway-superpowers:tdd`). Vendoring the 74
  product skills as a plugin would break their bare cross-references.

### Consequence

The only shape that Hermes can update unattended is a **git repo whose root is
the plugin**. Neither existing repo can be that repo (scanner), and subdirectory
installs cannot update. Hence generated companion repos.

## 3. Options

| Option | Verdict |
|---|---|
| Root `plugin.yaml` in the existing repos | Rejected: scanner blocks the install (dangerous verdict). |
| Keep installing the subdirectory | Rejected: no `.git`, `update` refuses. |
| Vendor all skills as a Hermes plugin | Rejected: namespacing breaks cross-references; scanner blocks. |
| Hub tap + scheduled `hermes skills update` | Fallback only: works, but no native auto-apply. |
| **Generated companion repos (`git subtree split`)** | **Chosen.** Root-level plugin, clean scanner surface, native auto-update. |

## 4. Design

### 4.1 Release side

Nightly worker per repo:

1. Two-way sync local ↔ repo (conflicts abort and report; they are never
   auto-resolved).
2. Commit to `main` and push directly — no PR.
3. Bump the version: added/removed skill → minor, content-only change → patch.
4. Write the new version into every harness-read manifest **in the same commit**:
   `hermes/plugin/plugin.yaml`, `.claude-plugin/plugin.json`,
   `.claude-plugin/marketplace.json` (top-level `version` and `metadata.version`).
5. Tag `vX.Y.Z`; create the GitHub release.
6. Silent when the tree hash is unchanged.

Bumping the version at release time removes the post-release
`chore(release): sync plugin manifests` PR and the drift window that caused
`docs/post-mortems/2026-11-18-release-manifest-drift.md`.

### 4.2 Claude Code

No code change. Document the one-time opt-in:

```json
"extraKnownMarketplaces": {
  "tapway-superpowers": {
    "source": { "source": "github", "repo": "tapway/tapway-superpowers" },
    "autoUpdate": true
  }
}
```

### 4.3 Hermes

Two companion repos, published from the main repos on every release:

- `tapway/tapway-superpowers-hermes` — root is this repo's `hermes/plugin/`.
- `tapway/tapway-skills-hermes` — a scanner-clean **updater plugin** (code, not
  a vendored skills tree). On `on_session_start` it fast-forwards a cached clone
  of `tapway-skills`, compares tree hashes, and copies `skills/` into
  `~/.hermes/skills/`, preserving bare skill names.

Install:

```bash
hermes plugins install tapway/tapway-superpowers-hermes --enable
hermes plugins install tapway/tapway-skills-hermes      --enable
hermes plugins auto-update on      # once per profile
```

## 5. How the companion repos link, and why they cannot drift

The companion is a **generated mirror**, not a submodule and not a fork.

```bash
git subtree split --prefix=hermes/plugin -b mirror-tmp
# assert: $(git rev-parse mirror-tmp^{tree}) == $(git rev-parse <source-tag>:hermes/plugin)
git push --force-with-lease origin mirror-tmp:master
```

A submodule was rejected: Hermes clones plugins with `git clone --depth 1` and
no `--recurse-submodules`, so submodule content would be missing at install
time; the superproject pointer would also need a bump every release, which is a
second drift surface with worse failure modes.

Five invariants keep the pair honest:

1. **One editable source.** Only the main repo is edited. Companion repos carry
   a "generated — do not edit" banner and accept no feature PRs.
2. **Tree-hash gate on both sides.** The release job refuses to push unless the
   split tree equals the source subtree; the companion's CI re-asserts the same
   equality on every push and PR:
   - `SOURCE.json` records `{repo, commit, tag, version, tree}`.
   - CI clones the source at `commit`, computes `HEAD:hermes/plugin`, and fails
     on any mismatch — including a hand-edit committed by an admin.
3. **Version lockstep.** Source tag = `plugin.yaml` = `plugin.json` =
   `marketplace.json` (`version` and `metadata.version`) = companion tag =
   `SOURCE.json.version`. `scripts/check-release-drift.sh` gains the companion
   as its sixth surface.
4. **Atomic, ordered release.** Verify manifests → tests → bump → tag source →
   split and assert hash → push mirror → tag mirror with the same tag → read
   back. A failure at any step is a red workflow; there is no "tagged but
   mirror stale" green state.
5. **Nightly reconcile.** Compare the newest source tag with `SOURCE.json`; if
   the companion is behind, re-split and push, and report it. Self-healing, and
   a manual hotfix in the companion is overwritten rather than merged back.

## 6. Rollout

1. `tapway-skills`: `open_pr()` → `commit_and_release()` (tests first).
2. `tapway-superpowers`: release workflow publishes the mirror after tagging.
3. Create the two companion repos with the integrity CI.
4. Write the updater plugin.
5. README: Claude opt-in and the Hermes two-command install.
6. This server: re-point the nightly cron, reinstall from the companion repo,
   enable `plugins.auto_apply`.
7. Delete the PR-based sync path.

## 7. Acceptance criteria

- An unchanged nightly run emits nothing, commits nothing, tags nothing.
- A changed run produces one commit, a bumped version, and
  tag == manifest version == release name.
- Claude with `autoUpdate: true` picks up a release after a session start.
- Hermes reports `git` + `update available` between releases and applies it.
- A fresh Hermes profile needs only the two install commands.
- Companion tree hash equals the source subtree hash at every release, and a
  hand-edit in a companion fails CI.

## 8. Open questions

- Should the companion repos be archived entirely once Hermes retains `.git`
  for subdirectory installs? That upstream change would remove the need for
  them; the mirrors should stay until every supported Hermes build has it.
- Major-version policy for breaking removals (skill deleted, plugin API
  changed): auto-bump or human approval? Proposal: auto-bump only for
  additions/edits; a removal requires a human, because it deletes user-visible
  skills.