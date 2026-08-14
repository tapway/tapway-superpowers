# install.ps1 — Install all 24 Tapway Superpowers skills into Hermes Agent
#              (gbrain-style: one command scaffolds the whole skillpack).
#
# Modes ($env:HERMES_INSTALL_MODE):
#   auto  (default) — prefer local copy when this checkout has hermes/skills/;
#                     otherwise use the Hermes skill hub. Parses hub output for
#                     skills-guard blocks (exit code alone is NOT reliable).
#   local           — copy from this repo's hermes/skills/ only.
#   hub             — hermes skills install from GitHub only.
#
# Optional:
#   $env:HERMES_DRY_RUN = "1"
#   $env:HERMES_SKILLS_REF = "v1.8.2"   # documented pin for local checkout
#
# Usage:
#   .\install.ps1                         # default category: tapway
#   .\install.ps1 "tapway-superpowers"    # custom skills category
#
# See hermes/INSTALL_ISSUES.md for the field report that motivated this installer.

param([string]$Category = "tapway")

$ErrorActionPreference = "Stop"

$Repo = "tapway/tapway-superpowers"
$SkillRoot = "hermes/skills"
$Mode = if ($env:HERMES_INSTALL_MODE) { $env:HERMES_INSTALL_MODE } else { "auto" }

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LocalSkillsDir = Join-Path $ScriptDir "skills"

$Skills = @(
  "interview",
  "brainstorming",
  "writing-plans",
  "tdd",
  "e2e-playwright",
  "quality-gates",
  "dependency-audit",
  "api-contract-testing",
  "db-migration-testing",
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
  "incident-runbook",
  "pr",
  "repo-docs",
  "git-worktrees",
  "setup-project",
  "codemax-gbrain"
)

$NameCollisions = @("writing-plans", "systematic-debugging")

if (-not (Get-Command hermes -ErrorAction SilentlyContinue)) {
  Write-Error "Hermes CLI not found on PATH. Install it first: curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash"
  exit 1
}

function Get-HermesHome {
  try {
    $cfg = & hermes config path 2>$null
    if ($cfg) { return (Split-Path -Parent $cfg) }
  } catch {}
  if ($env:HERMES_HOME) { return $env:HERMES_HOME }
  $win = Join-Path $env:USERPROFILE "AppData\Local\hermes"
  if (Test-Path $win) { return $win }
  return (Join-Path $env:USERPROFILE ".hermes")
}

function Test-LocalSkills {
  return (Test-Path (Join-Path $LocalSkillsDir "tdd\SKILL.md"))
}

function Install-LocalSkill([string]$Skill) {
  $src = Join-Path $LocalSkillsDir $Skill
  $dest = Join-Path $DestRoot $Skill
  if (-not (Test-Path (Join-Path $src "SKILL.md"))) {
    return $false
  }
  New-Item -ItemType Directory -Force -Path $DestRoot | Out-Null
  if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
  Copy-Item -Recurse -Force $src $dest
  return (Test-Path (Join-Path $dest "SKILL.md"))
}

function Install-HubSkill([string]$Skill) {
  $identifier = "$Repo/$SkillRoot/$Skill"
  # Capture all streams. Hermes often exits 0 even when skills-guard blocks.
  $out = & hermes skills install $identifier --category $Category --yes 2>&1 | Out-String
  $out.Trim().Split("`n") | Select-Object -Last 12 | ForEach-Object { Write-Host "      $_" }

  if ($out -match "Installation blocked|Blocked \(community|Verdict: DANGEROUS") {
    return $false
  }
  if ($out -match "Error:|FAILED|Traceback") {
    return $false
  }
  if ($out -match "Installed:|already installed") {
    return $true
  }
  return ($LASTEXITCODE -eq 0)
}

$HermesHomeDir = Get-HermesHome
$DestRoot = Join-Path $HermesHomeDir "skills\$Category"
$HaveLocal = Test-LocalSkills

