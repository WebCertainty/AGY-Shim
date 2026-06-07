<#
.SYNOPSIS
    Setup, maintain, and verify the AGY-Shim installation.
.DESCRIPTION
    A comprehensive tool to install, uninstall, and verify the AGY-Shim configuration
    in both session-only (temporary) and permanent User scopes. Isolates each wrapper
    identity in its own bin subdirectory to prevent shadowing of other genuine CLIs.
.PARAMETER Action
    The action to perform. Options: Install, Uninstall, Verify. Default is Install.
.PARAMETER Scope
    The scope of environment variables and PATH modification. Options: User (permanent), Session (temporary). Default is User.
.PARAMETER Provider
    The provider to masquerade (e.g., gemini, copilot, claude, codex, cursor). If not specified on Install, the script prompts the user.
.PARAMETER AgyPath
    Explicit path to agy.exe. Defaults to an existing AGY_PATH value, then %LOCALAPPDATA%\agy\bin\agy.exe.
.PARAMETER Bypass
    Set this switch to permanently or temporarily enable the permission bypass flag (AGY_SHIM_ALLOW_BYPASS=1).
.PARAMETER Help
    Show detailed usage instructions.
.EXAMPLE
    .\scripts\setup_agy_shim.ps1 -Action Install -Scope User -Provider copilot -Bypass
    Installs the shim permanently for Copilot with permission bypass enabled.
.EXAMPLE
    .\scripts\setup_agy_shim.ps1 -Action Verify
    Verifies the current shim configuration and wrapper precedence.
.EXAMPLE
    .\scripts\setup_agy_shim.ps1 -Action Uninstall -Scope User
    Removes the shim and environment variables permanently from the User account.
#>
Param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("Install", "Uninstall", "Verify")]
    [string]$Action = "Install",

    [Parameter(Mandatory=$false)]
    [ValidateSet("User", "Session")]
    [string]$Scope = "User",

    [Parameter(Mandatory=$false)]
    [ValidateSet("gemini", "copilot", "claude", "codex", "cursor")]
    [string]$Provider,

    [Parameter(Mandatory=$false)]
    [string]$AgyPath,

    [Parameter(Mandatory=$false)]
    [switch]$Bypass,

    [Parameter(Mandatory=$false)]
    [switch]$Help
)

# --- Help Display Function ---
function Show-Help {
    Write-Host @"

AGY-Shim Setup & Maintenance Utility
====================================

Usage:
  .\scripts\setup_agy_shim.ps1 [-Action <Install|Uninstall|Verify>] [-Scope <User|Session>] [-Provider <name>] [-AgyPath <path>] [-Bypass] [-Help]

Parameters:
  -Action       Action to perform:
                  Install   - Configure wrappers on PATH and set env variables (Default).
                  Uninstall - Cleanly remove wrappers from PATH and clear env variables.
                  Verify    - Verify PATH precedence and variable configurations.

  -Scope        Where to apply changes:
                  User      - Permanent configuration for your Windows User account (Default).
                  Session   - Temporary configuration for the current PowerShell terminal session only.

  -Provider     Directly specify the provider wrapper to configure:
                  gemini, copilot, claude, codex, cursor
                  (If omitted during Install, you will be prompted to select one).

  -AgyPath      Explicit path to agy.exe. If omitted, the script preserves an
                existing AGY_PATH value or uses %LOCALAPPDATA%\agy\bin\agy.exe.

  -Bypass       Flag/Switch to enable AGY_SHIM_ALLOW_BYPASS=1 (permits executing prompts without checks).

  -Help         Show this help information.

Examples:
  1. Permanent install for Copilot (Bypassing permissions):
     .\scripts\setup_agy_shim.ps1 -Action Install -Scope User -Provider copilot -Bypass

  2. Temporary session-only install for Gemini:
     .\scripts\setup_agy_shim.ps1 -Action Install -Scope Session -Provider gemini

  3. Verify shim status:
     .\scripts\setup_agy_shim.ps1 -Action Verify

  4. Permanent uninstall:
     .\scripts\setup_agy_shim.ps1 -Action Uninstall -Scope User

"@ -ForegroundColor White
}

if ($Help) {
    Show-Help
    exit 0
}

