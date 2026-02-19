#!/usr/bin/env python3
"""
Subprocess worker for global input recording via pynput.
Runs outside the Qt process to isolate native crashes on macOS.
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import threading
import time
from typing import Set


def _now_ms() -> int:
    return int(time.time() * 1000)


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _normalize_key_name(key_obj) -> str:
    raw = str(key_obj)
    if raw.startswith("Key."):
        raw = raw[4:]
    low = raw.lower()
    mapping = {
        "ctrl_l": "ctrl",
        "ctrl_r": "ctrl",
        "shift_l": "shift",
        "shift_r": "shift",
        "alt_l": "alt",
        "alt_r": "alt",
        "cmd": "cmd",
        "esc": "esc",
        "enter": "enter",
        "tab": "tab",
        "space": "space",
    }
    if low in mapping:
        return mapping[low]
    if len(low) == 1:
        return low
    return low


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stop-combo", default="cmd+1")
    parser.add_argument("--startup-ignore-ms", type=int, default=500)
    args = parser.parse_args()

    stop_event = threading.Event()
    started_ts = _now_ms()
    pressed_mods: Set[str] = set()
    pressed_keys: Set[str] = set()

    def _sigterm_handler(_signum, _frame):
        stop_event.set()

    signal.signal(signal.SIGTERM, _sigterm_handler)
    signal.signal(signal.SIGINT, _sigterm_handler)

    try:
        from pynput import keyboard, mouse
    except Exception as exc:
        _emit({"type": "error", "message": f"pynput import failed: {exc}"})
        return 2

    def on_click(x, y, button, pressed):
        if stop_event.is_set():
            return False
        if not pressed:
            return
        now = _now_ms()
        if now - started_ts < args.startup_ignore_ms:
            return
        btn = "left"
        if button == mouse.Button.right:
            btn = "right"
        elif button == mouse.Button.middle:
            btn = "middle"
        _emit({
            "type": "event",
            "event": {
                "type": "click",
                "button": btn,
                "x": int(x),
                "y": int(y),
                "ts": now,
            },
        })

    def on_press(key):
        if stop_event.is_set():
            return False
        now = _now_ms()
        if now - started_ts < args.startup_ignore_ms:
            return

        key_name = _normalize_key_name(key)
        if key_name in {"ctrl", "shift", "alt", "cmd"}:
            pressed_mods.add(key_name)
            return

        if key_name in pressed_keys:
            return
        pressed_keys.add(key_name)

        combo_parts = []
        for mod in ("ctrl", "alt", "shift", "cmd"):
            if mod in pressed_mods:
                combo_parts.append(mod)
        combo_parts.append(key_name)
        combo = "+".join(combo_parts)

        if combo == args.stop_combo:
            _emit({"type": "stop_requested"})
            stop_event.set()
            return False

        _emit({"type": "event", "event": {"type": "key", "key": combo, "ts": now}})

    def on_release(key):
        key_name = _normalize_key_name(key)
        if key_name in {"ctrl", "shift", "alt", "cmd"}:
            pressed_mods.discard(key_name)
        else:
            pressed_keys.discard(key_name)

    mouse_listener = None
    keyboard_listener = None
    try:
        mouse_listener = mouse.Listener(on_click=on_click)
        keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        mouse_listener.start()
        keyboard_listener.start()

        while not stop_event.is_set():
            time.sleep(0.02)
    except Exception as exc:
        _emit({"type": "error", "message": f"listener runtime error: {exc}"})
        return 3
    finally:
        for listener in (mouse_listener, keyboard_listener):
            if listener is not None:
                try:
                    listener.stop()
                except Exception:
                    pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
