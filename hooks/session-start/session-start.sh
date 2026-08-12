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
if [ "${CODEMAX_ENABLED:-0}" = "1" ]; then
  WO_ID=""
  BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
  # Look for a WO-* reference in the branch name or CLAUDE.md
  case "$BRANCH" in
    *wo-*) WO_ID="$(echo "$BRANCH" | grep -oiE 'wo-[0-9]+' | head -1)" ;;
  esac
  if [ -z "$WO_ID" ] && [ -f "CLAUDE.md" ]; then
    WO_ID="$(grep -oiE 'WO-[0-9]+' CLAUDE.md 2>/dev/null | head -1)"
  fi
  if [ -n "$WO_ID" ]; then
    echo "🧠 gbrain: active work order detected → $WO_ID"
    echo "   Pull its traced requirement/blueprint/ADR into context (see codemax-gbrain skill)."
    echo "   Run 'codemax sync run' before /pr so the brain stays current."
    echo ""
  else
    echo "🧠 gbrain: CodeMAX enabled (no WO-* detected)."
    echo "   Use 'codemax sync run' to push docs, or the codemax-gbrain skill on any WO-* task."
    echo ""
  fi
fi

echo "✅ Project context loaded. CLAUDE.md is your source of truth."