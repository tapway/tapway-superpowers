#!/bin/bash
# Run a repo's skill evals with `claude plugin eval`.
#
#   scripts/skill-evals.sh [--repo DIR] [--case GLOB] [--max-cost USD] [--dry-run]
#
# Expects in the repo:
#   .claude/skills/<skill>/SKILL.md     the skills under test
#   evals/<case>/case.yaml (+ scaffold.sh)
#   evals/plugin.json                   optional: {"name": ..., "description": ...}
#   evals/include.txt                   optional: repo paths the scaffolds copy,
#                                       one per line (e.g. scripts/env-helper.sh)
#
# It assembles <repo>/.eval-plugin/ (gitignore it): the skills, the cases, the
# include.txt files at their repo paths, and this plugin's evals/lib as
# evals/_tapway/ for canary-env.sh / canary-repo.sh. Then it runs the eval with
# Bash allowed, nothing published, a cost cap, and no baseline arm
# (--ablation none; that flag does not switch hooks off). The eval sandbox does
# not load the repo's .claude/ hooks, so a case measures the skill text, not
# the repo's guard. Reports land in .eval-plugin/evals/results/latest.json.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
repo=.
case_glob='*'
max_cost=10
dry_run=0
while [ $# -gt 0 ]; do
  case "$1" in
    --repo|--case|--max-cost)
      [ $# -ge 2 ] || { echo "skill-evals: $1 needs a value" >&2; exit 64; }
      case "$1" in
        --repo) repo=$2 ;;
        --case) case_glob=$2 ;;
        --max-cost) max_cost=$2 ;;
      esac
      shift 2 ;;
    --dry-run) dry_run=1; shift ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
    *) echo "skill-evals: unknown option $1" >&2; exit 64 ;;
  esac
done

repo=$(cd "$repo" && pwd)
[ -d "$repo/.claude/skills" ] || { echo "skill-evals: no .claude/skills in $repo" >&2; exit 1; }
[ -d "$repo/evals" ] || { echo "skill-evals: no evals/ in $repo" >&2; exit 1; }
ls "$repo"/evals/*/case.yaml >/dev/null 2>&1 || { echo "skill-evals: no evals/<case>/case.yaml in $repo" >&2; exit 1; }

out="$repo/.eval-plugin"
rm -rf "$out"
mkdir -p "$out/.claude-plugin" "$out/evals"
if [ -f "$repo/evals/plugin.json" ]; then
  cp "$repo/evals/plugin.json" "$out/.claude-plugin/plugin.json"
else
  printf '{"name": "%s-skills", "description": "Eval-only wrapper for %s/.claude/skills"}\n' \
    "$(basename "$repo")" "$(basename "$repo")" > "$out/.claude-plugin/plugin.json"
fi
cp -r "$repo/.claude/skills" "$out/skills"
cp -R "$repo/evals/." "$out/evals/"
rm -rf "$out/evals/results" "$out/evals/plugin.json" "$out/evals/include.txt"  # top level only
mkdir -p "$out/evals/_tapway"
cp "$HERE/evals/lib/"*.sh "$out/evals/_tapway/"
if [ -f "$repo/evals/include.txt" ]; then
  while IFS= read -r path || [ -n "$path" ]; do
    case "$path" in ''|'#'*) continue ;; esac
    case "$path" in /*|*..*) echo "skill-evals: include.txt paths must be relative: $path" >&2; exit 1 ;; esac
    # The eval workspace is sent to a model: never copy a real secret into it.
    if printf '%s' "$path" | grep -qiE '(^|/)\.env($|\.)|(^|/)\.envrc$|[^/]\.env$|credentials|\.pem$|\.key$|id_(rsa|ed25519|ecdsa)$|\.netrc$|\.npmrc$|\.pgpass$' \
       && ! printf '%s' "$path" | grep -qiE '(^|/)(sample|example|template)\.env|\.env\.(example|sample|template|dist)$'; then
      echo "skill-evals: include.txt must not list secret files: $path" >&2; exit 1
    fi
    [ -e "$repo/$path" ] || { echo "skill-evals: include.txt lists a missing path: $path" >&2; exit 1; }
    mkdir -p "$out/$(dirname "$path")"
    cp -r "$repo/$path" "$out/$path"
  done < "$repo/evals/include.txt"
fi

cmd=(claude plugin eval "$out" --case "$case_glob" --ablation none --scaffold --trust-plugin
     --allow-tools Bash --no-publish -j 3 --max-cost-usd "$max_cost"
     --json "$out/evals/results/latest.json")
echo "assembled $out ($(ls -d "$out"/evals/*/case.yaml | wc -l) cases, $(ls "$out/skills" | wc -l) skills)"
if [ "$dry_run" = 1 ]; then
  printf 'would run:'; printf ' %q' "${cmd[@]}"; echo
  exit 0
fi
command -v claude >/dev/null 2>&1 || { echo "skill-evals: claude CLI not found" >&2; exit 1; }
mkdir -p "$out/evals/results"
"${cmd[@]}"
