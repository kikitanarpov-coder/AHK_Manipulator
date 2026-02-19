# Release Checklist

## Preflight

- Virtual environment is active.
- Dependencies installed:
  - `pip install -r requirements.txt`
  - `pip install pyinstaller`

## Automated checks

### macOS

Run:

```bash
bash scripts/release_check_macos.sh
```

Pass criteria:
- Unit/integration/stability tests pass.
- `dist/AHKManipulator.app` exists.
- CLI smoke check from bundle executable passes.

### Windows

Run on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/release_check_windows.ps1
```

Pass criteria:
- Unit/integration/stability tests pass.
- `dist/AHKManipulator.exe` exists.
- CLI smoke check for `.exe` passes.

## Manual GUI checks (required on target OS)

1. Start app and create/open/save board repeatedly.
2. Run/Stop execution quickly several times.
3. Open overlay and close during execution.
4. Import/export AHK.
5. Add/remove/reorder/copy actions.
6. Open settings and add/remove DB paths.
7. Close app while worker thread is active.

Pass criteria:
- No crash.
- No freeze.
- No unhandled exception dialogs.
- Expected state after each action.

## OS permission checks

### macOS
- Accessibility permission granted.
- Screen Recording permission granted.

### Windows
- Defender/SmartScreen does not block local run (or is explicitly approved for internal QA).

## Artifacts

- macOS: `dist/AHKManipulator.app`
- Windows: `dist/AHKManipulator.exe`

Store test log and release commit hash with artifacts.
