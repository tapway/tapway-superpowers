# /release — Bump Version and Prepare a Release

Bumps the version in `plugin.json` and `marketplace.json`, adds a new section header to `CHANGELOG.md`, commits, and prints the exact commands to tag and publish the release.

## Usage
```
/release patch    # 1.0.0 → 1.0.1
/release minor    # 1.0.0 → 1.1.0
/release major    # 1.0.0 → 2.0.0
```

## What it does
1. Reads current version from `.claude-plugin/plugin.json`
2. Bumps it according to the argument
3. Writes new version to both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
4. Prepends a new `## [X.Y.Z] — YYYY-MM-DD` section to `CHANGELOG.md`
5. Commits the version bump
6. Prints the tag + GitHub release commands to run locally

> **Note:** The tag itself must be pushed from a local machine — the Claude Code web environment cannot push git tags. The commands are printed at the end for you to copy.

## Implementation

```bash
set -e

BUMP="${1:-}"
if [[ "$BUMP" != "patch" && "$BUMP" != "minor" && "$BUMP" != "major" ]]; then
  echo "ERROR: argument must be one of: patch, minor, major" >&2
  exit 1
fi

# Read current version from plugin.json
CURRENT=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])")
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

# Bump
case "$BUMP" in
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch) PATCH=$((PATCH + 1)) ;;
esac
NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
TODAY=$(date +%Y-%m-%d)

echo "Bumping $CURRENT → $NEW_VERSION"

# Update plugin.json
python3 - <<PYEOF
import json
for path in ['.claude-plugin/plugin.json', '.claude-plugin/marketplace.json']:
    with open(path) as f:
        data = json.load(f)
    # plugin.json has top-level version
    if 'version' in data:
        data['version'] = '$NEW_VERSION'
    # marketplace.json has nested versions
    if 'metadata' in data:
        data['metadata']['version'] = '$NEW_VERSION'
    if 'plugins' in data:
        for p in data['plugins']:
            p['version'] = '$NEW_VERSION'
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    print(f'Updated {path}')
PYEOF

# Prepend new version block to CHANGELOG.md (Keep a Changelog format)
# Inserts after the header block (first 6 lines: title, blank, description, format link, semver link, blank)
NEW_SECTION="## [$NEW_VERSION] — $TODAY

### Added

- _(fill in before pushing)_

---

"
python3 - <<PYEOF
with open('CHANGELOG.md', 'r') as f:
    content = f.read()

# Find the insertion point: after the header, before the first ## section
import re
match = re.search(r'\n## \[', content)
if match:
    insert_at = match.start() + 1  # after the \n
    new_content = content[:insert_at] + """$NEW_SECTION""" + content[insert_at:]
else:
    new_content = content + '\n$NEW_SECTION'

with open('CHANGELOG.md', 'w') as f:
    f.write(new_content)
print('Updated CHANGELOG.md')
PYEOF

echo ""
echo "Fill in the [$NEW_VERSION] section in CHANGELOG.md, then:"
echo ""

# Commit version bump files (changelog will be committed separately after editing)
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json CHANGELOG.md
git commit -m "chore: bump version to $NEW_VERSION"
git push origin main

echo ""
echo "✅ Version $NEW_VERSION committed and pushed."
echo ""
echo "════════════════════════════════════════════"
echo "  Run these locally to tag and publish:"
echo "════════════════════════════════════════════"
echo ""
echo "  git pull origin main"
echo "  git tag -a v$NEW_VERSION -m \"v$NEW_VERSION\""
echo "  git push origin v$NEW_VERSION"
echo ""
echo "  # PowerShell — create GitHub release:"
echo "  \$content = Get-Content CHANGELOG.md -Raw"
echo "  \$notes = [regex]::Match(\$content, '(?s)## \[$NEW_VERSION\].*?(?=\r?\n---\r?\n)').Value"
echo "  \$notes | Set-Content release-notes.tmp -Encoding utf8"
echo "  gh release create v$NEW_VERSION --title \"v$NEW_VERSION\" --notes-file release-notes.tmp"
echo "  Remove-Item release-notes.tmp"
echo ""
echo "  # bash/zsh — create GitHub release:"
echo "  gh release create v$NEW_VERSION \\"
echo "    --title \"v$NEW_VERSION\" \\"
echo "    --notes \"\$(sed -n '/## \[$NEW_VERSION\]/,/^---/{ /^---/!p }' CHANGELOG.md | sed '1d')\""
echo "════════════════════════════════════════════"
```
