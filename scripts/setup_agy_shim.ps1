Param(
    [string]$TargetDir = "YOURFOLDER\agy-shim"
)

Write-Host "Preparing AGY-Shim in $TargetDir" -ForegroundColor Cyan

# Create or reuse target directory
New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
Set-Location $TargetDir

# Clone or update repository
if (Test-Path ".git") {
    Write-Host "Repository already present, pulling latest..." -ForegroundColor Yellow
    git pull
} else {
    git clone https://github.com/dknewton613-cloud/AGY-Shim.git .
}

# Set AGY_PATH to the default local install location (adjust if needed)
$env:AGY_PATH = "$env:LOCALAPPDATA\agy\bin\agy.exe"
Write-Host "Set AGY_PATH = $env:AGY_PATH"

# Prepend local bin to PATH so wrappers in the repo take precedence in this session
$pwdBin = Join-Path -Path (Get-Location) -ChildPath "bin"
$env:PATH = "$pwdBin;$env:PATH"
Write-Host "Prepended $pwdBin to PATH"

# Opt-in: permission-bypass is unsafe; require explicit confirmation
$consent = Read-Host -Prompt "Enable permission-bypass (AGY_SHIM_ALLOW_BYPASS=1)? Type YES to enable (unsafe)"
if ($consent -eq "YES") {
    $env:AGY_SHIM_ALLOW_BYPASS = "1"
    Write-Host "AGY_SHIM_ALLOW_BYPASS=1 set (unsafe). Use only in isolated environments." -ForegroundColor Red
} else {
    Write-Host "Safe-mode retained (AGY_SHIM_ALLOW_BYPASS not set)." -ForegroundColor Green
}

# Verification
Write-Host "`nVerification:" -ForegroundColor Cyan
Write-Host "where.exe agy:" -ForegroundColor DarkYellow
where.exe agy 2>$null || Write-Host "agy not found in PATH" -ForegroundColor Yellow

Write-Host "`nGet-Command agy:" -ForegroundColor DarkYellow
try { Get-Command agy } catch { Write-Host "agy not found via Get-Command" -ForegroundColor Yellow }

if (-not (Test-Path $env:AGY_PATH)) {
    Write-Host "Warning: agy.exe not found at $env:AGY_PATH" -ForegroundColor Yellow
} else {
    Write-Host "agy.exe found at $env:AGY_PATH" -ForegroundColor Green
}

Write-Host "`nTo start the shim: python -m src.agy_shim.main" -ForegroundColor Cyan
Write-Host "Close this PowerShell window to revert environment changes." -ForegroundColor Cyan