# --- Paths Setup ---
$repoRoot = Split-Path -Path $PSScriptRoot -Parent
$binPath = Join-Path -Path $repoRoot -ChildPath "bin"
$defaultAgyPath = "$env:LOCALAPPDATA\agy\bin\agy.exe"
$allProviders = @("gemini", "copilot", "claude", "codex", "cursor")

# --- Helper functions to manage environment variables ---
function Get-EnvVar([string]$name, [string]$scope) {
    if ($scope -eq "User") {
        return [Environment]::GetEnvironmentVariable($name, "User")
    } else {
        return Get-Item -Path "env:$name" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Value
    }
}

function Set-EnvVar([string]$name, [string]$value, [string]$scope) {
    if ($scope -eq "User") {
        [Environment]::SetEnvironmentVariable($name, $value, "User")
    } else {
        Set-Item -Path "env:$name" -Value $value
    }
}

function Remove-EnvVar([string]$name, [string]$scope) {
    if ($scope -eq "User") {
        [Environment]::SetEnvironmentVariable($name, $null, "User")
    } else {
        Remove-Item -Path "env:$name" -ErrorAction SilentlyContinue
    }
}

function Test-IsShimCommand([string]$candidate, [string]$providerBin) {
    if (-not $candidate) {
        return $false
    }

    try {
        $candidatePath = [IO.Path]::GetFullPath($candidate)
        $providerPath = [IO.Path]::GetFullPath($providerBin).TrimEnd(
            [IO.Path]::DirectorySeparatorChar,
            [IO.Path]::AltDirectorySeparatorChar
        ) + [IO.Path]::DirectorySeparatorChar
        return $candidatePath.StartsWith(
            $providerPath,
            [StringComparison]::OrdinalIgnoreCase
        )
    } catch {
        return $false
    }
}

