#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 -m unittest -q tests/test_backend.py tests/test_regressions.py tests/test_all_actions_emulation.py tests/test_stability_failures.py

pyinstaller --clean --noconfirm build/macos.spec

python3 scripts/release_smoke_check.py --target macos --artifact dist/AHKManipulator.app

echo "macOS release check: PASS"
