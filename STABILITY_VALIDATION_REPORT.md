# Stability Validation Report

## 1. Functional Map

### Entry points
- `main.py`:
  - GUI start: `python main.py`
  - CLI demo: `python main.py --cli`

### GUI actions and handlers
- Main toolbar (`ui/main_window.py`):
  - New/Open/Save board
  - Record toggle
  - Run/Stop execution
  - Import/Export AHK
  - Settings dialog
- Right panel (`ui/right_panel.py`):
  - Add action with parameters
  - Edit selected action
  - Row edit/remove
  - Hotkey capture (`Ctrl+Shift+R`)
- Task board (`ui/task_board_widget.py`):
  - Add/remove rows
  - Add/remove/reorder/copy actions
- Keyboard recorder dialog (`ui/key_recorder_dialog.py`)
- Screen overlay (`ui/screen_overlay.py`)

### Backend functions
- Core models: `Coordinates`, `Color`, `Action`, `TaskRow`, `TaskBoard`
- Execution engine: execute, pause/resume, stop, variables
- Action handlers:
  - Mouse: click, move
  - Keyboard: key press
  - Timing: wait
  - Screen: wait pixel color/change, wait image, screenshot
  - Logic: conditional, loop, log, wait text (OCR contract)
  - DB: search/get/iterate/save/check/run row
- Import/Export:
  - AHK import
  - AHK/Python/JSON export
- Services:
  - mouse/keyboard (`pynput` controllers)
  - screen (`mss` + Pillow + OpenCV)
  - database (Excel/CSV)

### Threads and async
- Qt worker thread for board execution:
  - `BackendWorker` moved to `QThread`
  - queued signal execution
- Async execution loop inside worker

### Global listeners
- No global keyboard listener object is used.
- `pynput.Controller` is used for input output only.

## 2. Coverage Matrix

### Unit + integration + stress tests (automated)
- `tests/test_backend.py`
- `tests/test_regressions.py`
- `tests/test_all_actions_emulation.py`
- `tests/test_stability_failures.py`

### Verified by tests
- All `ActionType` have registered handlers.
- End-to-end board execution with every action type.
- Repeated execution (100 runs).
- Repeated CSV database loading (100 loads).
- Stop during execution.
- Conditional `skip_next` and `break`.
- Screenshot failure handling (no crash).
- Missing/corrupt file handling for DB/import.
- Save/load/export/import cycles.
- Backend shutdown closes services.

## 3. Hardening Applied
- Centralized logging + global exception hooks:
  - `app_logging.py`
- Worker thread lifecycle safety:
  - clean thread shutdown on window close
- Resource lifecycle:
  - `BackendApplication.shutdown()`
  - `ScreenService.close()`
- Safer file operations:
  - `pathlib`-based save/load/import/export
- Reduced silent-fail zones:
  - critical runtime paths moved from `print` to structured logging

## 4. Test Execution Result

- Command: `python3 -m unittest -q`
- Result: `Ran 62 tests, OK (skipped=4)`

Skipped tests are GUI-manual scripts requiring `PyQt6` runtime in environment.

## 5. Residual Risks / Not Fully Provable Here

- Full GUI interaction stress (rapid clicks/shortcuts) in real window manager.
- macOS Accessibility/Screen Recording permission behavior.
- Real PyInstaller runtime validation (`.app`/`.exe`) in target OS.
- OCR real implementation for `WAIT_TEXT` (currently explicit contract fallback).

## 6. Production-Readiness Gate

Current codebase is backend-stable under automated stress/failure tests.
For final release sign-off, run these on target hosts:
1. Build with PyInstaller on macOS and Windows.
2. Run GUI smoke + rapid-click scenarios with PyQt6 installed.
3. Validate permissions and real input/output on OS-level controls.
