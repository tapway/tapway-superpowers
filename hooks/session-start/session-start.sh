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

# Check for @claude GitHub Actions workflow
if [ -d ".git" ] && [ ! -f ".github/workflows/claude.yml" ]; then
  echo "⚠️  SETUP REQUIRED: .github/workflows/claude.yml is missing."
  echo "   Without it, @claude mentions in PR comments will not trigger fixes."
  echo "   To fix: tell me 'set up the @claude GitHub Actions workflow'"
  echo "   and I will create and commit the file for you."
  echo ""
fi

echo "✅ Project context loaded. CLAUDE.md is your source of truth."