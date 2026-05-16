# Publishes this project to a new GitHub repo (requires GitHub CLI: gh)
# Usage: .\scripts\publish-to-github.ps1
# Optional: .\scripts\publish-to-github.ps1 -RepoName my-bot -Private

param(
    [string]$RepoName = "discord-ai-bot",
    [switch]$Private
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is not installed."
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) is not installed. See https://cli.github.com/"
}

gh auth status | Out-Null

if (-not (Test-Path .git)) {
    git init
    git branch -M main
}

git add -A
git status

$msg = "Initial commit: Discord AI bot with OpenAI, TTS, and logging"
git commit -m $msg 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Nothing new to commit or commit failed."
}

$visibility = if ($Private) { "--private" } else { "--public" }
gh repo create $RepoName $visibility --source=. --remote=origin --push

Write-Host ""
Write-Host "Done. Open: https://github.com/$(gh api user -q .login)/$RepoName"
