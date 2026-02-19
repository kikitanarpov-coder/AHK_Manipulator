$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Script
    )

    Write-Host "==> $Name"
    & $Script
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Name (exit code $LASTEXITCODE)"
    }
}

Invoke-Step -Name "Run tests" -Script {
    python -m unittest -q tests/test_backend.py tests/test_regressions.py tests/test_all_actions_emulation.py tests/test_stability_failures.py
}

Invoke-Step -Name "Build Windows EXE" -Script {
    pyinstaller --clean --noconfirm build/windows.spec
}

# Accept both onefile and onedir outputs.
$artifactCandidates = @(
    "dist/AHKManipulator.exe",
    "dist/AHKManipulator/AHKManipulator.exe"
)
$artifact = $artifactCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $artifact) {
    Write-Host "Dist contents:" -ForegroundColor Yellow
    if (Test-Path "dist") { Get-ChildItem -Recurse dist | ForEach-Object { Write-Host $_.FullName } }
    throw "Build output not found in expected locations"
}

Invoke-Step -Name "Smoke check" -Script {
    python scripts/release_smoke_check.py --target windows --artifact $artifact
}

Write-Host "Windows release check: PASS ($artifact)"
