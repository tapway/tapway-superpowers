# install.ps1 — Install all 24 Tapway Superpowers skills + enforceable hooks
#              into OpenAI Codex (Windows / PowerShell / git-bash).
#
# Mirrors codex/install.sh: copies skills to $HOME\.agents\skills (user scope)
# or <project>\.agents\skills (repo scope), and optionally wires .codex/hooks.json
# + hook scripts + AGENTS.md into a consuming project.
#
# Env:
#   CODEX_SKILL_SCOPE=user|repo       scope for skills (default: user)
#   CODEX_TARGET_PROJECT=<dir>        consuming project to wire hooks + AGENTS.md into
#   CODEX_DRY_RUN=1                   preview commands, no writes

$ErrorActionPreference = "Stop"

$SkillSrc     = Join-Path $PSScriptRoot "skills"
$HookSrc      = Join-Path $PSScriptRoot "hooks"
$HJsonTemplate= Join-Path $PSScriptRoot "hooks.json.template"
$AgentsTemplate = Join-Path $PSScriptRoot "templates\AGENTS.md"

$SkillScope   = if ($env:CODEX_SKILL_SCOPE) { $env:CODEX_SKILL_SCOPE } else { "user" }
$TargetProject= if ($env:CODEX_TARGET_PROJECT) { $env:CODEX_TARGET_PROJECT } else { "" }
$DryRun       = if ($env:CODEX_DRY_RUN) { 1 } else { 0 }

$Skills = @(
  "interview","brainstorming","writing-plans","tdd","e2e-playwright",
  "quality-gates","api-contract-testing","db-migration-testing","autoship",
  "refactor","systematic-debugging","code-review","pre-review-cleanup",
  "security-audit","verification","doubt","observe","deprecate",
  "incident-runbook","pr","repo-docs","git-worktrees","setup-project",
  "codemax-gbrain"
)
$Umbrella = @("tapway")

if ($SkillScope -eq "user") {
  $SkillDest = Join-Path $HOME ".agents\skills"
} elseif ($SkillScope -eq "repo") {
  if (-not $TargetProject) { $TargetProject = (Get-Location).Path }
  $SkillDest = Join-Path $TargetProject ".agents\skills"
} else {
  Write-Error "CODEX_SKILL_SCOPE must be 'user' or 'repo' (got: $SkillScope)"
  exit 1
}

Write-Host "Installing Tapway Superpowers into Codex"
Write-Host "  skill scope    : $SkillScope -> $SkillDest"
if ($TargetProject) { Write-Host "  target project : $TargetProject (hooks + AGENTS.md)" }
Write-Host "  dry-run        : $DryRun"
Write-Host ""

function Install-SkillDir {
  param([string]$Name)
  $src  = Join-Path $SkillSrc "$Name"
  $dest = Join-Path $SkillDest $Name
  if (-not (Test-Path (Join-Path $src "SKILL.md"))) {
    Write-Host "  local source missing: $src"
    return $false
  }
  New-Item -ItemType Directory -Force -Path $SkillDest | Out-Null
  if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
  Copy-Item -Recurse -Force $src $dest
  return (Test-Path (Join-Path $dest "SKILL.md"))
}

$installed = 0
$failed = 0
foreach ($skill in ($Skills + $Umbrella)) {
  Write-Host -NoNewline ("  • {0,-22} " -f $skill)
  if ($DryRun -eq 1) {
    Write-Host "(dry-run) -> $SkillDest\$skill"
    $installed++
    continue
  }
  if (Install-SkillDir $skill) { Write-Host "✓"; $installed++ }
  else { Write-Host "✗ FAILED"; $failed++ }
}

# --- Wire hooks + AGENTS.md into a consuming project (optional) ---
if ($TargetProject -and $DryRun -ne 1) {
  if (-not (Test-Path $TargetProject)) { Write-Error "CODEX_TARGET_PROJECT does not exist: $TargetProject"; exit 1 }

  $CodexDir = Join-Path $TargetProject ".codex"
  New-Item -ItemType Directory -Force -Path (Join-Path $CodexDir "hooks") | Out-Null

  Copy-Item -Force $HJsonTemplate (Join-Path $CodexDir "hooks.json")
  Get-ChildItem -Path $HookSrc -Filter "*.sh" | ForEach-Object {
    Copy-Item -Force $_.FullName (Join-Path $CodexDir "hooks")
  }

  $AgentsPath = Join-Path $TargetProject "AGENTS.md"
  if (Test-Path $AgentsPath) {
    Write-Host "  • AGENTS.md exists — skipping template."
  } else {
    Copy-Item -Force $AgentsTemplate $AgentsPath
    Write-Host "  • Wrote $AgentsPath (pipeline directive)."
  }

  Write-Host "  • Wrote $CodexDir\hooks.json"
  Write-Host "  • Copied $((Get-ChildItem $HookSrc -Filter '*.sh').Count) hook scripts to $CodexDir\hooks\"
  Write-Host ""
  Write-Host "⚠️  NEXT: Codex requires a one-time TRUST REVIEW before hooks run."
  Write-Host "   Start Codex in the project and run:  /hooks"
  Write-Host "   See codex/README.md."
}

Write-Host ""
Write-Host "Done. ${installed}/$($Skills.Count + $Umbrella.Count) skills installed (failed=${failed})."
Write-Host "Trigger: `$tapway  (or a step via `$interview, `$brainstorming, `$writing-plans, `$tdd, `$code-review, `$pr)"
if ($failed -gt 0) { exit 1 }
exit 0