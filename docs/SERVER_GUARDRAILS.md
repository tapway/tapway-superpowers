# Running Claude Code on a server

On a laptop, a mistake costs a rephrase. On a server, `cat .env` puts production
passwords into a transcript, and an unattended `docker compose down` takes a
service off-line. This page sets up a server so that every Claude session there:

- has `tapway-superpowers` and `tapway-skills` installed, always, and the user
  cannot switch them off;
- cannot read `.env` or credential files, dump the environment, or put a
  password on a command line (`tool-guard`);
- asks a human before commands recognised as changing something: deploys,
  migrations, git/gh writes, database and file writes, repo scripts
  (`TAPWAY_GUARD_ASK=1`; see the [known limits](../hooks/tool-guard/README.md#known-limits));
- cannot run in bypass ("skip all approvals") mode.

## The layers

```
/etc/claude-code/managed-settings.json  ← root-owned, overrides every user and repo setting
  ├─ installs + force-enables tapway-superpowers and tapway-skills
  ├─ TAPWAY_GUARD_ASK=1  (tool-guard asks before changes)
  ├─ deny: .env / credential files;  ask: deploy, commit, push
  └─ bypass mode disabled

tapway-superpowers (plugin)  ← the same on every machine
  └─ hooks: tool-guard (secrets, branches, approvals), pre-bash-safety, commit gates

<repo>/.claude/  ← what only this repo knows
  ├─ tool-guard.json   which branches, helpers and make targets are special here
  ├─ settings.json     the repo's own deny/ask floor (applies even without the plugin)
  └─ skills/           the repo's own skills (deploy, health checks, ...)
```

Claude Code merges all of them: every hook runs, any `deny` from any level wins,
and an "ask" from any level shows the prompt.

## Fresh server: one-time setup (needs sudo)

1. Install Claude Code and log in as the user who will run it.
2. Give that user read access to the private `tapway/*` repos (`gh auth login`,
   or a deploy key), so the plugins can install.
3. Install the managed settings:

   ```bash
   sudo mkdir -p /etc/claude-code
   gh api \
     -H "Accept: application/vnd.github.raw" \
     repos/tapway/tapway-superpowers/contents/server/managed-settings.json \
     | sudo tee /etc/claude-code/managed-settings.json >/dev/null
   sudo chmod 644 /etc/claude-code/managed-settings.json
   ```

   Or copy `server/managed-settings.json` from a checkout. Do **not** add
   `allowManagedHooksOnly`: it would switch off each repo's own hooks.
4. Start `claude` from a repo root, accept the folder trust prompt, then check:
   - `/plugin`: both plugins installed and enabled (managed);
   - `/hooks`: `tool-guard.sh` listed for Bash and the file tools;
   - ask Claude to `cat .env`: it must be blocked by `tool-guard`.

## How updates reach a server

1. A PR is merged into `master` here.
2. The release workflow tags it and opens a "sync plugin manifests to X.Y.Z" PR.
3. That PR is merged: the new version is now published. (Claude Code compares
   the `version` in `plugin.json`, not commits, so step 3 is what ships it.)
4. Servers with `autoUpdate: true` (the template) download it within about ten
   minutes of a session starting. Or by hand:
   `claude plugin marketplace update tapway-superpowers` then
   `claude plugin update tapway-superpowers@tapway-superpowers`.
5. Hooks load when a session starts: exit and restart `claude`.

`claude plugin list` shows the installed version.

## Adopting it in a repo

- Add `.claude/tool-guard.json` for the repo's branches, helpers and read-only
  make targets ([reference](../hooks/tool-guard/README.md)).
- Keep a small deny/ask floor in the repo's `.claude/settings.json` (plain
  config, no code): it still protects a machine where the plugin is missing.
- Give every skill that runs commands an eval with canary secrets
  ([evals](../evals/README.md)), and run `scripts/skill-evals.sh` before merging
  skill changes. Evals run on a laptop or in CI, never on the server.
