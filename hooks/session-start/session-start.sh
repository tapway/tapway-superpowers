#!/bin/bash
# Session start — loads project context into Claude's working memory

echo "🚀 Claude Code session starting for: $(basename $(pwd))"
echo ""
echo "📋 Current branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'N/A')"
echo "📝 Last 3 commits:"
git log --oneline -3 2>/dev/null || echo "  (no git history)"
echo ""
echo "🔄 Git status:"
git status --short 2>/dev/null || echo "  (no git)"
echo ""

# Check for open TODOs in CLAUDE.md
if grep -q "\- \[ \]" CLAUDE.md 2>/dev/null; then
  echo "📌 Open items in CLAUDE.md:"
  grep "\- \[ \]" CLAUDE.md | head -5
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
# Users who don't use CodeMAX set nothing and see nothing (no hooks, no errors).
#
# Hints off the GitHub issue for this branch, not a WO-* identifier: nothing
# in the actual dev flow ever writes a WO-* into a branch name or CLAUDE.md
# (work orders live on the CodeMAX panel, disconnected from this repo), while
# every branch gets a GitHub issue via the writing-plans skill after /plan.
# Same lookup as hooks/pre-execute-github-issue/check.sh.
if [ "${CODEMAX_ENABLED:-0}" = "1" ]; then
  ISSUE_NUM=""
  if command -v gh &>/dev/null; then
    REPO="$(git remote get-url origin 2>/dev/null | sed -E 's|.*github\.com[:/]([^/]+/[^/]+)(\.git)?$|\1|')"
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

echo "✅ Project context loaded. CLAUDE.md is your source of truth."