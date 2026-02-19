#!/usr/bin/env python3
"""
Post-build smoke checks for AHK Manipulator artifacts.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        env=dict(os.environ, QT_QPA_PLATFORM=os.environ.get("QT_QPA_PLATFORM", "offscreen")),
    )
    return proc.returncode, proc.stdout


def check_macos(app_path: Path) -> int:
    exe = app_path / "Contents" / "MacOS" / "AHKManipulator"
    if not exe.exists():
        print(f"FAIL: executable not found: {exe}")
        return 1
    code, out = _run([str(exe), "--cli"])
    if code != 0:
        print("FAIL: macOS artifact CLI run failed")
        print(out)
        return 1
    print("PASS: macOS CLI smoke check")
    return 0


def check_windows(exe_path: Path) -> int:
    if not exe_path.exists():
        print(f"FAIL: executable not found: {exe_path}")
        return 1
    code, out = _run([str(exe_path), "--cli"])
    if code != 0:
        print("FAIL: Windows artifact CLI run failed")
        print(out)
        return 1
    print("PASS: Windows CLI smoke check")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["macos", "windows"], required=True)
    parser.add_argument("--artifact", required=True, help="Path to .app or .exe")
    args = parser.parse_args()

    artifact = Path(args.artifact).expanduser().resolve()
    if args.target == "macos":
        return check_macos(artifact)
    return check_windows(artifact)


if __name__ == "__main__":
    sys.exit(main())
