#!/bin/bash
# Session start — loads project context into Codex's working memory.
# Codex sends the SessionStart payload ({hook_event, ...}) as JSON on stdin.

INPUT=$(cat)
# SessionStart payload has no tool_input; parse anyway for forward compat.
PAYLOAD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)))" 2>/dev/null || echo "")

echo "🚀 Codex session starting for: $(basename $(pwd))"
echo ""
echo "📋 Current branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'N/A')"
echo "📝 Last 3 commits:"
git log --oneline -3 2>/dev/null || echo "  (no git history)"
echo ""
echo "🔄 Git status:"
git status --short 2>/dev/null || echo "  (no git)"
echo ""

# Check for open TODOs in AGENTS.md
if grep -q "\- \[ \]" AGENTS.md 2>/dev/null; then
  echo "📌 Open items in AGENTS.md:"
  grep "\- \[ \]" AGENTS.md | head -5
  echo ""
fi

# Check for required GitHub Actions release workflow
if [ -d ".git" ]; then
  [ ! -f ".github/workflows/release.yml" ] && \
    { echo "⚠️  SETUP REQUIRED: missing .github/workflows/release.yml"
      echo "   • release.yml — semver auto-release (vX.Y.Z-stg/prod) on merge"
      echo "   To fix: tell me 'setup project' and I will create it for you."
      echo ""; }
fi

# CodeMAX / gbrain — OPT-IN. Only runs when CODEMAX_ENABLED=1 is set.
# Hints off the GitHub issue for this branch (see pre-execute-github-issue-check.sh).
if [ "${CODEMAX_ENABLED:-0}" = "1" ]; then
  ISSUE_NUM=""
  if command -v gh &>/dev/null; then
    REPO="$(git remote get-url origin 2>/dev/null | sed -E 's|.*github\.com[:/]([^/]+/[^/]+)(\.git)?$|\1|' | sed -E 's|\.git$||')"
    BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
    if [ -n "$REPO" ] && [ -n "$BRANCH" ]; then
      ISSUE_NUM="$(gh issue list --repo "$REPO" --search "label:codemax in:body ${BRANCH}" --json number --jq '.[0].number // ""' 2>/dev/null)"
    fi
  fi
  if [ -n "$ISSUE_NUM" ]; then
    echo "🧠 gbrain: GitHub issue #$ISSUE_NUM found for this branch"
    echo "   Pull its traced requirement/blueprint/ADR into context (see codemax-gbrain skill)."
    echo "   Run 'codemax sync run' before /pr so the brain stays current."
    echo ""
  else
    echo "🧠 gbrain: CodeMAX enabled (no GitHub issue detected for this branch yet)."
    echo "   One is auto-created after the plan step; use 'codemax sync run' to push docs, or the codemax-gbrain skill once an issue exists."
    echo ""
  fi
fi

echo "✅ Project context loaded. AGENTS.md is your source of truth."