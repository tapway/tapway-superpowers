# install.ps1 — Install Tapway Superpowers skills into Hermes Agent (Windows)
#
# Copies the 6 Tapway-specific skills into your Hermes skills directory.
# Idempotent: re-running just refreshes the files.
#
# Usage (PowerShell):
#   .\install.ps1                # auto-detect location
#   .\install.ps1 "C:\path\to\skills"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SrcDir = $ScriptDir

if ($args.Count -ge 1) {
    $HermesSkills = $args[0]
} elseif ($env:HERMES_SKILLS_HOME) {
    $HermesSkills = $env:HERMES_SKILLS_HOME
} elseif ($env:HERMES_HOME) {
    $HermesSkills = Join-Path $env:HERMES_HOME "skills"
} elseif ($env:LOCALAPPDATA) {
    $HermesSkills = Join-Path $env:LOCALAPPDATA "hermes\skills"
} else {
    $HermesSkills = Join-Path $env:USERPROFILE "AppData\Local\hermes\skills"
}

$Skills = @("interview","brainstorming","writing-plans","tdd","repo-docs","pr")

Write-Host "Source : $SrcDir"
Write-Host "Target : $HermesSkills"
Write-Host

if (-not (Test-Path $HermesSkills)) { New-Item -ItemType Directory -Force -Path $HermesSkills | Out-Null }
$TapwayDir = Join-Path $HermesSkills "tapway"
if (-not (Test-Path $TapwayDir)) { New-Item -ItemType Directory -Force -Path $TapwayDir | Out-Null }

foreach ($s in $Skills) {
    $src = Join-Path $SrcDir "$s\SKILL.md"
    if (Test-Path $src) {
        $destDir = Join-Path $TapwayDir $s
        if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Force -Path $destDir | Out-Null }
        Copy-Item $src (Join-Path $destDir "SKILL.md") -Force
        Write-Host "  [OK] installed tapway/$s"
    } else {
        Write-Host "  [!!] missing source for $s (skipped)"
    }
}

Write-Host
Write-Host "Done. Restart Hermes (or run 'hermes skills list') to verify."
Write-Host
Write-Host "Recommended: pin the dev process to memory so it runs on every task:"
Write-Host "  interview -> brainstorming -> writing-plans -> [tdd] -> simplify-code -> requesting-code-review -> pr"
