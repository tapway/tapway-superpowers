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

echo "✅ Project context loaded. CLAUDE.md is your source of truth."