# --- Action: Verify ---
function Verify-Shim {
    Write-Host "`n=== AGY-Shim Status Verification ===" -ForegroundColor Cyan
    
    # Check Environment Variables (Session Scope)
    $sessBypass = Get-EnvVar "AGY_SHIM_ALLOW_BYPASS" "Session"
    $sessAgyPath = Get-EnvVar "AGY_PATH" "Session"
    
    # Check Environment Variables (User Scope)
    $userBypass = Get-EnvVar "AGY_SHIM_ALLOW_BYPASS" "User"
    $userAgyPath = Get-EnvVar "AGY_PATH" "User"
    
    Write-Host "`nEnvironment Variables:"
    Write-Host "  Session Scope:" -ForegroundColor Gray
    $sessColor = if ($sessBypass -eq "1") { "Yellow" } else { "Green" }
    Write-Host "    AGY_SHIM_ALLOW_BYPASS = $(if ($sessBypass) { $sessBypass } else { 'Not Set (Safe Mode)' })" -ForegroundColor $sessColor
    Write-Host "    AGY_PATH              = $(if ($sessAgyPath) { $sessAgyPath } else { 'Not Set (Auto-detect)' })"
    
    Write-Host "  User Scope (Permanent):" -ForegroundColor Gray
    $userColor = if ($userBypass -eq "1") { "Yellow" } else { "Green" }
    Write-Host "    AGY_SHIM_ALLOW_BYPASS = $(if ($userBypass) { $userBypass } else { 'Not Set (Safe Mode)' })" -ForegroundColor $userColor
    Write-Host "    AGY_PATH              = $(if ($userAgyPath) { $userAgyPath } else { 'Not Set (Auto-detect)' })"

    # Verify agy.exe presence
    $agyToTest = if ($sessAgyPath) {
        $sessAgyPath
    } elseif ($userAgyPath) {
        $userAgyPath
    } else {
        $defaultAgyPath
    }
    if (Test-Path $agyToTest) {
        Write-Host "  Local agy.exe status  : Found at $agyToTest" -ForegroundColor Green
    } else {
        Write-Host "  Local agy.exe status  : NOT found at $agyToTest (Ensure Antigravity is installed)" -ForegroundColor Red
    }

    # Verify wrapper precedence
    Write-Host "`nWrapper Precedence (where.exe check):"
    
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    
    foreach ($p in $allProviders) {
        Write-Host "  Provider '$p':" -ForegroundColor DarkYellow
        $pBin = Join-Path -Path $binPath -ChildPath $p
        
        $cmdNames = if ($p -eq "cursor") { @("cursor", "cursor-agent") } else { @($p) }
        
        foreach ($cmdName in $cmdNames) {
            $pCmd = Join-Path -Path $pBin -ChildPath "$cmdName.exe"
            if (-not (Test-Path $pCmd)) {
                $pCmd = Join-Path -Path $pBin -ChildPath "$cmdName.cmd"
            }
            $paths = @(where.exe $cmdName 2>$null)
            $labelPrefix = if ($cmdNames.Count -gt 1) { "    [$cmdName] " } else { "    " }
            
            if ($paths.Count -gt 0) {
                $isShimFirst = Test-IsShimCommand $paths[0] $pBin
                foreach ($path in $paths) {
                    $color = if (Test-IsShimCommand $path $pBin) { "Cyan" } else { "DarkGray" }
                    Write-Host "${labelPrefix}-> $path" -ForegroundColor $color
                }
                if ($isShimFirst) {
                    if ($Scope -eq "User" -and $userPath -notlike "*$pBin*") {
                        Write-Host "    Result ($cmdName): Pending Removal (Registry updated - restart PowerShell / GUI host to update PATH)" -ForegroundColor Yellow
                    } else {
                        Write-Host "    Result ($cmdName): Active (Shim takes precedence)" -ForegroundColor Green
                    }
                } else {
                    if ($userPath -like "*$pBin*") {
                        Write-Host "${labelPrefix}-> Installed at $pCmd" -ForegroundColor Cyan
                        Write-Host "    Result ($cmdName): Pending (Registry updated - restart PowerShell / GUI host to update PATH)" -ForegroundColor Yellow
                    } else {
                        Write-Host "    Result ($cmdName): Shim not active (another CLI takes precedence)" -ForegroundColor Gray
                    }
                }
            } else {
                if ($userPath -like "*$pBin*" -and (Test-Path $pCmd)) {
                    Write-Host "${labelPrefix}-> Installed at $pCmd" -ForegroundColor Cyan
                    Write-Host "    Result ($cmdName): Pending (Registry updated - restart PowerShell / GUI host to update PATH)" -ForegroundColor Yellow
                } else {
                    Write-Host "${labelPrefix}-> (Not found on PATH)" -ForegroundColor Gray
                }
            }
        }
    }
    Write-Host ""
}

# Detect if run without parameters (Interactive Wizard mode)
$isInteractiveWizard = $PSBoundParameters.Count -eq 0

if ($isInteractiveWizard) {
    Write-Host "`n=== AGY-Shim Setup Wizard ===" -ForegroundColor Cyan
    Write-Host "No parameters specified. Starting interactive guide..."
    
    # 1. Action Choice
    Write-Host "`nSelect an action to perform:"
    Write-Host "  [1] Install (Default)" -ForegroundColor Green
    Write-Host "  [2] Verify status" -ForegroundColor Yellow
    Write-Host "  [3] Uninstall" -ForegroundColor Red
    $actChoice = Read-Host "Select a number (1-3) [1]"
    
    if ($actChoice -eq "2") {
        $Action = "Verify"
    } elseif ($actChoice -eq "3") {
        $Action = "Uninstall"
    } else {
        $Action = "Install"
    }
    
    # 2. Scope Choice (for Install/Uninstall)
    if ($Action -ne "Verify") {
        Write-Host "`nSelect configuration scope:"
        Write-Host "  [1] Permanent (User Scope) - Recommended for GUI hosts like Clairvoyance" -ForegroundColor Green
        Write-Host "  [2] Temporary (Session Scope) - Active in this terminal session only" -ForegroundColor Yellow
        $scopeChoice = Read-Host "Select a number (1-2) [1]"
        
        if ($scopeChoice -eq "2") {
            $Scope = "Session"
        } else {
            $Scope = "User"
        }
    }
}

if ($Action -eq "Verify") {
    Verify-Shim
    exit 0
}

