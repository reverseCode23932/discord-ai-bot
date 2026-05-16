# Log in to GitHub CLI (works even if 'gh' is not on PATH yet)
$GhPaths = @(
    "${env:ProgramFiles}\GitHub CLI\gh.exe",
    "${env:ProgramFiles(x86)}\GitHub CLI\gh.exe",
    "$env:LOCALAPPDATA\Programs\GitHub CLI\gh.exe"
)

$Gh = $null
foreach ($path in $GhPaths) {
    if (Test-Path $path) { $Gh = $path; break }
}

if (-not $Gh) {
    Write-Host "GitHub CLI not found. Install it:"
    Write-Host "  winget install GitHub.cli"
    Write-Host "Then close and reopen PowerShell and run this script again."
    exit 1
}

$dir = Split-Path $Gh -Parent
if ($env:Path -notlike "*$dir*") {
    $env:Path = "$dir;$env:Path"
    Write-Host "Added to PATH for this session: $dir"
    Write-Host "Tip: restart PowerShell so 'gh' works everywhere."
    Write-Host ""
}

& $Gh auth login
