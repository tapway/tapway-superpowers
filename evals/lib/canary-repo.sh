#!/bin/bash
# Turn the eval workspace (current dir) into a committed git repo whose env
# files are ignored, the way a real checkout looks. Run it after writing the
# files a case needs (canary-env.sh for the secrets).
#
#   canary-repo.sh [branch]        # default branch: main
set -eu
branch=${1:-main}
if ! grep -qx '# canary-repo' .gitignore 2>/dev/null; then
  printf '# canary-repo\n.env\n.env.*\n*.env\n!.env.example\n!.env.sample\n!.env.template\n!.env.dist\n!sample.env\n*.bak-*\n' >> .gitignore
fi
git init -q -b "$branch" .
# Fixtures must commit on any machine: no signing prompts, no global hooks.
g() { git -c user.name=eval -c user.email=eval@example.com -c commit.gpgsign=false -c core.hooksPath=/dev/null "$@"; }
g add -A
g commit -q --allow-empty -m "eval fixture"
echo "fixture repo on $branch"
