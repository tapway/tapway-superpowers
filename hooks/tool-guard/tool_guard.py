#!/usr/bin/env python3
"""PreToolUse guard: keep secrets out of the agent's context, keep it off
protected branches, and (when switched on) make commands that change things
wait for a human.

Blocks (exit 2, reason on stderr):
  - reading or copying .env / *.env / .envrc files (templates such as
    .env.example stay readable) and credential files (~/.aws/credentials, ssh
    private keys, .netrc, .npmrc, .pgpass, /run/secrets/, ...)
  - printing secrets: printenv / env / `export -p`, /proc/*/environ,
    `docker inspect` without a narrow --format, `docker [compose] exec ... env`,
    `docker compose config` without --quiet, `echo $..._TOKEN`,
    `print(os.environ)`, `gh auth token`, `kubectl get secret -o ...`, and a
    repo's secret getters (e.g. `envget KEY`) unless captured into a variable
  - secrets on a command line: curl -u, redis-cli -a, mysql -p<pw>,
    mc alias set, literal passwords in URLs or --password=...
  - commits on / pushes to protected branches, force-pushes, bulk ref pushes,
    and PRs that skip the repo's promotion flow

Asks (permissionDecision "ask") before commands it recognises as changing a
server, repo or database, when `ask_before_changes` is on in
.claude/tool-guard.json or TAPWAY_GUARD_ASK=1 is set (servers set it in
managed settings). This is a list of known changing commands, not an
allowlist: an unknown program runs without a prompt.

Shell handling: `\\` line continuations are joined, `#` comments dropped,
`bash -c`, `eval`, `$(...)` (quoted or not), backticks, `sudo`/`env`/`timeout`
wrappers, `if`/`for`/`{` keywords and `;` `&&` `|` chains are looked through.
Heredoc bodies fed to a shell, `ssh` or an interpreter are checked as code;
other heredoc bodies (commit messages, file contents) are data, though an
unquoted one is still checked for `$(...)` and secret variables. Anything it
cannot parse is blocked (fail closed).

Per-repo config: .claude/tool-guard.json (see hooks/tool-guard/README.md).
Over-blocking is deliberate: a false block costs a rephrase, a miss leaks a
secret into a transcript.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

CONFIG_NAME = ".claude/tool-guard.json"

DEFAULTS: dict = {
    # Branches nobody commits on or pushes to directly.
    "protected_branches": ["main", "master"],
    # base -> the only head allowed to open a PR into it, e.g. {"master": "staging"}.
    "pr_flow": {},
    # `gh pr create` must name --base (when the default branch is not the PR target).
    "require_pr_base": False,
    # Ask a human before commands that change things (TAPWAY_GUARD_ASK=1 forces on).
    "ask_before_changes": False,
    # Block direct access to .env files. Templates in allowed_env_templates stay readable.
    "protect_env_files": True,
    "allowed_env_templates": ["example", "sample", "template", "dist"],
    # Extra regexes for files that hold secrets in this repo.
    "secret_paths": [],
    # Repo helpers that print one secret; allowed only as VAR=$(getter KEY).
    "secret_getters": [],
    # Shown when an env file is blocked: where to go instead.
    "secret_hint": "read secrets through a helper that never prints values",
    # Read-only make targets (no prompt); every other target asks.
    "read_only_make_targets": [
        "help",
        "test",
        "lint",
        "check",
        "format-check",
        "typecheck",
    ],
    # Read-only package.json scripts (npm/pnpm/yarn/bun run <script>).
    "read_only_package_scripts": [
        "test",
        "lint",
        "check",
        "typecheck",
        "format-check",
        "format:check",
    ],
    # Regexes for repo scripts that only read: run directly, by an interpreter,
    # or via `docker exec`, they never prompt.
    "read_only_scripts": [],
    # Local tools that change nothing outside the working tree.
    "dev_tools": ["pytest", "ruff", "mypy", "pre-commit", "pip-audit"],
    # Read-only programs allowed inside `docker [compose] exec` without a prompt.
    "exec_read_only": [
        "pg_isready",
        "nvidia-smi",
        "df",
        "du",
        "ls",
        "uptime",
        "date",
        "cat",
        "head",
        "tail",
        "wc",
        "stat",
        "ps",
        "whoami",
        "id",
        "hostname",
        "which",
        "free",
    ],
    # Extra commands that change things (repo helpers such as `envset`).
    "mutating_commands": [],
    # Repo wrappers around redis-cli / psql / mc; classified like the real client.
    "redis_clients": [],
    "sql_clients": [],
    "minio_clients": [],
}
LIST_KEYS = {k for k, v in DEFAULTS.items() if isinstance(v, list)}

SEPARATORS = {";", "&&", "||", "|", "&", "(", ")", "|&", ";;"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
INTERPRETERS = {"python", "python3", "node", "ruby", "perl", "php", "deno"}
# Shell words that start a segment without being the program.
KEYWORDS = {
    "if",
    "then",
    "elif",
    "else",
    "fi",
    "do",
    "done",
    "while",
    "until",
    "for",
    "!",
    "{",
    "}",
    "case",
    "esac",
    "select",
}
# Prefixes that run the rest of the line as a command.
WRAPPERS = {
    "env",
    "sudo",
    "doas",
    "nohup",
    "time",
    "timeout",
    "nice",
    "ionice",
    "command",
    "exec",
    "stdbuf",
    "xargs",
    "builtin",
}
# Wrapper options that take a value (`sudo -u deploy git push`).
WRAPPER_OPTS_WITH_VALUE = {
    "sudo": {"-u", "-g", "-C", "-D", "-h", "-p", "-r", "-t", "-U", "--user", "--group"},
    "doas": {"-u", "-C"},
    "env": {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"},
    "timeout": {"-s", "--signal", "-k", "--kill-after"},
    "nice": {"-n", "--adjustment"},
    "ionice": {"-c", "-n", "-p"},
    "xargs": {"-I", "-L", "-n", "-P", "-s", "-d", "-E", "-a"},
    "stdbuf": {"-i", "-o", "-e"},
}
GIT_OPTS_WITH_VALUE = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--exec-path",
}
PUSH_OPTS_WITH_VALUE = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
GH_OPTS_WITH_VALUE = {"-R", "--repo"}
DOCKER_EXEC_OPTS_WITH_VALUE = {
    "-u",
    "--user",
    "-w",
    "--workdir",
    "-e",
    "--env",
    "--env-file",
    "--detach-keys",
    "--index",
}
MAKE_OPTS_WITH_VALUE = {
    "-C",
    "-f",
    "--file",
    "--directory",
    "-I",
    "-o",
    "-W",
    "--include-dir",
}
MESSAGE_OPTS = {
    "git": {"-m", "--message"},
    "gh": {"-t", "--title", "-b", "--body", "-n", "--notes"},
}

HEREDOC = re.compile(r"(?<!<)<<(?!<)-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
REDIRECT = re.compile(r"^(\d*)(>>?|<<<|<)(.*)$")
HARMLESS_OUT = {"/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty"}
HARMLESS_OUT_PREFIXES = ("/tmp/", "$TMPDIR/", "${TMPDIR}/")
MAX_COMMAND = 64 * 1024  # longer commands are blocked rather than slowly parsed

# .env, ./.env, app/.env.local, .envrc, .env.prod.bak-1; not sample.env
ENV_FILE = re.compile(r"(?<![\w.-])\.env(?:rc)?(?:\.[\w.-]+)?(?![\w/-])", re.I)
# prod.env, config/secrets.env; not sample.env / example.env / template.env
NAMED_ENV_FILE = re.compile(
    # A file name ends the word (space, quote, end); `process.env.X` or `process.env)` is code.
    r"(?<![\w.-])(?!(?:sample|example|template|process)\.env\b)[\w-]+\.env(?=$|[\s'\"])",
    re.I,
)
CREDENTIAL_FILE = re.compile(
    r"\.aws/credentials|\.git-credentials|\.netrc\b|\.docker/config\.json"
    r"|\.claude/\.credentials|\.kube/config|\.npmrc\b|\.pypirc\b|\.pgpass\b"
    r"|gh/hosts\.yml|/run/secrets/|\bcredentials[\w.-]*\.json\b"
    r"|service[-_]?account[\w.-]*\.json\b"
    r"|/\.ssh/(?![\w.-]*\.pub\b)(?!known_hosts\b)(?!config\b)"
    r"|\bid_(?:rsa|ed25519|ecdsa|dsa)\b(?!\.pub)"
    r"|(?<![\w.-])(?![\w.-]*(?:cert|chain|pub)[\w.-]*\.pem\b)[\w.-]+\.pem\b"
    r"|\.p12\b|\.pfx\b|\.jks\b|\.keystore\b|(?<![\w.-])[\w.-]+\.key\b",
    re.I,
)
PROC_ENVIRON = re.compile(r"/proc/[^/\s]*/environ")
ASSIGNED = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=\"?\$\(\s*$")
LITERAL_URL_LOGIN = re.compile(r"://[^\s/:@'\"$<{]+:[^\s/@'\"$<{]+@")
LITERAL_PASSWORD_OPT = re.compile(r"--pass(?:word)?[= ]+(?![\"']?\$)\S+")
ENV_DUMP_WORD = re.compile(r"(?:^|[\s;|&(])(?:env|printenv)(?:$|[\s;|&)])")
SECRET_WORDS = r"(?:PASSWORD|PASSWD|SECRET|TOKEN|API_KEY|ACCESS_KEY|PRIVATE_KEY|DATABASE_URL|_DSN|CREDENTIAL)"
# $NAME / ${NAME} of a secret-looking variable; not \$NAME, ${#NAME} or ${NAME:+x}.
SECRET_REF = r"(?<!\\)\$\{?[A-Z_]*" + SECRET_WORDS + r"[A-Z0-9_]*(?![A-Z0-9_])(?!:[+?])"
SECRET_VAR = re.compile(SECRET_REF)
SECRET_ECHO = re.compile(r"(?:^|[\s;|&('\"])(?:echo|printf)\b[^;|&\n]*" + SECRET_REF)
NODE_PRINT_ENV = re.compile(
    r"(?:^|\s)(?:-p|--print)\s+['\"]?process\.env['\"]?(?:\s|$)"
)
ENV_PRINT = re.compile(
    r"print\(\s*(?:dict\(\s*)?os\.environ\s*\)?\s*\)"
    r"|in\s+os\.environ(?:\.items\(\))?\s*:\s*print\("  # for k in os.environ: print(...)
    r"|json\.dumps\(\s*(?:dict\(\s*)?os\.environ"
    r"|print\((?!\s*(?:bool|len)\()[^)\n]*(?:os\.environ|os\.getenv)[^)\n]*"
    + SECRET_WORDS
    + r"|console\.(?:log|dir|info)\(\s*process\.env\s*\)"
    r"|console\.(?:log|dir|info)\([^)\n]*process\.env\.[A-Z_]*"
    + SECRET_WORDS
    + r"|JSON\.stringify\(\s*process\.env"
    r"|console\.(?:log|dir|info|table)\(\s*Object\.(?:entries|values)\(\s*process\.env"
)
ALEMBIC_READ = re.compile(r"\balembic\s+(current|heads|history|show|branches)\b")
ALEMBIC_WRITE = re.compile(r"\balembic\s+(upgrade|downgrade|stamp|revision|merge)\b")

# Commands that may name a secret file without reading it.
NAME_ONLY = {"ls", "test", "[", "[[", "stat", "echo", "printf", "touch"}
GIT_NAME_ONLY = {"check-ignore", "status", "ls-files"}
COMPOSE_CONFIG_SAFE = {
    "-q",
    "--quiet",
    "--services",
    "--volumes",
    "--images",
    "--profiles",
    "--networks",
}
READ_ONLY_DOCKER = {
    "ps",
    "logs",
    "images",
    "version",
    "info",
    "stats",
    "top",
    "inspect",
    "events",
    "port",
    "history",
    "search",
}
DOCKER_MANAGEMENT = {
    "container",
    "image",
    "network",
    "volume",
    "system",
    "context",
    "buildx",
    "plugin",
    "node",
    "service",
    "stack",
    "secret",
    "config",
}
READ_ONLY_DOCKER_SUB = {
    "ls",
    "list",
    "inspect",
    "df",
    "history",
    "ps",
    "logs",
    "top",
    "stats",
    "port",
    "info",
    "events",
}
READ_ONLY_COMPOSE = {
    "ps",
    "logs",
    "config",
    "convert",
    "images",
    "version",
    "ls",
    "top",
    "port",
    "events",
}
COMPOSE_CHANGING = {
    "up",
    "down",
    "build",
    "restart",
    "stop",
    "start",
    "rm",
    "pull",
    "create",
    "run",
    "exec",
    "kill",
    "pause",
    "unpause",
    "cp",
    "push",
    "watch",
}
READ_ONLY_GIT = {
    "status",
    "log",
    "diff",
    "show",
    "fetch",
    "rev-parse",
    "branch",
    "ls-files",
    "check-ignore",
    "describe",
    "remote",
    "blame",
    "shortlog",
    "rev-list",
    "merge-base",
    "config",
    "grep",
    "reflog",
    "ls-remote",
    "show-ref",
    "cat-file",
    "for-each-ref",
    "name-rev",
    "count-objects",
    "var",
    "version",
    "help",
    "whatchanged",
    "tag",
    "worktree",
    "stash",
}
MUTATING_GIT_BRANCH = {
    "-d",
    "-D",
    "-m",
    "-M",
    "--delete",
    "--move",
    "-f",
    "--force",
    "-c",
    "-C",
    "--set-upstream-to",
    "-u",
    "--unset-upstream",
}
GIT_CONFIG_WRITE = {
    "--unset",
    "--unset-all",
    "--add",
    "--replace-all",
    "--rename-section",
    "--remove-section",
    "-e",
    "--edit",
}
READ_ONLY_GH = {
    ("pr", "view"),
    ("pr", "list"),
    ("pr", "checks"),
    ("pr", "diff"),
    ("pr", "status"),
    ("run", "list"),
    ("run", "view"),
    ("run", "watch"),
    ("repo", "view"),
    ("repo", "list"),
    ("release", "list"),
    ("release", "view"),
    ("issue", "view"),
    ("issue", "list"),
    ("issue", "status"),
    ("workflow", "list"),
    ("workflow", "view"),
    ("label", "list"),
    ("secret", "list"),
    ("variable", "list"),
    ("cache", "list"),
    ("gist", "list"),
    ("auth", "status"),
    ("search", None),
    ("api", None),
}
MUTATING_PLAIN = {
    "rm",
    "mv",
    "cp",
    "tee",
    "dd",
    "chmod",
    "chown",
    "kill",
    "pkill",
    "killall",
    "systemctl",
    "service",
    "reboot",
    "shutdown",
    "apt",
    "apt-get",
    "dpkg",
    "pip",
    "pip3",
    "npm",
    "pnpm",
    "yarn",
    "bun",
    "npx",
    "uv",
    "alembic",
    "mkdir",
    "rmdir",
    "ln",
    "truncate",
    "crontab",
    "ufw",
    "iptables",
    "useradd",
    "usermod",
    "scp",
    "rsync",
    "ssh",
    "mc",
    "sudo",
    "doas",
    "install",
    "patch",
    "unzip",
    "wget",
    "terraform",
    "helm",
    "kubectl",
    "aws",
    "gcloud",
    "az",
    "mysql",
    "mariadb",
    "mongosh",
    "mongo",
    "pm2",
    "supervisorctl",
    "certbot",
    "at",
}
REDIS_READ = {
    "ping",
    "info",
    "xlen",
    "xinfo",
    "xrange",
    "xrevrange",
    "xpending",
    "llen",
    "lrange",
    "get",
    "type",
    "ttl",
    "exists",
    "scan",
    "dbsize",
    "memory",
    "client",
    "slowlog",
    "config",
}
REDIS_READ_FLAGS = {"--scan", "--bigkeys", "--memkeys", "--stat", "--latency"}
MINIO_READ = {"ls", "stat", "du", "find", "tree", "ping", "admin"}
PACKAGE_MANAGERS = {"npm", "pnpm", "yarn", "bun"}
PACKAGE_READ = {
    "ls",
    "list",
    "outdated",
    "view",
    "info",
    "why",
    "explain",
    "help",
    "config",
    "audit",
    "doctor",
    "root",
    "bin",
    "prefix",
    "whoami",
    "search",
}
SYSTEMCTL_READ = {
    "status",
    "show",
    "list-units",
    "list-unit-files",
    "list-timers",
    "is-active",
    "is-enabled",
    "is-failed",
    "cat",
}
KUBECTL_READ = {
    "get",
    "describe",
    "logs",
    "top",
    "version",
    "api-resources",
    "api-versions",
    "explain",
    "cluster-info",
    "auth",
    "config",
}
TERRAFORM_READ = {
    "plan",
    "show",
    "validate",
    "fmt",
    "version",
    "providers",
    "graph",
    "output",
}
HELM_READ = {
    "list",
    "ls",
    "status",
    "history",
    "template",
    "lint",
    "version",
    "search",
    "show",
    "env",
    "repo",
}
SQL_WRITE = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|vacuum|reindex|rename)\b",
    re.I,
)
CURL_WRITE = re.compile(
    r"(?:^|\s)(?:-X\s*(?!GET\b|HEAD\b)\w+|--request\s+(?!GET\b|HEAD\b)\w+|-[a-zA-Z]*[dFT]\b"
    r"|--data\S*|--form\b|--upload-file|--json\b|-[a-zA-Z]*X\s*(?!GET\b|HEAD\b)[A-Z]+)"
)
# Files that set the guard's own policy. In managed mode the agent may read
# them but not change them (TAPWAY_GUARD_MANAGED=1, set by the server template).
POLICY_FILE = re.compile(
    r"(?:^|[/'\"\s=])\.claude/(?:tool-guard\.json|settings(?:\.local)?\.json)(?![\w.-])"
)
WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
POLICY_READERS = NAME_ONLY | {
    "cat",
    "less",
    "more",
    "head",
    "tail",
    "grep",
    "egrep",
    "rg",
    "jq",
    "diff",
    "wc",
    "file",
}
FILE_KEYS = ("file_path", "path", "notebook_path", "glob", "pattern")


class BlockedError(Exception):
    """The command must not run."""


class AskError(Exception):
    """The command may run, but only with a human's explicit approval."""