# --- Action: Uninstall ---
if ($Action -eq "Uninstall") {
    Write-Host "`nUninstalling AGY-Shim (Scope: $Scope)..." -ForegroundColor Cyan
    
    # 1. Clean Path
    if ($Scope -eq "User") {
        $oldPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if (-not $oldPath) { $oldPath = "" }
        $pathParts = $oldPath -split ";"
        $filteredParts = $pathParts | Where-Object {
            $path = $_.Trim()
            $isShimPath = $false
            if ($path -eq $binPath) { $isShimPath = $true } # Backward compatibility for old bin
            foreach ($p in $allProviders) {
                $pBin = Join-Path -Path $binPath -ChildPath $p
                if ($path -eq $pBin) { $isShimPath = $true }
            }
            -not $isShimPath
        }
        $newPath = ($filteredParts | Where-Object { $_ -ne "" }) -join ";"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Host "  Removed shim directories from User PATH." -ForegroundColor Green
        
        # Also clean up from current session PATH for clean status verification
        $sessionPathParts = $env:PATH -split ";"
        $sessionFiltered = $sessionPathParts | Where-Object {
            $path = $_.Trim()
            $isShimPath = $false
            if ($path -eq $binPath) { $isShimPath = $true }
            foreach ($p in $allProviders) {
                $pBin = Join-Path -Path $binPath -ChildPath $p
                if ($path -eq $pBin) { $isShimPath = $true }
            }
            -not $isShimPath
        }
        $env:PATH = ($sessionFiltered | Where-Object { $_ -ne "" }) -join ";"
    } else {
        $pathParts = $env:PATH -split ";"
        $filteredParts = $pathParts | Where-Object {
            $path = $_.Trim()
            $isShimPath = $false
            if ($path -eq $binPath) { $isShimPath = $true } # Backward compatibility for old bin
            foreach ($p in $allProviders) {
                $pBin = Join-Path -Path $binPath -ChildPath $p
                if ($path -eq $pBin) { $isShimPath = $true }
            }
            -not $isShimPath
        }
        $env:PATH = ($filteredParts | Where-Object { $_ -ne "" }) -join ";"
        Write-Host "  Removed shim directories from current Session PATH." -ForegroundColor Green
    }
    
    # 2. Clean Environment Variables
    Remove-EnvVar "AGY_SHIM_ALLOW_BYPASS" $Scope
    Remove-EnvVar "AGY_PATH" $Scope
    if ($Scope -eq "User") {
        Remove-EnvVar "AGY_SHIM_ALLOW_BYPASS" "Session"
        Remove-EnvVar "AGY_PATH" "Session"
    }
    Write-Host "  Cleared AGY_SHIM_ALLOW_BYPASS and AGY_PATH variables." -ForegroundColor Green
    
    Verify-Shim
    Write-Host "Uninstall complete. Please restart PowerShell and your GUI host / Clairvoyance for changes to take effect." -ForegroundColor Green
    exit 0
}

# --- Action: Install ---
# Detect existing CLIs and build recommendations
$installedList = [System.Collections.Generic.List[string]]::new()
$notInstalledList = [System.Collections.Generic.List[string]]::new()

foreach ($p in $allProviders) {
    if (where.exe $p 2>$null) {
        $installedList.Add($p)
    } else {
        $notInstalledList.Add($p)
    }
}

