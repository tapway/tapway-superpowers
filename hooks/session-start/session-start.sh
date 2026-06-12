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

# Check for required GitHub Actions workflows
if [ -d ".git" ]; then
  MISSING=""
  [ ! -f ".github/workflows/claude.yml" ]  && MISSING="$MISSING claude.yml"
  [ ! -f ".github/workflows/release.yml" ] && MISSING="$MISSING release.yml"
  if [ -n "$MISSING" ]; then
    echo "⚠️  SETUP REQUIRED: missing GitHub Actions workflows:$MISSING"
    echo "   • claude.yml  — auto PR review + @claude fix commands"
    echo "   • release.yml — CalVer auto-release (YYYY.WW.XX.YY-stg/prod) on merge"
    echo "   To fix: tell me 'setup project' and I will create them for you."
    echo ""
  fi
fi

echo "✅ Project context loaded. CLAUDE.md is your source of truth."