# Plan: Ship an installable Hermes plugin

## Goal

Anyone with Hermes can install Tapway Superpowers without cloning the repo or
running `hermes/install.sh`:

```bash
hermes plugins install tapway/tapway-superpowers/hermes/plugin --enable
```

## Why not a root plugin.yaml

`hermes plugins install tapway/tapway-superpowers` would install the whole
repository. Hermes plugin-guard scans that tree as DANGEROUS (hook scripts,
Codex installers, docs that mention `curl | bash` and `sudo`). A subdirectory
install copies only `hermes/plugin/`. That tree is the already-scrubbed Hermes
skill port plus a thin `register()`.

## Approach

1. Add `hermes/plugin/plugin.yaml` and `hermes/plugin/__init__.py`.
2. Mirror `hermes/skills/` into `hermes/plugin/skills/` so the installed plugin
   is self-contained. A test fails if the two trees diverge.
3. `register()` calls `ctx.register_skill` for each skill directory.
4. Document the one-line install in `hermes/README.md`, the root README, and
   `docs/DEPLOYMENT.md`.

Plugin skills are namespaced (`tapway-superpowers:brainstorming`). They do not
create bare slash commands. `hermes/install.sh` remains the slash-command path.

## Files

| Path | What |
|---|---|
| `hermes/plugin/plugin.yaml` | Manifest. Name `tapway-superpowers`, version `2.4.0`. |
| `hermes/plugin/__init__.py` | `register(ctx)` walks `skills/`. |
| `hermes/plugin/skills/` | Byte mirror of `hermes/skills/`. |
| `tests/test_hermes_plugin.py` | Manifest, register coverage, byte mirror, documented install command. |
| `hermes/README.md`, `README.md`, `docs/DEPLOYMENT.md`, `docs/WORKFLOWS.md` | Install instructions. |

## Rollback

Delete `hermes/plugin/` and the doc lines. No Claude plugin manifest change.
Installed copies are removed with `hermes plugins remove tapway-superpowers`.
