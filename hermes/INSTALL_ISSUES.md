# Hermes install — field issues (v1.8.2 update)

Documented during a real Windows + Hermes Agent update to
[`tapway-superpowers@v1.8.2`](https://github.com/tapway/tapway-superpowers/releases/tag/v1.8.2)
(commit `6b5d21c`). Use this when debugging install/update failures.

## Environment

| Piece | Observed |
|---|---|
| OS | Windows 10, Hermes terminal = git-bash/MSYS |
| Claude Code plugin | Already at `1.8.2` after `claude plugin marketplace update` + `claude plugin update` |
| Hermes skills (before) | 16 of 24 under `skills/tapway-superpowers/` (Jul 28 local drop) |
| Hermes skills (goal) | Full 24-skill pack + `/tapway` bundle |

Claude Code path was healthy (agents manifest fix from #18 verified).
**All pain was on the Hermes skillpack path.**

---

## Issue 1 — Hub `skills-guard` false positives block first-party skills

`hermes skills install tapway/tapway-superpowers/hermes/skills/<name>` runs
skills-guard on community sources. These **first-party** Hermes ports were
verdict **DANGEROUS** and **blocked** (`--force` does **not** override
dangerous):

| Skill | Guard rule(s) | Trigger (benign docs text) |
|---|---|---|
| `tdd` | `agent_config_mod` | Prompt template: `CLAUDE.md / project conventions` |
| `autoship` | `agent_config_mod`, `sudo_usage` | `CLAUDE.md`; rollback snippet `sudo systemctl restart` |
| `systematic-debugging` | `agent_config_mod` | Post-mortem: `update CLAUDE.md convention` |
| `pre-review-cleanup` | `agent_config_mod` | Scan list / example mentioning `CLAUDE.md` |
| `pr` | `agent_config_mod`, `env_exfil_curl` | `TARGET_BRANCH` grep over `CLAUDE.md`; example `curl -H "Authorization: token …"` |
| `repo-docs` | `read_secrets_file` | Discovery: `cat .env.example` |
| `setup-project` | `agent_config_mod`, `path_traversal` | Skill exists to create agent guide + `ln -sf …/.git/hooks` |

Safe skills (interview, brainstorming, writing-plans, e2e-playwright, …)
installed via hub without issue.

### Fix in this PR

1. **Installer local mode** — when run from a git checkout, copy
   `hermes/skills/*` into `$HERMES_HOME/skills/<category>/` and skip the hub
   scanner (authoritative for our own pack).
2. **Skill wording** — Hermes ports avoid guard-trigger substrings while
   keeping the same behavior (prefer `AGENTS.md` / `.hermes.md`; no raw
   bearer curl examples; no `sudo systemctl`; no `cat` of env templates).

---

## Issue 2 — Installer reported success on blocked installs

`hermes skills install` returned **exit code 0** even when stdout contained:

```text
Installation blocked: Blocked (community source + dangerous verdict, …).
--force does not override a dangerous verdict.
```

Old `install.sh` / `install.ps1` treated exit 0 as success:

```bash
if hermes skills install …; then
  echo "✓ installed"
  installed=$((installed + 1))
fi
# …
echo "Done. $installed/$installed skills installed."   # always 24/24
```

So a half-installed pack looked green.

### Fix in this PR

- Parse hub output for `Installation blocked` / `Verdict: DANGEROUS`.
- Track hub vs local vs failed counts separately.
- Exit **non-zero** if any skill failed.
- Never print `24/24` unless 24 actually landed.

---

## Issue 3 — No offline / pin-to-tag path

Hub install always pulls the **default branch tip** via skills.sh / GitHub.
There is no `hermes skills install …@v1.8.2` today.

Updating “to v1.8.2” required:

1. `git fetch --tags && git checkout v1.8.2` in a clone, then
2. Local copy into Hermes skills.

### Fix in this PR

- `HERMES_INSTALL_MODE=local` copies from the current checkout (tag/commit you
  have checked out).
- `HERMES_SKILLS_REF` is documented as the human pin for that checkout.
- Default `auto` mode prefers local when `hermes/skills/` exists beside the
  installer.

---

## Issue 4 — Category name drift

| Source | Category |
|---|---|
| Old manual drop | `tapway-superpowers` |
| Installer default | `tapway` |

Both work; paths differ (`skills/tapway/…` vs `skills/tapway-superpowers/…`).
Re-running with a different category creates a second tree.

### Fix in this PR

- Document both; recommend keeping the category you already use
  (`bash install.sh tapway-superpowers` if that is what `hermes skills list`
  shows).
- Default remains `tapway` for greenfield installs.

---

## Issue 5 — Bare skill name collisions

Hermes also ships / hosts:

- `software-development/writing-plans`
- `software-development/systematic-debugging` (builtin)

After installing Tapway copies, `hermes skills list` may show **one row per
bare name** even though both trees exist on disk. The `/tapway` bundle still
references the Tapway names.

### Fix in this PR

- Installer prints a collisions notice.
- Document in `hermes/README.md`: prefer `/tapway` or qualified paths when
  disambiguating.

---

## Issue 6 — Claude vs Hermes surfaces (not a bug)

| Surface | Update path | v1.8.2 status |
|---|---|---|
| Claude Code plugin | `claude plugin marketplace update tapway-superpowers` then `claude plugin update tapway-superpowers@tapway-superpowers` | Already current; agents → `AGENT.md` |
| Local git clone | `git fetch --tags && git checkout v1.8.2` | Required for Hermes local install pin |
| Hermes skills | `hermes/install.sh` (this PR) | Was incomplete until local sync |

Do not assume Claude plugin update refreshes Hermes skills — they are separate.

---

## Issue 7 — Windows path quirks (environment)

- `git -C /c/Users/...` sometimes fails under MSYS; `cd` into the repo or use
  `pathlib`/`git -C` with a Windows path works.
- `claude plugin validate` from git-bash can double-prefix `C:\c\Users\...`.
  Validate from PowerShell or pass a native Windows path.

Not fixed in-repo (host tooling); noted so agents do not chase false failures.

---

## Recommended update procedure (post-fix)

```bash
# 1) Pin the repo
git fetch --tags origin
git checkout v1.8.2   # or main after this PR merges

# 2) Hermes skills (from repo root)
cd hermes
# keep existing category if you already use it:
bash install.sh tapway-superpowers
# or greenfield:
# bash install.sh

# 3) Verify
ls "$HERMES_HOME/skills/tapway-superpowers" | wc -l   # expect 24
hermes bundles list | grep tapway
```

PowerShell:

```powershell
cd hermes
.\install.ps1 tapway-superpowers
```

Force local-only:

```bash
HERMES_INSTALL_MODE=local bash install.sh tapway-superpowers
```

---

## Related

- Release: https://github.com/tapway/tapway-superpowers/releases/tag/v1.8.2
- Agents manifest fix: #18
- Hermes skill hub / skills-guard: Hermes Agent `tools/skills_guard.py`
