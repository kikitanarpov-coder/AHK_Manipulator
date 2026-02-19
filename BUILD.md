# Build Instructions

## 1) Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
```

## 2) Run Tests

```bash
python3 -m unittest -q tests/test_backend.py tests/test_regressions.py tests/test_all_actions_emulation.py tests/test_stability_failures.py
```

## 3) Build for macOS (.app)

```bash
pyinstaller --clean --noconfirm build/macos.spec
```

Output:
- `dist/AHKManipulator.app`

Notes:
- On macOS grant Accessibility + Screen Recording permissions to the built app.
- Unsigned app may require Gatekeeper override during local testing.
- Automated release check: `bash scripts/release_check_macos.sh`

## 4) Build for Windows (.exe)

Run on Windows machine/CI:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --clean --noconfirm build/windows.spec
```

Output:
- `dist/AHKManipulator.exe`
- Automated release check: `powershell -ExecutionPolicy Bypass -File scripts/release_check_windows.ps1`

## 5) Runtime Arguments

- Default: GUI start (`python main.py`)
- CLI demo: `python main.py --cli`
