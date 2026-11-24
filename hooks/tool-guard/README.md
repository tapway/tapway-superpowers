# tool-guard

A `PreToolUse` hook that runs before **every** Bash command and file-tool call
(Read, Edit, Write, MultiEdit, Grep, Glob, NotebookEdit). It does three jobs:

1. **Keeps secrets out of the transcript.** Blocks:
   - reading or copying `.env`, `*.env` and `.envrc` files (templates such as
     `.env.example`, `.env.local.example` and `sample.env` stay readable);
   - credential files: `~/.aws/credentials`, ssh private keys, `.netrc`,
     `.npmrc`, `.pgpass`, `gh/hosts.yml`, `/run/secrets/`, `credentials*.json`,
     private-key `.pem`/`.key`;
   - environment dumps: `printenv`, `env`, `export -p`, `/proc/*/environ`,
     `docker exec|compose exec|compose run ... env`, `docker inspect` without a
     narrow `--format`, `docker compose config|convert` without `--quiet`,
     `echo $..._TOKEN`, `print(os.environ)`, `console.log(process.env)`, `ps e`,
     `systemctl show` without `-p`;
   - credential printers: `gh auth token`, `aws configure get`,
     `aws secretsmanager get-secret-value`, `kubectl get secret -o ...`,
     `vault read`;
   - passwords in argv: `curl -u`, `redis-cli -a`, `mysql -p<pw>`,
     `mc alias set`, `user:pass@` URLs, `--password=`;
   - `grep -r` over the repo root without `--include`/`--exclude` (it reads
     `.env`; the Grep tool and `rg` skip gitignored files).
2. **Keeps work off protected branches.** Blocks commits on and pushes to
   protected branches (also via `HEAD`, `@`, a computed `"$(git branch
   --show-current)"`, `--all`, `--mirror`, `--tags`, a `checkout` or `cd`
   earlier on the same line), every force-push (`--force`, `-f`, `+refspec`),
   and PRs that skip the repo's promotion flow.
3. **Asks before changes (opt-in).** With `ask_before_changes` on, or
   `TAPWAY_GUARD_ASK=1` in the environment, commands it recognises as changing
   a server, repo or database show an approval prompt: docker/compose
   up/down/build/run/rm, changing `make` and `package.json` scripts, git/gh
   writes, `curl` with a body or non-GET method, SQL and Redis writes, `rm`,
   `mv`, redirects into files, installs, `sed -i`, `find -delete`, repo scripts
   (`./deploy.sh`, `bash x.sh`, `python manage.py ...`), `npx`, `kubectl` /
   `terraform` / `helm` / `aws` writes. Read-only commands run freely.

It looks through `\` line continuations, `#` comments, `bash -c`, `eval`,
`$(...)` (quoted or not), backticks, `sudo`/`env`/`timeout` wrappers (with
their option values), `if`/`for`/`{` keywords, redirections and `;` `&&` `|`
chains. Heredoc bodies fed to a shell, `ssh`, an interpreter or a SQL client
are checked as code; other heredoc bodies (commit messages, file contents) are
data, but an unquoted one is still checked for `$(...)` and secret variables.
Anything it cannot parse is blocked, and so is everything when `python3` is
missing or the repo config is broken: it fails closed.

Over-blocking is deliberate: a false block costs a rephrase, a miss puts a
secret into a transcript.

## Known limits

- **Asking is a list of known changing commands, not an allowlist.** An
  unknown program (`./bin/something-new`, a custom CLI) runs without a prompt.
  On servers, keep the managed-settings `ask` rules and read what the agent runs.
- **It reads commands, not intent.** A script the agent writes to a file and
  then runs can still read anything the user can; the prompt before running it
  (repo scripts ask) is the defence.
- Globs that only match at run time (`cat .en?`) are not expanded.
- Deliberate blocks some users will hit: `git push --tags` (tags trigger
  releases), `declare -p NAME`, a secret getter's name used as a plain word.
- Claude Code only. Codex and Hermes run `pre-bash-safety`, not tool-guard.

## Defaults (no config)

| | Default |
|---|---|
| Protected branches | `main`, `master` |
| PR flow | none |
| Ask before changes | **off** (on with `TAPWAY_GUARD_ASK=1`; the server template sets it) |
| `.env` files | blocked; `.env.example`, `.env.sample`, `.env.template`, `.env.dist` (also as a last suffix, e.g. `.env.local.example`) readable |
| Credential files, env dumps, secrets in argv | always blocked |

