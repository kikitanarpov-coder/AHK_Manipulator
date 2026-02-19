# AHK v2 Integration

## What is implemented

- Parse AHK v2 scripts:
  - `#Requires AutoHotkey v2.0`
  - global variables
  - functions
  - hotkeys (`F2:: { ... }`)
  - command/call lines (`Click(...)`, `Sleep(...)`, `Send(...)`, etc.)
- Validate script with diagnostics:
  - version checks
  - Windows-specific command hints
  - potentially dangerous command warnings
- Execute:
  - `native` mode: run via `AutoHotkey.exe` (Windows)
  - `emulated` mode: translate to internal task board and execute through backend
  - `auto` mode: native on Windows if AHK is found, otherwise emulated
- Path guard:
  - optional `allowed_root` prevents script execution outside trusted directory

## Backend API

```python
from backend import BackendApplication

app = BackendApplication(...)
script = app.parse_ahk_file("examples/ahk_v2_sample.ahk")
validation = app.validate_ahk_file("examples/ahk_v2_sample.ahk")
result = app.execute_ahk_file(
    "examples/ahk_v2_sample.ahk",
    mode="auto",          # auto | native | emulated
    timeout_sec=30,
    allowed_root="examples",
)
```

## Notes

- On macOS/Linux, Windows-only commands are reported and handled with graceful fallback.
- In emulation mode unsupported commands are converted to log actions (no crash).
- UTF-8 with BOM is supported for `.ahk` files.
