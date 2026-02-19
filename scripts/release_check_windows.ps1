$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python -m unittest -q tests/test_backend.py tests/test_regressions.py tests/test_all_actions_emulation.py tests/test_stability_failures.py

pyinstaller --clean --noconfirm build/windows.spec

python scripts/release_smoke_check.py --target windows --artifact dist/AHKManipulator.exe

Write-Host "Windows release check: PASS"