Asking is off by default so `/autoship` and everyday local work are not
interrupted; secret and branch protection are always on.

## Per-repo config: `.claude/tool-guard.json`

Optional. Every key is optional; unknown keys, wrong types and bad regexes
block every call until fixed (so a typo cannot silently weaken the guard). On a
laptop the agent may still Read/Edit the broken file itself to fix it. Keys
starting with `_` are comments.

### Managed mode (servers): repo config can only tighten

The agent can edit any file in the repo, including this config. So on machines
where the guard must hold no matter what the agent does, set
`TAPWAY_GUARD_MANAGED=1` (the [server template](../../server/managed-settings.json)
does). Then:

- `protect_env_files` is always `true`; `allowed_env_templates` can only drop
  entries from the defaults; `protected_branches` is the defaults **plus** the
  repo's list. Credential files, env dumps and secrets in argv are always
  blocked anyway.
- The agent cannot change the guard's own policy: Edit/Write/MultiEdit of
  `.claude/tool-guard.json` or `.claude/settings*.json`, and shell commands that
  write them (`>`, `sed -i`, `cp`, `mv`, `rm`, `tee`, inline Python), are
  blocked; reading them is fine. The server template also denies these edits in
  Claude Code's own permissions, so both layers hold.
- A broken config is fixed by a human, not by the agent.

```json
{
  "_comment": "why these settings",
  "protected_branches": ["develop", "staging", "master"],
  "pr_flow": {"staging": "develop", "master": "staging"},
  "require_pr_base": true,
  "ask_before_changes": true,
  "secret_getters": ["envget"],
  "secret_hint": "use scripts/env.sh (envshow, envcheck)",
  "read_only_make_targets": ["help", "test", "lint", "preflight"],
  "read_only_scripts": ["\\bscripts/check_stream\\.py\\b"],
  "mutating_commands": ["envset"],
  "redis_clients": ["rcli"],
  "sql_clients": ["psqlq"],
  "minio_clients": ["minio_mc"]
}
```

| Key | Type | Default | Meaning |
|---|---|---|---|
| `protected_branches` | list | `["main","master"]` | No commits on / pushes to these |
| `pr_flow` | object | `{}` | base → the only head allowed to open a PR into it |
| `require_pr_base` | bool | `false` | `gh pr create` must pass `--base` |
| `ask_before_changes` | bool | `false` | Prompt before changing commands |
| `protect_env_files` | bool | `true` | Block `.env` files (credential files stay blocked regardless) |
| `allowed_env_templates` | list | `example, sample, template, dist` | `.env.*.<suffix>` files that stay readable |
| `secret_paths` | list (regex) | `[]` | Extra files that hold secrets in this repo |
| `secret_getters` | list | `[]` | Helpers that print one secret; only `VAR=$(getter KEY)` is allowed |
| `secret_hint` | string | generic | Shown when an env file is blocked: where to go instead |
| `read_only_make_targets` | list | `help, test, lint, check, format-check, typecheck` | Targets that never prompt |
| `read_only_package_scripts` | list | `test, lint, check, typecheck, format-check, format:check` | `npm/pnpm/yarn/bun run` scripts that never prompt |
| `read_only_scripts` | list (regex) | `[]` | Repo scripts that never prompt (direct, via an interpreter, or `docker exec`) |
| `dev_tools` | list | `pytest, ruff, mypy, pre-commit, pip-audit` | Local tools that never prompt (also via `uv run`, `python -m`) |
| `exec_read_only` | list | `pg_isready, nvidia-smi, cat, ls, df, ps, ...` | Programs allowed via `docker [compose] exec` without a prompt |
| `mutating_commands` | list | `[]` | Extra commands that prompt (repo helpers) |
| `redis_clients` / `sql_clients` / `minio_clients` | list | `[]` | Repo wrappers classified like `redis-cli` / `psql` / `mc` |

The config is found through `CLAUDE_PROJECT_DIR` (set by Claude Code), else the
payload's `cwd`. A command that `cd`s into another git repo is judged by that
repo's own config (or the defaults); `ask_before_changes` stays on if the
starting repo had it.

## Tests

`python3 tests/test_tool_guard.py` pipes real Claude Code payloads (JSON on
stdin) through `tool-guard.sh` for every rule, every config key, and every
finding of the adversarial review it went through before release.
