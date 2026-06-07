[CmdletBinding()]
param(
    [string]$OutputRoot = (Join-Path (Split-Path $PSScriptRoot -Parent) "bin"),
    [switch]$IncludeRuntime
)

$ErrorActionPreference = "Stop"
$source = Join-Path $PSScriptRoot "launcher.cs"
$repoRoot = Split-Path $PSScriptRoot -Parent
$providers = @("claude", "codex", "copilot", "cursor", "cursor-agent", "gemini")
$compilerCandidates = @(
    (Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"),
    (Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe")
)
$compiler = $compilerCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not (Test-Path -LiteralPath $source)) {
    throw "Launcher source not found: $source"
}
if (-not $compiler) {
    throw "The Windows .NET Framework C# compiler (csc.exe) was not found."
}

foreach ($provider in $providers) {
    $providerDir = if ($provider -eq "cursor-agent") { "cursor" } else { $provider }
    $outputDir = Join-Path $OutputRoot $providerDir
    $outputPath = Join-Path $outputDir "$provider.exe"
    New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

    & $compiler /nologo /target:exe "/out:$outputPath" $source
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to compile $outputPath"
    }
    Write-Host "Built $outputPath"
}

if ($IncludeRuntime) {
    $runtimeRoot = Split-Path $OutputRoot -Parent
    Copy-Item -LiteralPath (Join-Path $repoRoot "src") `
        -Destination (Join-Path $runtimeRoot "src") `
        -Recurse `
        -Force
    Write-Host "Copied Python runtime source for executable verification."
}