if (-not $Provider) {
    Write-Host "`n=== Provider Selection for Installation ===" -ForegroundColor Cyan
    Write-Host "To masquerade the Antigravity agent, please select a provider wrapper identity."
    Write-Host "Tip: It is highly recommended to select a provider you DO NOT have installed so it does not conflict with genuine tools.`n"
    
    $index = 1
    $menuItems = @()
    
    # Add not installed first (Recommended)
    foreach ($p in $notInstalledList) {
        $recText = "Not Installed"
        if ($p -eq "gemini" -or $p -eq "copilot") {
            $recText += " - ACTIVE EVALUATION"
            $color = "Green"
        } elseif ($p -eq "cursor") {
            $recText += " - HOST VALIDATION REQUIRED"
            $color = "Red"
        } else {
            $recText += " - NOT VERIFIED"
            $color = "Gray"
        }
        Write-Host "  [$index] $p ($recText)" -ForegroundColor $color
        $menuItems += $p
        $index++
    }
    
    # Add installed second
    foreach ($p in $installedList) {
        $warnText = "Currently Installed - Warning: Overrides genuine CLI"
        if ($p -eq "gemini" -or $p -eq "copilot") {
            $warnText += " (ACTIVE EVALUATION)"
            $color = "Yellow"
        } elseif ($p -eq "cursor") {
            $warnText += " (HOST VALIDATION REQUIRED)"
            $color = "Red"
        } else {
            $warnText += " (NOT VERIFIED)"
            $color = "Yellow"
        }
        Write-Host "  [$index] $p ($warnText)" -ForegroundColor $color
        $menuItems += $p
        $index++
    }
    
    Write-Host ""
    $selection = Read-Host "Select a number (1-$($index-1))"
    
    if ($selection -match '^\d+$' -and [int]$selection -ge 1 -and [int]$selection -lt $index) {
        $Provider = $menuItems[[int]$selection - 1]
    } else {
        Write-Host "Invalid selection. Aborting installation." -ForegroundColor Red
        exit 1
    }
}

# Warn that provider identities require host-specific validation
if ($Provider -eq "cursor") {
    Write-Host "`nWARNING: The Cursor identity has not passed current live-host validation." -ForegroundColor Yellow
    $confirmCursor = Read-Host "Proceed with Cursor installation anyway? (Y/N) [N]"
    if ($confirmCursor -ne "Y" -and $confirmCursor -ne "y") {
        Write-Host "Installation aborted." -ForegroundColor Red
        exit 1
    }
} elseif ($Provider -notin @("gemini", "copilot")) {
    Write-Host "`nWARNING: The selected identity ($Provider) has version-detection evidence only; live-host interoperability is not confirmed." -ForegroundColor Yellow
    $confirmUnverified = Read-Host "Proceed anyway? (Y/N) [Y]"
    if ($confirmUnverified -eq "N" -or $confirmUnverified -eq "n") {
        Write-Host "Installation aborted." -ForegroundColor Red
        exit 1
    }
}

$targetBinPath = Join-Path -Path $binPath -ChildPath $Provider
$providerCommand = if ($Provider -eq "cursor") { "cursor" } else { $Provider }
$providerExe = Join-Path -Path $targetBinPath -ChildPath "$providerCommand.exe"
$providerCmd = Join-Path -Path $targetBinPath -ChildPath "$providerCommand.cmd"

if (-not (Test-Path -LiteralPath $providerExe) -and -not (Test-Path -LiteralPath $providerCmd)) {
    Write-Host "Installation aborted. No wrapper was found for '$Provider' in $targetBinPath." -ForegroundColor Red
    exit 1
}

if (-not $AgyPath) {
    $AgyPath = Get-EnvVar "AGY_PATH" "Session"
}
if (-not $AgyPath) {
    $AgyPath = Get-EnvVar "AGY_PATH" "User"
}
if (-not $AgyPath) {
    $AgyPath = $defaultAgyPath
}
$AgyPath = [Environment]::ExpandEnvironmentVariables($AgyPath)

if (-not (Test-Path -LiteralPath $AgyPath -PathType Leaf)) {
    Write-Host "Installation aborted. agy.exe was not found at: $AgyPath" -ForegroundColor Red
    Write-Host "Install and authenticate Antigravity first, or pass -AgyPath <path>." -ForegroundColor Yellow
    exit 1
}
$AgyPath = (Resolve-Path -LiteralPath $AgyPath).Path

