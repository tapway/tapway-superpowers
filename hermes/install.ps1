# install.ps1 — Install all 19 Tapway Superpowers skills into Hermes Agent
#              (gbrain-style: one command scaffolds the whole skillpack).
#
# Uses Hermes's native skill hub (hermes skills install) with GitHub
# identifiers, so there is no dependence on local file layout — works from
# anywhere, idempotent, stays in sync with the repo.
#
# Also creates a `/tapway` skill bundle so the whole pipeline loads with a
# single slash command.
#
# Usage (PowerShell):
#   .\install.ps1                         # default category: tapway
#   .\install.ps1 "sweng"                 # custom skills category
#
# Prereqs:
#   - `hermes` on PATH
#   - GitHub auth recommended (gh auth login / GH_TOKEN) to avoid rate limits
#
# Dry-run / preview first (no writes):
#   $env:HERMES_DRY_RUN = "1"; .\install.ps1

param([string]$Category = "tapway")

$ErrorActionPreference = "Stop"

$Repo     = "tapway/tapway-superpowers"
$SkillRoot = "hermes/skills"

# All 19 ported skills. Order = pipeline order.
$Skills = @(
  "interview",
  "brainstorming",
  "writing-plans",
  "tdd",
  "e2e-playwright",
  "autoship",
  "refactor",
  "systematic-debugging",
  "code-review",
  "pre-review-cleanup",
  "security-audit",
  "verification",
  "doubt",
  "observe",
  "deprecate",
  "pr",
  "repo-docs",
  "git-worktrees",
  "setup-project"
)

if (-not (Get-Command hermes -ErrorAction SilentlyContinue)) {
  Write-Error "Hermes CLI not found on PATH. Install it first: curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash"
  exit 1
}

Write-Host "Installing Tapway Superpowers into Hermes (category: $Category)"
Write-Host "Source repo: $Repo/$SkillRoot"
Write-Host

$installed = 0
foreach ($skill in $Skills) {
  $identifier = "$Repo/$SkillRoot/$skill"
  Write-Host ("  - {0,-20} " -f $skill) -NoNewline

  if ($env:HERMES_DRY_RUN) {
    Write-Host "(dry-run) hermes skills install $identifier --category $Category --yes"
    $installed++
    continue
  }

  hermes skills install $identifier --category $Category --yes
  if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] installed tapway/$skill"
    $installed++
  } else {
    Write-Host "[FAIL] could not install tapway/$skill"
    Write-Host "  Try: gh auth login   (avoids GitHub API rate limits)"
  }
}

Write-Host
if ($env:HERMES_DRY_RUN) {
  Write-Host "[dry-run] Would create bundle:"
  $bundleCmd = "hermes bundles create tapway"
  foreach ($skill in $Skills) { $bundleCmd += " --skill $skill" }
  $bundleCmd += ' --description "Tapway strict engineering pipeline" --force'
  Write-Host "          $bundleCmd"
  Write-Host
  Write-Host "Dry-run complete: $installed skills would be installed."
  exit 0
}

# Create (or refresh) the /tapway bundle that loads the whole pipeline.
$bundleArgs = @("create", "tapway")
foreach ($skill in $Skills) { $bundleArgs += "--skill"; $bundleArgs += $skill }
$bundleArgs += "--description"; $bundleArgs += "Tapway strict engineering pipeline"
$bundleArgs += "--force"
hermes bundles @bundleArgs

Write-Host
Write-Host "Done. $installed skills installed."
Write-Host "  - Verify:         hermes skills list | Select-String tapway"
Write-Host "  - Run the whole pipeline:  /tapway"
Write-Host "  - Or invoke a single step: /interview /brainstorming /writing-plans /tdd ... /pr"
Write-Host
Write-Host "Recommended: pin the dev process to memory so it runs on every task:"
Write-Host "  interview -> brainstorming -> writing-plans -> [tdd] -> simplify-code -> requesting-code-review -> pr"