class ConfigError(Exception):
    """.claude/tool-guard.json is unreadable or has the wrong shape."""


# --- config -------------------------------------------------------------


def project_dir(payload: dict) -> Path:
    for candidate in (os.environ.get("CLAUDE_PROJECT_DIR"), payload.get("cwd")):
        if candidate:
            return Path(candidate)
    return Path.cwd()


def load_config(root: Path) -> dict:
    config = {k: list(v) if isinstance(v, list) else v for k, v in DEFAULTS.items()}
    path = root / CONFIG_NAME
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ConfigError(f"{CONFIG_NAME}: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"{CONFIG_NAME} must be a JSON object")
        for key, value in data.items():
            if key.startswith("_"):  # "_comment" and friends
                continue
            if key not in DEFAULTS:
                raise ConfigError(f"{CONFIG_NAME}: unknown key {key!r}")
            expected = type(DEFAULTS[key])
            if not isinstance(value, expected):
                raise ConfigError(
                    f"{CONFIG_NAME}: {key!r} must be a {expected.__name__}"
                )
            if key in LIST_KEYS and not all(isinstance(v, str) for v in value):
                raise ConfigError(f"{CONFIG_NAME}: {key!r} must list strings")
            if key == "pr_flow" and not all(
                isinstance(k, str) and isinstance(v, str) for k, v in value.items()
            ):
                raise ConfigError(
                    f"{CONFIG_NAME}: 'pr_flow' maps branch names to branch names"
                )
            config[key] = value
    config["_managed"] = os.environ.get("TAPWAY_GUARD_MANAGED") == "1"
    if config["_managed"]:
        # Managed machines (servers): a repo config may add rules, never remove
        # them. The agent can edit a repo, so the repo cannot switch these off.
        config["protect_env_files"] = True
        config["protected_branches"] = sorted(
            set(DEFAULTS["protected_branches"]) | set(config["protected_branches"])
        )
        config["allowed_env_templates"] = [
            t
            for t in config["allowed_env_templates"]
            if t in DEFAULTS["allowed_env_templates"]
        ]
    if os.environ.get("TAPWAY_GUARD_ASK") == "1":
        config["ask_before_changes"] = True
    try:
        config["_secret_paths"] = [re.compile(p) for p in config["secret_paths"]]
        config["_read_only_scripts"] = [
            re.compile(p) for p in config["read_only_scripts"]
        ]
    except re.error as exc:
        raise ConfigError(f"{CONFIG_NAME}: bad regex ({exc})") from exc
    config["_mutating"] = MUTATING_PLAIN | set(config["mutating_commands"])
    config["_project"] = str(root)
    if config["secret_getters"]:
        names = "|".join(re.escape(g) for g in config["secret_getters"])
        config["_getters"] = re.compile(rf"(?<![\w-])({names})(?![\w-])")
    else:
        config["_getters"] = None
    return config


# --- parsing ------------------------------------------------------------


def join_continuations(cmd: str) -> str:
    """`git push \\<newline> --force` is one command, not two."""
    return re.sub(r"\\\r?\n", " ", cmd)


def split_heredocs(cmd: str) -> tuple[str, list[tuple[str, str, bool]]]:
    """Remove heredoc bodies; return (command, [(line before <<, body, quoted)])."""
    out, bodies, lines, i = [], [], cmd.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        matches = list(HEREDOC.finditer(line))
        out.append(HEREDOC.sub(" ", line))
        for match in matches:
            end, body = match.group(2), []
            i += 1
            while i < len(lines) and lines[i].strip() != end:
                body.append(lines[i])
                i += 1
            bodies.append(
                (line[: match.start()], "\n".join(body), bool(match.group(1)))
            )
        i += 1
    return "\n".join(out), bodies


def strip_heredocs(cmd: str) -> str:
    return split_heredocs(cmd)[0]


def strip_comments(cmd: str) -> str:
    """Drop `# ...` where bash would: unquoted, at the start of a word."""
    out, i, quote, n = [], 0, None, len(cmd)
    while i < n:
        c = cmd[i]
        if quote:
            out.append(c)
            if c == "\\" and quote == '"' and i + 1 < n:
                out.append(cmd[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c == "\\" and i + 1 < n:
            out.append(c + cmd[i + 1])
            i += 2
            continue
        if c in "'\"":
            quote = c
        elif c == "#" and (i == 0 or cmd[i - 1] in " \t\n;|&("):
            end = cmd.find("\n", i)
            if end == -1:
                break
            i = end
            continue
        out.append(c)
        i += 1
    return "".join(out)


ASSIGNED_BEFORE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=\"?$")


SUBST = "$__SUBST__"  # stands in for a $(...) the outer pass must not re-read


def substitutions(cmd: str) -> list[tuple[str, bool, int, int]]:
    """Every $(...) and `...` body bash would run (unquoted or in double
    quotes; not in single quotes), and whether it is assigned straight to a
    variable (VAR=$(...))."""
    found, i, n, single = [], 0, len(cmd), False
    while i < n:
        c = cmd[i]
        if single:
            single = c != "'"
            i += 1
            continue
        if c == "\\":
            i += 2
            continue
        if c == "'":
            single = True
            i += 1
            continue
        if c not in "$`":
            i += 1
            continue
        assigned = bool(ASSIGNED_BEFORE.search(cmd[max(0, i - 200) : i]))
        if cmd.startswith("$(", i) and not cmd.startswith("$((", i):
            depth, j = 1, i + 2
            while j < n and depth:
                depth += {"(": 1, ")": -1}.get(cmd[j], 0)
                j += 1
            found.append(
                (cmd[i + 2 : j - 1] if depth == 0 else cmd[i + 2 :], assigned, i, j)
            )
            i = j
            continue
        if cmd[i] == "`":
            j = cmd.find("`", i + 1)
            end = n if j == -1 else j + 1
            found.append(
                (cmd[i + 1 :] if j == -1 else cmd[i + 1 : j], assigned, i, end)
            )
            i = end
            continue
        i += 1
    return found


def check_substitutions(
    text: str, config: dict, state: dict, depth: int
) -> tuple[bool, str]:
    """Check every substitution as its own command (in a subshell: a cd inside
    stays inside); return (changes, text with the substitutions masked)."""
    changed, masked, last = False, [], 0
    for body, assigned, start, end in substitutions(text):
        # VAR=$(envget KEY) / VAR=$(gh auth token) hold a secret without printing it.
        sub_config = dict(config, _getters=None, _captured=True) if assigned else config
        changed |= check_command(body, sub_config, dict(state), depth + 1)
        masked.append(text[last:start] + SUBST)
        last = end
    masked.append(text[last:])
    return changed, "".join(masked)


def tokenize(cmd: str) -> list[str]:
    """Tokens of a command whose heredocs and comments are already removed."""
    cmd = re.sub(r"\d*>&(?:\d+|-)", " ", cmd)  # 2>&1, >&2: fd plumbing
    cmd = re.sub(r"&>>?", " > ", cmd)  # &>file
    cmd = cmd.replace("$(", " ( ").replace("`", " ; ").replace("\n", " ; ")
    lexer = shlex.shlex(cmd, posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError as exc:  # unbalanced quotes
        raise BlockedError(
            f"could not parse the command ({exc}); refusing to guess"
        ) from exc


def split_commands(tokens: list[str]) -> list[list[str]]:
    commands, current = [], []
    for tok in tokens:
        if tok in SEPARATORS:
            if current:
                commands.append(current)
            current = []
        else:
            current.append(tok)
    if current:
        commands.append(current)
    return commands


def drop_assignments(argv: list[str]) -> list[str]:
    while argv and (ASSIGNMENT.match(argv[0]) or argv[0] in KEYWORDS):
        argv = argv[1:]
    return argv


def unwrap(argv: list[str]) -> list[str]:
    """The command a wrapper runs: `sudo -u x env A=1 timeout 5 git push` -> `git push`.

    Only the wrapper's own options (and their values) are dropped; the inner
    command keeps its options (e.g. `--force`).
    """
    wrapper = None
    while argv:
        word = argv[0]
        name = word.rsplit("/", 1)[-1]
        if ASSIGNMENT.match(word) or word in KEYWORDS:
            argv = argv[1:]
        elif name in WRAPPERS:
            wrapper, argv = name, argv[1:]
        elif word.startswith("-") and word != "-" and wrapper:
            takes_value = word in WRAPPER_OPTS_WITH_VALUE.get(wrapper, set())
            argv = argv[2:] if takes_value else argv[1:]
        elif wrapper in {"timeout", "nice"} and re.match(r"^[0-9.]+[smhd]?$", word):
            argv = argv[1:]
        else:
            break
    return argv


def split_redirects(argv: list[str]) -> tuple[list[str], list[str], set[int]]:
    """(argv without redirections, output targets, indices of output targets)."""
    args, outs, out_idx, i = [], [], set(), 0
    while i < len(argv):
        match = REDIRECT.match(argv[i])
        if match and not (i == 0 and match.group(2) == "<<<"):
            op, target, target_idx = match.group(2), match.group(3), i
            if not target and i + 1 < len(argv):
                target, target_idx = argv[i + 1], i + 1
                i += 1
            if op in (">", ">>"):
                outs.append(target)
                out_idx.add(target_idx)
            i += 1
            continue
        args.append(argv[i])
        i += 1
    return args, outs, out_idx


def program(argv: list[str]) -> str:
    return argv[0].rsplit("/", 1)[-1] if argv else ""


# --- secrets ------------------------------------------------------------


def names_env_file(text: str, config: dict) -> bool:
    if not config["protect_env_files"]:
        return False
    for match in ENV_FILE.finditer(text):
        parts = [
            x.lower() for x in match.group(0).split(".")[2:]
        ]  # .env.local.example -> [local, example]
        if not set(parts) & set(config["allowed_env_templates"]):
            return True
    return bool(NAMED_ENV_FILE.search(text))


def names_credential(text: str, config: dict) -> bool:
    return bool(
        CREDENTIAL_FILE.search(text)
        or PROC_ENVIRON.search(text)
        or any(p.search(text) for p in config["_secret_paths"])
    )


def names_secret_path(text: str, config: dict) -> bool:
    return names_env_file(text, config) or names_credential(text, config)


def check_raw(raw: str, config: dict) -> None:
    """Checks on the whole command text (heredoc bodies and comments removed)."""
    getters = config["_getters"]
    if getters is not None:
        for match in getters.finditer(raw):
            if raw[match.end() : match.end() + 2] == "()":  # a function definition
                continue
            if not ASSIGNED.search(raw[: match.start()]):
                raise BlockedError(
                    f"`{match.group(1)}` prints a secret; capture it instead: "
                    f"VAR=$({match.group(1)} ...)"
                )
    if PROC_ENVIRON.search(raw):
        raise BlockedError("reading a process environment exposes its secrets")
    if LITERAL_URL_LOGIN.search(raw):
        raise BlockedError(
            "a password inside a URL; read it from the environment into a variable"
        )
    if LITERAL_PASSWORD_OPT.search(raw):
        raise BlockedError("a literal --password on the command line")
    if SECRET_ECHO.search(re.sub(r"'[^']*'", "''", raw)):  # '...' is literal text
        raise BlockedError(
            'echoing a secret variable prints it; test it with [ -n "$VAR" ] instead'
        )


def exempt_indices(head: str, argv: list[str]) -> set[int]:
    """Argument positions that name a file without reading it: commit/PR
    messages, grep patterns, and --env-file values (loaded, not printed)."""
    exempt: set[int] = set()
    opts = MESSAGE_OPTS.get(head, set())
    pattern_given = any(a in {"-e", "--regexp", "-f", "--file"} for a in argv)
    pattern_seen = False
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg in opts or arg == "--env-file":
            exempt.add(i + 1)
            i += 2
            continue
        if any(arg.startswith(o + "=") for o in opts) or arg.startswith("--env-file="):
            exempt.add(i)
        elif head in {"grep", "egrep", "fgrep", "rg"}:
            if arg in {"--include", "--exclude", "--exclude-dir", "-g", "--glob"}:
                exempt.add(i + 1)
                i += 2
                continue
            if arg.startswith(
                ("--include=", "--exclude=", "--exclude-dir=", "--glob=")
            ):
                exempt.add(i)
                i += 1
                continue
            if arg in {"-e", "--regexp"}:
                exempt.add(i + 1)
                i += 2
                continue
            if not arg.startswith("-") and not pattern_given and not pattern_seen:
                exempt.add(i)
                pattern_seen = True
        i += 1
    return exempt


def names_policy_file(text: str) -> bool:
    return bool(POLICY_FILE.search(text.replace("\\", "/")))


def check_policy_tokens(
    head: str, argv: list[str], out_idx: set[int], config: dict
) -> None:
    """Managed mode: the guard's policy files are read-only for the agent."""
    if not config.get("_managed"):
        return
    hits = [i for i, t in enumerate(argv) if names_policy_file(t)]
    if not hits:
        return
    rest = argv[1:]
    reading = head in POLICY_READERS or (
        head == "git"
        and rest
        and rest[0] in READ_ONLY_GIT
        and rest[0] not in {"config", "stash"}
    )
    if (
        reading
        and not out_idx.intersection(hits)
        and not (head == "sed" and any(a.startswith("-i") for a in rest))
    ):
        return
    raise BlockedError(
        "the guard's policy (.claude/tool-guard.json, .claude/settings*.json) is managed on this machine"
    )


def check_secret_tokens(
    head: str, argv: list[str], out_idx: set[int], config: dict
) -> None:
    exempt = exempt_indices(head, argv) | out_idx  # writing to .env leaks nothing
    env_hits = [
        i for i, t in enumerate(argv) if i not in exempt and names_env_file(t, config)
    ]
    cred_hits = [
        i for i, t in enumerate(argv) if i not in exempt and names_credential(t, config)
    ]
    if not env_hits and not cred_hits:
        return
    rest = argv[1:]
    if head in NAME_ONLY:
        return
    if (
        head == "git"
        and rest
        and (rest[0] in GIT_NAME_ONLY or (rest[0] == "rm" and "--cached" in rest))
    ):
        return
    target_dir = any(
        a in {"-t", "--target-directory"} or a.startswith("--target-directory=")
        for a in argv
    )
    if head in {"cp", "install"} and not cred_hits and not target_dir:
        positional = [i for i, t in enumerate(argv) if i and not t.startswith("-")]
        if positional and env_hits == [positional[-1]]:  # cp .env.example .env
            return
    if cred_hits:
        raise BlockedError("credential files are off limits")
    raise BlockedError(f"direct access to a secrets file; {config['secret_hint']}")


# --- protected branches -------------------------------------------------


def git_toplevel(cwd: str | None) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", cwd or ".", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return str(Path(out.stdout.strip()).resolve()) if out.returncode == 0 else None


def config_for(cwd: str, config: dict) -> dict:
    """The config of the repo a `cd` lands in: its own .claude/tool-guard.json
    (or the defaults). Asking never switches off on the way."""
    top = git_toplevel(cwd)
    if top is None or top == git_toplevel(config["_project"]):
        return config
    try:
        other = load_config(Path(top))
    except ConfigError as exc:
        raise BlockedError(f"{top}: fix {exc}") from exc
    other["ask_before_changes"] = (
        other["ask_before_changes"] or config["ask_before_changes"]
    )
    return other


def git_branch(cwd: str | None) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", cwd or ".", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def is_local_branch(name: str, cwd: str | None) -> bool:
    try:
        out = subprocess.run(
            [
                "git",
                "-C",
                cwd or ".",
                "rev-parse",
                "--verify",
                "--quiet",
                f"refs/heads/{name}",
            ],
            capture_output=True,
            timeout=5,
        )
        return out.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def check_push(args: list[str], branch: str, protected: set[str]) -> None:
    positional, skip = [], False
    for arg in args:
        if skip:
            skip = False
            continue
        if arg in PUSH_OPTS_WITH_VALUE:
            skip = True
            continue
        if arg.startswith("--"):
            name = arg.split("=", 1)[0]
            if name.startswith("--force") or name in {"--mirror", "--all", "--tags"}:
                raise BlockedError(
                    f"`git push {name}` is not allowed (no force-push, no bulk ref updates)."
                )
            continue
        if arg.startswith("-") and arg != "-":
            if "f" in arg[1:]:
                raise BlockedError("no force-push.")
            continue
        positional.append(arg)

    refspecs = positional[1:]
    if not refspecs:
        if branch in protected:
            raise BlockedError(
                f"you are on {branch}; this push would update it. Push a feature branch and open a PR."
            )
        return
    for spec in refspecs:
        if spec.startswith("+"):
            raise BlockedError("a `+refspec` is a force-push.")
        src, _, dst = spec.partition(":")
        target = (dst or src).removeprefix("refs/heads/")
        # HEAD, @, or a computed name ("$(git branch --show-current)") is the current branch.
        if target in ("HEAD", "@") or any(c in target for c in "$(`"):
            target = branch
        if target in protected:
            raise BlockedError(
                f"no direct push to {target}. Push a feature branch and open a PR."
            )


def branch_after_checkout(
    args: list[str], branch: str, cwd: str | None, protected: set[str]
) -> str:
    """Branch a checkout/switch leaves us on. `git checkout main -- file` and
    `git checkout file.py` restore files and keep the branch."""
    if "--" in args:
        return branch
    for flag in ("-b", "-B", "-c", "-C", "--create", "--force-create", "--orphan"):
        if flag in args and args.index(flag) + 1 < len(args):
            return args[args.index(flag) + 1]
    targets = [a for a in args if not a.startswith("-")]
    if targets and (targets[0] in protected or is_local_branch(targets[0], cwd)):
        return targets[0]
    return branch


def git_subcommand(argv: list[str]) -> tuple[int, str | None, bool]:
    """(index of the subcommand, the -C directory if any, whether -C was used)."""
    cwd, other, i = None, False, 1
    while i < len(argv) and argv[i].startswith("-"):
        if argv[i] in GIT_OPTS_WITH_VALUE and i + 1 < len(argv):
            if argv[i] == "-C":
                cwd, other = argv[i + 1], True
            i += 2
        else:
            i += 1
    return i, cwd, other


def unresolved(path: str) -> bool:
    """A path the guard cannot know before the shell expands it."""
    return path == "-" or any(c in path for c in "$`(")


def check_git_branches(argv: list[str], state: dict, config: dict) -> None:
    protected = set(config["protected_branches"])
    i, other_cwd, other_repo = git_subcommand(argv)
    if other_repo and unresolved(other_cwd or ""):  # git -C "$PWD": assume this repo
        other_cwd, other_repo = None, False
    if i >= len(argv):
        return
    cwd = other_cwd if other_repo else state["cwd"]
    branch = git_branch(cwd) if other_repo else state["branch"]
    sub, args = argv[i], argv[i + 1 :]
    if sub in ("checkout", "switch"):
        new = branch_after_checkout(args, branch, cwd, protected)
        if not other_repo:
            state["branch"] = new
    elif sub == "commit":
        if branch in protected:
            raise BlockedError(
                f"no commits on {branch}. Move the work to a feature branch first."
            )
    elif sub == "push":
        check_push(args, branch, protected)


def option_value(args: list[str], names: tuple[str, ...]) -> str | None:
    for i, arg in enumerate(args):
        for name in names:
            if arg == name and i + 1 < len(args):
                return args[i + 1]
            if arg.startswith(name + "="):
                return arg.split("=", 1)[1]
    return None


def gh_words(args: list[str]) -> list[str]:
    """gh's positional words, skipping global options with values (-R o/r)."""
    words, skip = [], False
    for arg in args:
        if skip:
            skip = False
        elif arg in GH_OPTS_WITH_VALUE:
            skip = True
        elif not arg.startswith("-"):
            words.append(arg)
    return words


def check_pr_create(argv: list[str], state: dict, config: dict) -> None:
    if gh_words(argv[1:])[:2] != ["pr", "create"]:
        return
    args = argv[argv.index("create") + 1 :]
    base = option_value(args, ("--base", "-B"))
    head = option_value(args, ("--head", "-H")) or state["branch"]
    if base is None:
        if config["require_pr_base"]:
            raise BlockedError(
                "pass --base explicitly; this repo's default branch is not the PR target."
            )
        return
    required = config["pr_flow"].get(base)
    if required is not None and head != required:
        raise BlockedError(f"PRs into {base} come only from {required}.")


# --- what changes things ------------------------------------------------


def runs_read_only_script(args: list[str], config: dict) -> bool:
    text = " ".join(args)
    return any(p.search(text) for p in config["_read_only_scripts"])


def check_segment(argv: list[str], config: dict) -> bool:
    """Raise BlockedError on a leak; return True if the command changes things."""
    argv = drop_assignments(argv)
    if not argv:
        return False
    args, outs, out_idx = split_redirects(argv)
    writes = any(
        t not in HARMLESS_OUT and not t.startswith(HARMLESS_OUT_PREFIXES) for t in outs
    )
    head = program(argv)
    check_secret_tokens(head, argv, out_idx, config)
    check_policy_tokens(head, argv, out_idx, config)
    if not args:  # only redirections, e.g. `> file`
        return writes
    rest = args[1:]

    if head == "command" and rest[:1] in (["-v"], ["-V"]):
        return writes
    runs_inner = head in WRAPPERS and head != "env"
    env_runs = head == "env" and bool(unwrap(args))
    if runs_inner or env_runs:
        inner = unwrap(args)
        return check_segment(inner, config) or head in config["_mutating"] or writes

    captured = config.get("_captured", False)
    if head == "printenv" and captured and rest:  # VAR=$(printenv NAME)
        return writes
    if head in {"printenv", "env"}:
        raise BlockedError("dumping the environment exposes secrets")
    if head in {"set", "export", "declare", "typeset"} and (
        not rest or rest[0] in {"-p", "-x", "-px"}
    ):
        raise BlockedError("dumping shell variables exposes secrets")
    if head in INTERPRETERS:
        check_code(" ".join(rest))
    if head == "ssh":  # the remote command line runs in a shell over there
        check_container_command(rest)
    check_secret_commands(head, rest, captured)
    return writes or changes(head, rest, args, config)


def check_code(code: str) -> None:
    """Inline code (python -c, node -e/-p, a container command line)."""
    if ENV_PRINT.search(code) or NODE_PRINT_ENV.search(code):
        raise BlockedError("printing the process environment exposes its secrets")


def recursive_grep_reads_env(head: str, rest: list[str]) -> bool:
    """grep -r / rg --no-ignore over the repo root also reads .env files."""
    pairs, i = [], 0
    while i < len(rest):
        a = rest[i]
        for opt in ("--include", "--exclude", "--glob", "-g"):
            if a == opt and i + 1 < len(rest):
                pairs.append((opt, rest[i + 1].strip("'\"")))
                i += 1
            elif a.startswith(opt + "="):
                pairs.append((opt, a.split("=", 1)[1].strip("'\"")))
        i += 1
    if head == "rg":
        if not any(re.match(r"^-u+$", a) or a.startswith("--no-ignore") for a in rest):
            return False  # rg skips gitignored files, .env included
        excluded = any(
            v.startswith("!") and "env" in v for o, v in pairs if o in {"--glob", "-g"}
        )
        return not excluded
    if not any(
        a in {"-r", "-R", "--recursive"} or re.match(r"^-[a-zA-Z]*[rR]", a)
        for a in rest
    ):
        return False
    excluded = any(o == "--exclude" and "env" in v for o, v in pairs)
    included = any(
        o == "--include" and v not in {"*", "*.*"} and "env" not in v for o, v in pairs
    )
    if excluded or included:
        return False
    skip_values = {
        "--include",
        "--exclude",
        "--exclude-dir",
        "-e",
        "--regexp",
        "-f",
        "--file",
        "-m",
        "-A",
        "-B",
        "-C",
    }
    positional, skip = [], False
    for a in rest:
        if skip:
            skip = False
        elif a in skip_values:
            skip = True
        elif not a.startswith("-"):
            positional.append(a)
    pattern_given = any(a in {"-e", "--regexp", "-f", "--file"} for a in rest)
    paths = positional if pattern_given else positional[1:]
    return not paths or any(p.rstrip("/") in {".", "", "*", "~", ".."} for p in paths)


def check_secret_commands(head: str, rest: list[str], captured: bool = False) -> None:
    """Commands whose only job here would be to print a secret. When the
    output is captured into a variable (VAR=$(...)), credential printers are
    fine: nothing reaches the transcript."""
    words = [a for a in rest if not a.startswith("-")]
    if head in {"grep", "egrep", "fgrep", "rg"} and recursive_grep_reads_env(
        head, rest
    ):
        raise BlockedError(
            "`grep -r` over the repo also reads .env; use the Grep tool, rg, or --exclude='.env*'"
        )
    if head == "curl" and any(
        a in {"-u", "--user"} or a.startswith(("-u", "--user=")) for a in rest
    ):
        raise BlockedError("curl -u puts the password in argv; pass it with -K <(...)")
    if head == "redis-cli" and any(a in {"-a", "--pass", "--askpass"} for a in rest):
        raise BlockedError("redis-cli -a puts the password in argv; use REDISCLI_AUTH")
    if head in {"mysql", "mariadb", "mysqldump"} and any(
        re.match(r"^-p\S", a) for a in rest
    ):
        raise BlockedError(
            "mysql -p<password> puts the password in argv; use MYSQL_PWD or an option file"
        )
    if head == "mc" and rest[:2] == ["alias", "set"]:
        raise BlockedError("mc alias set puts keys in argv; use MC_HOST_<alias> via -e")
    if captured:
        return
    if head == "gh" and gh_words(rest)[:2] == ["auth", "token"]:
        raise BlockedError("`gh auth token` prints a credential")
    if (
        head == "gh"
        and gh_words(rest)[:2] == ["auth", "status"]
        and any(a in {"-t", "--show-token"} for a in rest)
    ):
        raise BlockedError("`gh auth status --show-token` prints a credential")
    if head == "aws" and (
        words[:2] in (["configure", "get"], ["configure", "export-credentials"])
        or words[1:2] == ["get-secret-value"]
        or (
            words[1:2] in (["get-parameter"], ["get-parameters"])
            and "--with-decryption" in rest
        )
    ):
        raise BlockedError("this aws command prints a secret")
    if (
        head == "kubectl"
        and words[:1] == ["get"]
        and words[1:2]
        and words[1].startswith("secret")
        and any(
            a in {"-o", "--output"} or a.startswith(("-o", "--output=")) for a in rest
        )
    ):
        raise BlockedError(
            "`kubectl get secret -o ...` prints secret values; use describe"
        )
    if head == "kubectl" and words[:2] == ["config", "view"] and "--raw" in rest:
        raise BlockedError("`kubectl config view --raw` prints credentials")
    if head == "vault" and words[:1] in (["read"], ["kv"]):
        raise BlockedError("vault read prints secrets")
    if head == "ps" and any(
        not a.startswith("-") and "e" in a and a.isalpha() for a in rest
    ):
        raise BlockedError("`ps e` prints every process environment")
    if (
        head == "systemctl"
        and words[:1] == ["show"]
        and (
            not any(
                a in {"-p", "--property"} or a.startswith("--property=") for a in rest
            )
            or any("Environment" in a for a in rest)
        )
    ):
        raise BlockedError(
            "`systemctl show` prints unit environments; use -p <Property>"
        )


def changes(head: str, rest: list[str], args: list[str], config: dict) -> bool:
    """True if this (already secret-checked) command changes a server, repo or DB."""
    words = [a for a in rest if not a.startswith("-")]
    if head in {"docker", "docker-compose", "podman"}:
        return check_docker(head, rest, config)
    if head == "make":
        targets, skip = [], False
        for a in rest:
            if skip:
                skip = False
            elif a in MAKE_OPTS_WITH_VALUE:
                skip = True
            elif not a.startswith("-") and "=" not in a:
                targets.append(a)
        return not targets or any(
            t not in config["read_only_make_targets"] for t in targets
        )
    if head == "git":
        return git_changes(args)
    if head == "gh":
        gw = gh_words(rest)
        pair = tuple(gw[:2]) if len(gw) >= 2 else (gw[0], None) if gw else ()
        if pair and pair[0] == "api":
            if "graphql" in gw:
                return any("mutation" in a for a in rest)
            return any(
                a in {"-X", "--method", "-f", "-F", "--field", "--raw-field", "--input"}
                for a in rest
            )
        if pair and pair[0] == "search":
            return False
        return pair not in READ_ONLY_GH
    if head == "curl":
        return bool(CURL_WRITE.search(" ".join(rest)))
    if head == "wget":
        i = rest.index("-O") if "-O" in rest else -1
        to_stdout = any(a in {"-O-", "-qO-", "--spider"} for a in rest) or (
            i >= 0 and rest[i + 1 : i + 2] == ["-"]
        )
        return not to_stdout
    if head == "redis-cli" or head in config["redis_clients"]:
        if REDIS_READ_FLAGS.intersection(rest):
            return False
        return (
            not words
            or words[0].lower() not in REDIS_READ
            or (
                words[0].lower() == "config"
                and len(words) > 1
                and words[1].lower() != "get"
            )
        )
    if head in config["minio_clients"]:
        return (
            not words
            or words[0] not in MINIO_READ
            or (words[0] == "admin" and words[1:2] != ["info"])
        )
    if head in config["dev_tools"]:
        return False
    if head == "uv":
        if words[:1] == ["run"]:
            return not set(config["dev_tools"]).intersection(
                rest
            ) and not runs_read_only_script(rest, config)
        return not (
            not words
            or words[:1] == ["tree"]
            or words[:2] in (["pip", "list"], ["pip", "show"], ["pip", "freeze"])
        )
    if head in {"pip", "pip3"}:
        return not (
            not words
            or words[0] in {"list", "show", "freeze", "check", "help", "config"}
        )
    if head in PACKAGE_MANAGERS:
        scripts = config["read_only_package_scripts"]
        if not words or words[0] in PACKAGE_READ and "fix" not in words:
            return False
        if words[0] in {"run", "run-script"}:
            return words[1:2] == [] or words[1] not in scripts
        return words[0] not in scripts and words[0] not in {"test", "t"}
    if head == "alembic":
        return not ALEMBIC_READ.search("alembic " + " ".join(rest)) or bool(
            ALEMBIC_WRITE.search("alembic " + " ".join(rest))
        )
    if head in {"psql"} or head in config["sql_clients"]:
        return bool(SQL_WRITE.search(" ".join(rest))) or not any(
            a in {"-c", "--command"} for a in rest
        )
    if head in {"mysql", "mariadb"}:
        return bool(SQL_WRITE.search(" ".join(rest))) or not any(
            a in {"-e", "--execute"} for a in rest
        )
    if head == "sed":
        return any(a.startswith("-i") or a == "--in-place" for a in rest)
    if head == "find":
        return any(
            a
            in {"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprintf"}
            for a in rest
        )
    if head == "tar":
        if not rest or rest[0].startswith("--"):
            return "--list" not in rest
        return "t" not in rest[0]
    if head == "systemctl":
        return not words or words[0] not in SYSTEMCTL_READ
    if head == "kubectl":
        return not words or words[0] not in KUBECTL_READ
    if head == "terraform":
        return not words or words[0] not in TERRAFORM_READ
    if head == "helm":
        return (
            not words
            or words[0] not in HELM_READ
            or (words[0] == "repo" and words[1:2] not in ([], ["list"]))
        )
    if head in {"aws", "gcloud", "az"}:
        action = words[1] if len(words) > 1 else ""
        return not (
            action.startswith(("describe", "list", "get"))
            or (words[:2] == ["s3", "ls"])
        )
    if head in {"source", "."}:
        return False
    if head == "npx":
        tool = words[0] if words else ""
        return not (
            tool
            in {
                "tsc",
                "eslint",
                "jest",
                "vitest",
                "mocha",
                "biome",
                "stylelint",
                "vue-tsc",
            }
            or (tool == "prettier" and "--check" in rest)
            or (tool == "next" and words[1:2] == ["lint"])
            or (tool == "playwright" and words[1:2] == ["test"])
        )
    if head in SHELLS | INTERPRETERS:
        if any(a in {"--version", "-V", "--help"} for a in rest) or (
            head in SHELLS and "-n" in rest
        ):
            return False
        if head.startswith("python") and "-m" in rest:
            module = (
                rest[rest.index("-m") + 1] if rest.index("-m") + 1 < len(rest) else ""
            )
            if module in config["dev_tools"]:
                return False
        return not runs_read_only_script(args, config)
    relative = "/" in args[0] and not args[0].startswith("/")
    if relative and head not in config["_mutating"]:  # ./deploy.sh, scripts/x.sh
        return not runs_read_only_script(args, config)
    return head in config["_mutating"]


def git_changes(argv: list[str]) -> bool:
    i, _, _ = git_subcommand(argv)
    if i >= len(argv):
        return False
    sub, rest = argv[i], argv[i + 1 :]
    positional = [a for a in rest if not a.startswith("-")]
    if sub not in READ_ONLY_GIT:
        return True
    if sub == "branch":
        return any(a in MUTATING_GIT_BRANCH for a in rest) or bool(positional)
    if sub == "stash":
        return positional[:1] not in (["list"], ["show"])
    if sub == "tag":
        return bool(positional) and not any(
            a in {"-l", "--list", "-n", "--contains", "--points-at", "--merged"}
            for a in rest
        )
    if sub == "worktree":
        return positional[:1] != ["list"]
    if sub == "remote":
        return bool(positional) and positional[0] not in {"show", "get-url"}
    if sub == "config":
        return len(positional) > 1 or bool(GIT_CONFIG_WRITE.intersection(rest))
    return False


def check_container_command(after: list[str]) -> None:
    """The command line run inside a container (exec / run)."""
    if any(ENV_DUMP_WORD.search(a) for a in after):
        raise BlockedError("`env`/`printenv` inside a container exposes its secrets")
    if SECRET_ECHO.search(" ".join(after)):  # sh -c 'echo $SECRET' runs over there
        raise BlockedError("echoing a secret variable prints it")
    check_code(" ".join(after))


def exec_changes(rest_after_exec: list[str], config: dict) -> bool:
    """`docker exec [opts] <container> <program> ...` / `compose exec [opts] <svc> <program> ...`."""
    check_container_command(rest_after_exec)
    inner = " ".join(rest_after_exec)
    if ALEMBIC_READ.search(inner) and not ALEMBIC_WRITE.search(inner):
        return False
    if runs_read_only_script(rest_after_exec, config) and not re.search(
        r"[;&|]", inner
    ):
        return False
    positional, skip = [], False
    for a in rest_after_exec:
        if skip:
            skip = False
        elif a in DOCKER_EXEC_OPTS_WITH_VALUE:
            skip = True
        elif a.startswith("-") and not positional:
            continue
        else:
            positional.append(a)
    prog = positional[1].rsplit("/", 1)[-1] if len(positional) > 1 else ""
    if prog == "curl":
        return bool(CURL_WRITE.search(inner))
    return prog not in config["exec_read_only"]


def check_docker(head: str, rest: list[str], config: dict) -> bool:
    words = [a for a in rest if not a.startswith("-")]
    if head == "docker-compose" or words[:1] == ["compose"]:
        sub = next(
            (w for w in words if w in READ_ONLY_COMPOSE or w in COMPOSE_CHANGING), ""
        )
        if sub in {"config", "convert"} and not COMPOSE_CONFIG_SAFE.intersection(rest):
            raise BlockedError(
                "`docker compose config` prints every secret; add --quiet"
            )
        if sub in {"exec", "run"}:
            after = rest[rest.index(sub) + 1 :]
            check_container_command(after)
            return sub == "run" or exec_changes(after, config)
        if "--dry-run" in rest:
            return False
        return sub not in READ_ONLY_COMPOSE
    if not words:  # docker --version, docker --help
        return False
    sub = words[0]
    if sub in DOCKER_MANAGEMENT and len(words) > 1:
        if sub == "container" and words[1] in {"inspect", "exec", "run"}:
            sub = words[1]
        else:
            return words[1] not in READ_ONLY_DOCKER_SUB
    if sub == "inspect":
        fmt = next(
            (rest[i + 1] for i, a in enumerate(rest[:-1]) if a in {"-f", "--format"}),
            next((a.split("=", 1)[1] for a in rest if a.startswith("--format=")), None),
        )
        if fmt is None or re.search(
            r"Env|\{\{\s*json\s+\.\s*\}\}|\{\{\s*\.\s*\}\}|\.Config\s*(\}\}|\|)", fmt
        ):
            raise BlockedError(
                "`docker inspect` prints container env vars; use --format with the "
                "exact field (e.g. '{{.State.Status}}')"
            )
        return False
    if sub == "exec":
        return exec_changes(rest[rest.index("exec") + 1 :], config)
    if sub == "run":  # `docker run --env-file .env img env` would print the file
        check_container_command(rest[rest.index("run") + 1 :])
        return True
    return sub not in READ_ONLY_DOCKER


# --- entry points -------------------------------------------------------


def check_body(
    prefix: str, body: str, quoted: bool, config: dict, state: dict, depth: int
) -> bool:
    """A heredoc body: code for shells/ssh/interpreters/SQL clients, data otherwise."""
    segments = (
        split_commands(tokenize(strip_comments(prefix))) if prefix.strip() else []
    )
    feeder = unwrap(drop_assignments(segments[-1])) if segments else []
    prog = program(feeder)
    if prog in SHELLS or prog == "ssh":
        return check_command(body, config, dict(state), depth + 1) or prog == "ssh"
    if prog in INTERPRETERS:
        if names_secret_path(body, config) or ENV_PRINT.search(body):
            raise BlockedError("this script reads secrets or prints the environment")
        return True  # arbitrary code
    if prog in {"psql", "mysql", "mariadb"} or prog in config["sql_clients"]:
        return bool(SQL_WRITE.search(body))
    if not quoted:  # bash expands $(...) and $VARS in an unquoted heredoc
        changed, _ = check_substitutions(body, config, state, depth)
        if SECRET_VAR.search(body):
            raise BlockedError(
                "an unquoted heredoc expands a secret variable; quote the delimiter (<<'EOF')"
            )
        return changed
    return False


def check_command(cmd: str, config: dict, state: dict, depth: int = 0) -> bool:
    """Raise BlockedError if the command must not run; return True if it changes things."""
    if depth > 3:
        raise BlockedError("nested shells too deep to check")
    if len(cmd) > MAX_COMMAND:
        raise BlockedError(
            f"command longer than {MAX_COMMAND // 1024} KB; put it in a file and run that"
        )
    text, bodies = split_heredocs(join_continuations(cmd))
    text = strip_comments(text)
    check_raw(text, config)
    changed = False
    for prefix, body, quoted in bodies:
        changed |= check_body(prefix, body, quoted, config, state, depth)
    sub_changed, text = check_substitutions(text, config, state, depth)
    changed |= sub_changed
    saved: list[
        dict
    ] = []  # ( ... ) and $( ... ) run in a subshell: a cd inside stays inside
    current: list[str] = []
    for tok in tokenize(text) + [";"]:
        if tok not in SEPARATORS:
            current.append(tok)
            continue
        if current:
            changed |= check_simple_command(
                current, state.get("config", config), state, depth
            )
            current = []
        if tok == "(":
            saved.append(dict(state))
        elif tok == ")" and saved:
            state.update(saved.pop())
    return changed


def check_simple_command(
    argv: list[str], config: dict, state: dict, depth: int
) -> bool:
    """One command between separators: track cd, recurse into sh -c / eval,
    check branches, then the secret and change rules."""
    argv = drop_assignments(argv)
    if not argv:
        return False
    args, _, _ = split_redirects(argv)
    inner = unwrap(args)
    prog = program(inner)
    if prog == "cd":
        target = inner[1] if len(inner) > 1 else "~"
        if not unresolved(target):  # cd "$X" / cd -: keep the branch we know
            base = Path(state["cwd"] or ".")
            state["cwd"] = str(base / os.path.expanduser(target))
            state["branch"] = git_branch(state["cwd"])
            state["config"] = config_for(state["cwd"], config)
        return False
    if prog in SHELLS and "-c" in inner[1:]:
        idx = inner.index("-c") + 1
        changed = check_command(
            inner[idx] if idx < len(inner) else "", config, dict(state), depth + 1
        )
        return changed or program(args) in config["_mutating"]
    if prog == "eval":
        return check_command(" ".join(inner[1:]), config, state, depth + 1)
    if prog == "git":
        check_git_branches(inner, state, config)
    elif prog == "gh":
        check_pr_create(inner, state, config)
    return check_segment(argv, config)


def guard_config_path(tool_input: dict) -> bool:
    value = tool_input.get("file_path") or tool_input.get("path") or ""
    return isinstance(value, str) and value.replace("\\", "/").endswith(CONFIG_NAME)


def decide(payload: dict, config: dict) -> None:
    """Raise BlockedError or AskError; return quietly when the call may proceed."""
    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(tool, str) or not isinstance(tool_input, dict):
        raise BlockedError("unreadable hook input (no tool_name / tool_input)")
    if tool == "Bash":
        cmd = tool_input.get("command")
        if not isinstance(cmd, str):
            raise BlockedError("command is not a string")
        cwd = payload.get("cwd")
        state = {"branch": git_branch(cwd), "cwd": cwd}
        if check_command(cmd, config, state) and config["ask_before_changes"]:
            raise AskError("this command changes a server, repo or database")
        return
    if config.get("_managed") and tool in WRITE_TOOLS:
        target = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        if isinstance(target, str) and names_policy_file(target):
            raise BlockedError(
                f"{target} is managed on this machine; change it in the repo, not here"
            )
    for key in FILE_KEYS:
        value = tool_input.get(key)
        # Grep's `pattern` is a regex, not a path; only Glob's pattern names files.
        is_path = key != "pattern" or tool == "Glob"
        if isinstance(value, str) and is_path and names_secret_path(value, config):
            raise BlockedError(f"{value} holds secrets; {config['secret_hint']}")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise TypeError("payload is not an object")
    except (ValueError, TypeError) as exc:
        print(f"Blocked by tool-guard: unreadable hook input ({exc})", file=sys.stderr)
        return 2
    try:
        config = load_config(project_dir(payload))
        decide(payload, config)
    except ConfigError as exc:
        tool_input = payload.get("tool_input")
        if (
            os.environ.get("TAPWAY_GUARD_MANAGED") != "1"
            and payload.get("tool_name") != "Bash"
            and isinstance(tool_input, dict)
            and guard_config_path(tool_input)
        ):
            return 0  # let the agent open and fix the broken config itself
        print(f"Blocked by tool-guard: fix {exc}", file=sys.stderr)
        return 2
    except BlockedError as exc:
        print(f"Blocked by tool-guard: {exc}", file=sys.stderr)
        return 2
    except AskError as exc:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "ask",
                        "permissionDecisionReason": f"tool-guard: {exc}; approve only if you expect it",
                    }
                }
            )
        )
    except Exception as exc:  # noqa: BLE001 - a crash must block; exit 1 would let the call through
        print(
            f"Blocked by tool-guard: internal error ({type(exc).__name__}: {exc}); refusing to guess",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
