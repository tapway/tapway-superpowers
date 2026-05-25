# /upgrade-skills — Update All Plugins and Marketplaces

Update all installed Claude Code plugins and their marketplaces to the latest versions. Use this when you want to pull in improvements to skills, agents, or hooks.

## What it does
1. Updates all configured marketplaces from their sources
2. Updates each installed plugin to its latest version
3. Reports what changed

## Implementation
Run the following commands:

```bash
echo "Updating marketplaces..."
claude plugin marketplace update

echo ""
echo "Updating plugins..."

# Update each installed plugin
claude plugin update tapway-superpowers@tapway 2>&1 || echo "  (tapway-superpowers may already be at latest)"
claude plugin update andrej-karpathy-skills@karpathy-skills 2>&1 || echo "  (andrej-karpathy-skills may already be at latest)"
claude plugin update claude-code-setup@claude-plugins-official 2>&1 || echo "  (claude-code-setup may already be at latest)"

echo ""
echo "Done. Restart Claude Code to apply any plugin updates."
echo ""
echo "Verifying installed plugins:"
claude plugin list
```

## Manual alternative
If the automated commands don't work, run individually:
```
claude plugin marketplace update              # refresh all marketplace catalogs
claude plugin update tapway-superpowers@tapway
claude plugin update andrej-karpathy-skills@karpathy-skills
claude plugin update claude-code-setup@claude-plugins-official
```

Restart Claude Code after updating to apply changes.