# Consent must be explicit and must happen before PATH or environment mutation.
if (-not $Bypass) {
    Write-Host "`n[Security Warning] Required Permission Bypass" -ForegroundColor Yellow
    Write-Host "Antigravity runs prompts in a headless background process via this shim."
    Write-Host "Because it cannot prompt you interactively to confirm permissions, enabling"
    Write-Host "AGY_SHIM_ALLOW_BYPASS=1 is REQUIRED for prompt execution."
    Write-Host "This allows agy.exe to run with --dangerously-skip-permissions."
    Write-Host "For security implications, see README.md and docs/security-model.md."

    $confirmBypass = Read-Host "Type Y to accept this risk and continue [N]"
    if ($confirmBypass -cne "Y" -and $confirmBypass -cne "y") {
        Write-Host "Installation cancelled. No environment changes were made." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "`nInstalling AGY-Shim..." -ForegroundColor Cyan
Write-Host "  Target Provider wrapper: $Provider" -ForegroundColor White
Write-Host "  Scope: $Scope (applying changes...)" -ForegroundColor White
Write-Host "  Antigravity executable: $AgyPath" -ForegroundColor White

$previousUserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$previousSessionPath = $env:PATH
$previousScopeAgyPath = Get-EnvVar "AGY_PATH" $Scope
$previousScopeBypass = Get-EnvVar "AGY_SHIM_ALLOW_BYPASS" $Scope
$previousSessionAgyPath = Get-EnvVar "AGY_PATH" "Session"
$previousSessionBypass = Get-EnvVar "AGY_SHIM_ALLOW_BYPASS" "Session"

try {
    # 1. Update PATH
    if ($Scope -eq "User") {
        $oldPath = if ($null -eq $previousUserPath) { "" } else { $previousUserPath }
        $userPathParts = @($oldPath -split ";" | Where-Object { $_ })
        if ($targetBinPath -notin $userPathParts) {
            $newPath = (@($targetBinPath) + $userPathParts) -join ";"
            [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
            Write-Host "  Prepended shim bin\$Provider directory to permanent User PATH." -ForegroundColor Green
        } else {
            Write-Host "  Shim bin\$Provider directory is already present in User PATH." -ForegroundColor Gray
        }
    }

    $sessionPathParts = @($env:PATH -split ";" | Where-Object { $_ })
    if ($targetBinPath -notin $sessionPathParts) {
        $env:PATH = (@($targetBinPath) + $sessionPathParts) -join ";"
        Write-Host "  Prepended shim bin\$Provider directory to current Session PATH." -ForegroundColor Green
    } else {
        Write-Host "  Shim bin\$Provider directory is already present in Session PATH." -ForegroundColor Gray
    }

    # 2. Configure AGY_PATH
    Set-EnvVar "AGY_PATH" $AgyPath $Scope
    if ($Scope -eq "User") {
        Set-EnvVar "AGY_PATH" $AgyPath "Session"
    }
    Write-Host "  Set AGY_PATH = $AgyPath" -ForegroundColor Green

    # 3. Configure the explicitly accepted bypass.
    Set-EnvVar "AGY_SHIM_ALLOW_BYPASS" "1" $Scope
    if ($Scope -eq "User") {
        Set-EnvVar "AGY_SHIM_ALLOW_BYPASS" "1" "Session"
    }
    Write-Host "  Set AGY_SHIM_ALLOW_BYPASS = 1 (Required for prompt execution)" -ForegroundColor Yellow

} catch {
    Write-Host "Installation failed. Restoring the previous environment configuration..." -ForegroundColor Red
    if ($Scope -eq "User") {
        [Environment]::SetEnvironmentVariable("Path", $previousUserPath, "User")
    }
    $env:PATH = $previousSessionPath

    if ($null -eq $previousScopeAgyPath) {
        Remove-EnvVar "AGY_PATH" $Scope
    } else {
        Set-EnvVar "AGY_PATH" $previousScopeAgyPath $Scope
    }
    if ($null -eq $previousScopeBypass) {
        Remove-EnvVar "AGY_SHIM_ALLOW_BYPASS" $Scope
    } else {
        Set-EnvVar "AGY_SHIM_ALLOW_BYPASS" $previousScopeBypass $Scope
    }

    if ($Scope -eq "User") {
        if ($null -eq $previousSessionAgyPath) {
            Remove-EnvVar "AGY_PATH" "Session"
        } else {
            Set-EnvVar "AGY_PATH" $previousSessionAgyPath "Session"
        }
        if ($null -eq $previousSessionBypass) {
            Remove-EnvVar "AGY_SHIM_ALLOW_BYPASS" "Session"
        } else {
            Set-EnvVar "AGY_SHIM_ALLOW_BYPASS" $previousSessionBypass "Session"
        }
    }

    Write-Error $_
    exit 1
}

Verify-Shim

Write-Host "Installation complete! Please restart PowerShell and your GUI host / Clairvoyance for changes to take effect." -ForegroundColor Green
