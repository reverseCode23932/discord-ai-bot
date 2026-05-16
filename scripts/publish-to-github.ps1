# Publishes this project to GitHub (requires Git + GitHub CLI)
# Usage: .\scripts\publish-to-github.ps1
# Optional: .\scripts\publish-to-github.ps1 -RepoName my-bot -Private

param(
    [string]$RepoName = "discord-ai-bot",
    [switch]$Private
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

function Resolve-Gh {
    $cmd = Get-Command gh -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @(
        "${env:ProgramFiles}\GitHub CLI\gh.exe",
        "${env:ProgramFiles(x86)}\GitHub CLI\gh.exe",
        "$env:LOCALAPPDATA\Programs\GitHub CLI\gh.exe"
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) {
            $dir = Split-Path $path -Parent
            if ($env:Path -notlike "*$dir*") {
                $env:Path = "$dir;$env:Path"
            }
            return $path
        }
    }

    throw @"
GitHub CLI (gh) not found.

Install:  winget install GitHub.cli
Then close and reopen PowerShell, or run:
  & '${env:ProgramFiles}\GitHub CLI\gh.exe' auth login
"@
}

$Gh = Resolve-Gh
Write-Host "Using gh: $Gh"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is not installed."
}

& $Gh auth status
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Log in first, then run this script again:"
    Write-Host "  & '$Gh' auth login"
    exit 1
}

if (-not (Test-Path .git)) {
    git init
    git branch -M main
}

git add -A
git status

$msg = "Initial commit: Discord AI bot with OpenAI, TTS, and logging"
git commit -m $msg 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Nothing new to commit (or commit failed)."
}

$visibility = if ($Private) { "--private" } else { "--public" }
& $Gh repo create $RepoName $visibility --source=. --remote=origin --push

$login = & $Gh api user -q .login
Write-Host ""
Write-Host "Done. Open: https://github.com/$login/$RepoName"