Write-Host "Installing Tapway Superpowers into Hermes"
Write-Host "  category : $Category"
Write-Host "  mode     : $Mode"
Write-Host "  hermes   : $HermesHomeDir"
if ($HaveLocal) {
  Write-Host "  local    : $LocalSkillsDir (available)"
} else {
  Write-Host "  local    : (not available — run from a full git checkout for offline/local mode)"
}
if ($env:HERMES_SKILLS_REF) {
  Write-Host "  ref pin  : $($env:HERMES_SKILLS_REF) (applies to local checkout; hub follows default branch)"
}
Write-Host "  source   : $Repo/$SkillRoot"
Write-Host

$installed = 0
$failed = 0
$usedLocal = 0
$usedHub = 0
$failedNames = New-Object System.Collections.Generic.List[string]

foreach ($skill in $Skills) {
  Write-Host ("  - {0,-22} " -f $skill) -NoNewline

  if ($env:HERMES_DRY_RUN) {
    if ($Mode -eq "local" -or ($Mode -eq "auto" -and $HaveLocal)) {
      Write-Host "(dry-run) local-copy -> $DestRoot\$skill"
    } else {
      Write-Host "(dry-run) hub $Repo/$SkillRoot/$skill"
    }
    $installed++
    continue
  }

  $ok = $false
  $via = ""

  switch ($Mode) {
    "local" {
      if (Install-LocalSkill $skill) { $ok = $true; $via = "local" }
    }
    "hub" {
      if (Install-HubSkill $skill) { $ok = $true; $via = "hub" }
    }
    default {
      if ($HaveLocal) {
        if (Install-LocalSkill $skill) { $ok = $true; $via = "local" }
      } else {
        if (Install-HubSkill $skill) { $ok = $true; $via = "hub" }
      }
    }
  }

  if ($ok) {
    Write-Host "[OK] $via"
    $installed++
    if ($via -eq "local") { $usedLocal++ }
    if ($via -eq "hub") { $usedHub++ }
  } else {
    Write-Host "[FAIL]"
    $failed++
    $failedNames.Add($skill) | Out-Null
  }
}

Write-Host
$total = $Skills.Count

if ($env:HERMES_DRY_RUN) {
  Write-Host "[dry-run] Would create bundle: hermes bundles create tapway --skill ... (x$total) --force"
  Write-Host "Dry-run complete: $installed/$total skills would be installed."
  exit 0
}

$bundleArgs = @("create", "tapway")
foreach ($skill in $Skills) { $bundleArgs += "--skill"; $bundleArgs += $skill }
$bundleArgs += "--description"; $bundleArgs += "Tapway strict engineering pipeline"
$bundleArgs += "--force"
try {
  & hermes bundles @bundleArgs
  Write-Host "Bundle: /tapway refreshed"
} catch {
  Write-Host "Warning: hermes bundles create failed — skills may still be usable individually"
}

Write-Host
Write-Host "Done. $installed/$total skills installed (hub=$usedHub, local=$usedLocal, failed=$failed)."
if ($failed -gt 0) {
  Write-Host "Failed skills: $($failedNames -join ', ')"
  Write-Host "Hints:"
  Write-Host "  - From a git checkout:  `$env:HERMES_INSTALL_MODE='local'; .\hermes\install.ps1 $Category"
  Write-Host "  - Hub auth:             gh auth login"
  Write-Host "  - See:                  hermes/INSTALL_ISSUES.md"
}

Write-Host "  - Verify:         hermes skills list | Select-String tapway"
Write-Host "  - On disk:        $DestRoot"
Write-Host "  - Pipeline:       /tapway"
Write-Host
Write-Host "Name collisions with Hermes core/community skills: $($NameCollisions -join ', ')"
Write-Host
Write-Host "Recommended memory pin:"
Write-Host "  interview -> brainstorming -> writing-plans -> [tdd] -> simplify-code -> requesting-code-review -> pr"

if ($failed -gt 0) { exit 1 }
exit 0
