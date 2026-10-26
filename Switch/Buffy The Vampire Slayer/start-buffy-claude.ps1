# Launch Claude Code with Buffy research context. No installs, deletions, cloning or privilege changes.
# Usage (from a cloned copy of this repository):
#   & '.\Switch\Buffy The Vampire Slayer\start-buffy-claude.ps1'
[CmdletBinding()]
param(
    [string]$WorkspaceRoot = 'C:\Users\Public\App Developement\Decomps - Recomps'
)
$ErrorActionPreference = 'Stop'
$GameDir = Join-Path $WorkspaceRoot 'Projects\Buffy The Vampire Slayer\Game Files\Buffy the Vampire Slayer (Europe)\Buffy the Vampire Slayer (Europe)'
$ToolsSources = Join-Path $WorkspaceRoot 'Tools\Sources'
$Claude = Get-Command claude -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $Claude) { throw 'Claude Code CLI not found. Verify installation with: claude --version' }
if (-not (Test-Path -LiteralPath $GameDir -PathType Container)) {
    throw "Private Buffy game directory was not found: $GameDir"
}
$ArgsForClaude = @('--add-dir', $GameDir)
if (Test-Path -LiteralPath $ToolsSources -PathType Container) {
    $ArgsForClaude += @('--add-dir', $ToolsSources)
} else {
    Write-Warning "Shared tools directory missing; Claude should inventory other source locations: $ToolsSources"
}
$Prompt = @'
Run the initial Buffy the Vampire Slayer (2002 Xbox EUROPE) -> native Switch 1 FEASIBILITY audit. Read CLAUDE.md, FEASIBILITY-CONTRACT.md, TOOL-SOURCES.md and ../SHARED-KNOWLEDGE.md. Inspect the granted private game files READ-ONLY and public tools checkouts. Work on a separate research/buffy-* branch, do not modify Black. Favor decisive read-only probes, record exact evidence and limits, and produce BUFFY-FEASIBILITY-REPORT.md, BUFFY-EVIDENCE.json, TOOL-LOCK.json. Commit and push ONLY safe documentation if git authentication permits; otherwise explicitly report local outputs. Apply the owner's low-cost STOP/GO constraints. No whole-game codegen, huge builds, new GPU engine or game data in Git.
'@
Write-Host "[Buffy] Repo working directory: $PSScriptRoot"
Write-Host "[Buffy] Private game folder (read-only intent): $GameDir"
Write-Host "[Buffy] Claude Code will ask for normal tool permissions; review any writes."
Push-Location -LiteralPath $PSScriptRoot
try {
    & $Claude.Source @ArgsForClaude $Prompt
} finally {
    Pop-Location
}
