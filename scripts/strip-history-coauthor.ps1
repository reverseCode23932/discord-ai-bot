# Remove "Co-authored-by: Cursor" from all commit messages and force-push.
# Run from repo root. You must be the repo owner and okay with rewriting history.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$env:FILTER_BRANCH_SQUELCH_WARNING = "1"
git filter-branch -f --msg-filter "python `"$PWD\scripts\strip-coauthor.py`"" -- --all

Write-Host "Done. Verify:" -ForegroundColor Green
git log --format=%B | Select-String "Co-authored-by: Cursor"
Write-Host "If empty, push with: git push --force origin main" -ForegroundColor Yellow
