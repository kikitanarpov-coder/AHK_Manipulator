"""
Менеджер записи пользовательских действий:
- InputListenerThread (pynput)
- ActionBuffer
- OverlayController
- MiniActionHUD
"""

from __future__ import annotations

import logging
import json
import os
import subprocess
import sys
import uuid
from collections import deque
from dataclasses import dataclass
from threading import RLock
from typing import Deque, Dict, List, Optional

from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt6.QtGui import QGuiApplication

from backend import Action, ActionType, BackendApplication, Coordinates
from ui.screen_overlay import ScreenOverlay

logger = logging.getLogger(__name__)
DEFAULT_RECORDING_STOP_COMBO = "cmd+1"


@dataclass
class RecordingEvent:
    type: str  # click|double_click|key|wait
    ts: int
    button: str = ""
    x: int = 0
    y: int = 0
    key: str = ""
    delay_before: int = 0
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "button": self.button,
            "x": self.x,
            "y": self.y,
            "key": self.key,
            "delay_before": self.delay_before,
            "ts": self.ts,
            "metadata": self.metadata or {},
        }


class ActionBuffer:
    """Преобразует поток сырых событий в последовательные action+wait."""

    def __init__(self, min_wait_ms: int = 50, double_click_ms: int = 350):
        self.min_wait_ms = min_wait_ms
        self.double_click_ms = double_click_ms
        self._events: List[RecordingEvent] = []
        self._last_action_ts: Optional[int] = None
        self._pending_click: Optional[dict] = None

    def feed(self, raw: dict) -> List[RecordingEvent]:
        produced: List[RecordingEvent] = []
        raw_type = raw.get("type")
        if raw_type == "click":
            click = {
                "ts": int(raw["ts"]),
                "button": raw.get("button", "left"),
                "x": int(raw.get("x", 0)),
                "y": int(raw.get("y", 0)),
            }
            if self._pending_click:
                prev = self._pending_click
                if (
                    prev["button"] == click["button"]
                    and abs(prev["x"] - click["x"]) <= 4
                    and abs(prev["y"] - click["y"]) <= 4
                    and (click["ts"] - prev["ts"]) <= self.double_click_ms
                ):
                    self._pending_click = None
                    produced.extend(self._commit_action(RecordingEvent(
                        type="double_click",
                        ts=click["ts"],
                        button=click["button"],
                        x=click["x"],
                        y=click["y"],
                    )))
                    return produced

                produced.extend(self._flush_pending_click())

            self._pending_click = click
            return produced

        produced.extend(self._flush_pending_click())

        if raw_type == "key":
            produced.extend(self._commit_action(RecordingEvent(
                type="key",
                ts=int(raw["ts"]),
                key=str(raw.get("key", "")),
            )))
        return produced

    def flush(self) -> List[RecordingEvent]:
        return self._flush_pending_click()

    def events(self) -> List[RecordingEvent]:
        return list(self._events)

    def _flush_pending_click(self) -> List[RecordingEvent]:
        if not self._pending_click:
            return []
        click = self._pending_click
        self._pending_click = None
        return self._commit_action(RecordingEvent(
            type="click",
            ts=click["ts"],
            button=click["button"],
            x=click["x"],
            y=click["y"],
        ))

    def _commit_action(self, event: RecordingEvent) -> List[RecordingEvent]:
        produced: List[RecordingEvent] = []
        if self._last_action_ts is not None:
            delay = event.ts - self._last_action_ts
            if delay >= self.min_wait_ms:
                wait = RecordingEvent(type="wait", ts=event.ts, delay_before=delay)
                self._events.append(wait)
                produced.append(wait)

        event.delay_before = 0
        self._events.append(event)
        produced.append(event)
        self._last_action_ts = event.ts
        return produced


class InputListenerThread(QObject):
    input_event = pyqtSignal(dict)
    stop_requested = pyqtSignal()
    listener_error = pyqtSignal(str)
    listener_stopped = pyqtSignal(int)

    def __init__(self, stop_combo: str = DEFAULT_RECORDING_STOP_COMBO, startup_ignore_ms: int = 500):
        super().__init__()
        self.stop_combo = stop_combo
        self.startup_ignore_ms = startup_ignore_ms
        self._process: Optional[subprocess.Popen] = None
        self._stdout_buffer = ""
        self._read_timer = QTimer(self)
        self._read_timer.setInterval(20)
        self._read_timer.timeout.connect(self._drain_stdout)

    def start(self):
        if self._process is not None and self._process.poll() is None:
            return
        worker_path = os.path.join(os.path.dirname(__file__), "recording_listener_worker.py")
        cmd = [
            sys.executable,
            worker_path,
            "--stop-combo",
            self.stop_combo,
            "--startup-ignore-ms",
            str(self.startup_ignore_ms),
        ]
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            if self._process.stdout is not None:
                os.set_blocking(self._process.stdout.fileno(), False)
            if self._process.stderr is not None:
                os.set_blocking(self._process.stderr.fileno(), False)
            self._read_timer.start()
        except Exception as exc:
            logger.exception("Failed to start recording listener worker")
            self.listener_error.emit(str(exc))

    def stop(self):
        self._read_timer.stop()
        proc = self._process
        self._process = None
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=1.5)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                except Exception:
                    logger.exception("Failed to kill listener worker process")
            except Exception:
                logger.exception("Failed to stop listener worker process")

    def wait(self, msecs: int = 0) -> bool:
        proc = self._process
        if proc is None:
            return True
        timeout = None if msecs <= 0 else (msecs / 1000.0)
        try:
            proc.wait(timeout=timeout)
            return True
        except subprocess.TimeoutExpired:
            return False

    def requestInterruption(self):
        self.stop()

    def _drain_stdout(self):
        proc = self._process
        if proc is None:
            self._read_timer.stop()
            return
        try:
            if proc.stdout is not None:
                try:
                    chunk = proc.stdout.read()
                except BlockingIOError:
                    chunk = ""
                if chunk:
                    self._stdout_buffer += chunk
                    while "\n" in self._stdout_buffer:
                        line, self._stdout_buffer = self._stdout_buffer.split("\n", 1)
                        self._handle_worker_line(line)
            if proc.poll() is not None:
                self._read_timer.stop()
                stderr_tail = ""
                if proc.stderr is not None:
                    try:
                        stderr_tail = (proc.stderr.read() or "").strip()
                    except Exception:
                        stderr_tail = ""
                code = int(proc.returncode or 0)
                self._process = None
                self.listener_stopped.emit(code)
                if code != 0 and stderr_tail:
                    self.listener_error.emit(f"Listener worker exited with {code}: {stderr_tail}")
        except Exception as exc:
            logger.exception("Failed to read recording listener worker output")
            self.listener_error.emit(str(exc))
            self.stop()

    def _handle_worker_line(self, line: str):
        payload_raw = line.strip()
        if not payload_raw:
            return
        try:
            payload = json.loads(payload_raw)
        except Exception:
            logger.warning("Invalid listener worker output: %s", payload_raw[:300])
            return
        msg_type = payload.get("type")
        if msg_type == "event":
            event = payload.get("event")
            if isinstance(event, dict):
                self.input_event.emit(event)
        elif msg_type == "stop_requested":
            self.stop_requested.emit()
        elif msg_type == "error":
            self.listener_error.emit(str(payload.get("message", "Unknown listener worker error")))


class OverlayController:
    def __init__(self, backend: BackendApplication):
        self.backend = backend
        self.overlay: Optional[ScreenOverlay] = None

    def show(self):
        if self.overlay is None:
            self.overlay = ScreenOverlay(self.backend, interactive=False)
        self.overlay.show()

    def hide(self):
        if self.overlay is not None:
            self.overlay.hide()


class MiniActionHUD(QWidget):
    def __init__(self, max_lines: int = 8):
        super().__init__()
        self.max_lines = max_lines
        self.lines: Deque[str] = deque(maxlen=max_lines)
        self._init_ui()

    def _init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 20, 185);
                color: #f0f0f0;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        self.title = QLabel(f"● Recording... (stop: {DEFAULT_RECORDING_STOP_COMBO.upper()})")
        self.body = QLabel("")
        self.body.setWordWrap(True)
        layout.addWidget(self.title)
        layout.addWidget(self.body)
        self.resize(300, 180)

    def show_bottom_left(self):
        screen = QGuiApplication.primaryScreen()
        if not screen:
            self.show()
            return
        geo = screen.availableGeometry()
        x = geo.x() + 20
        y = geo.y() + geo.height() - self.height() - 30
        self.move(x, y)
        self.show()

    def add_event(self, event: RecordingEvent):
        if event.type == "click":
            text = f"Click ({event.x}, {event.y})"
        elif event.type == "double_click":
            text = f"DoubleClick ({event.x}, {event.y})"
        elif event.type == "key":
            text = event.key.upper()
        elif event.type == "wait":
            text = f"WAIT {event.delay_before} ms"
        else:
            text = event.type
        self.lines.append(text)
        self.body.setText("\n".join(self.lines))


class RecordingManager(QObject):
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal(int)  # count of recorded events
    recording_error = pyqtSignal(str)
    hud_updated = pyqtSignal(dict)

    def __init__(self, backend: BackendApplication, parent_window=None):
        super().__init__(parent_window)
        self.backend = backend
        self.parent_window = parent_window
        self.buffer = ActionBuffer()
        self.overlay = OverlayController(backend)
        self.hud: Optional[MiniActionHUD] = None
        self.listener_thread: Optional[InputListenerThread] = None
        self.is_recording = False
        self.target_row_id: Optional[str] = None
        self._state_lock = RLock()
        self._is_stopping = False

    def start(self):
        with self._state_lock:
            if self.is_recording:
                logger.warning("Recording start ignored: already running")
                return

            logger.info("Recording start requested")
            self.is_recording = True
            self._is_stopping = False
            self.buffer = ActionBuffer()
            self.target_row_id = None

            try:
                if not self.backend.current_board:
                    self.backend.create_board("Без названия")
                row = self.backend.add_row("Запись")
                self.target_row_id = row.id

                self.overlay.show()
                self.hud = MiniActionHUD()
                self.hud.show_bottom_left()

                if self.parent_window is not None:
                    self.parent_window.showMinimized()

                self.listener_thread = InputListenerThread(stop_combo=DEFAULT_RECORDING_STOP_COMBO, startup_ignore_ms=350)
                self.listener_thread.input_event.connect(self._on_raw_event, Qt.ConnectionType.QueuedConnection)
                self.listener_thread.stop_requested.connect(self._queue_stop, Qt.ConnectionType.QueuedConnection)
                self.listener_thread.listener_error.connect(self._on_listener_error, Qt.ConnectionType.QueuedConnection)
                self.listener_thread.start()
                logger.info("Recording listener thread started")
            except Exception as exc:
                logger.exception("Recording start failed")
                self._rollback_start()
                self.recording_error.emit(str(exc))
                return

        self.recording_started.emit()

    def stop(self):
        with self._state_lock:
            if not self.is_recording or self._is_stopping:
                return
            logger.info("Recording stop requested")
            self._is_stopping = True
            self.is_recording = False

        try:
            if self.listener_thread is not None:
                self.listener_thread.stop()
                if not self.listener_thread.wait(2000):
                    logger.warning("Listener thread did not stop in 2000ms, forcing interruption")
                    self.listener_thread.requestInterruption()
                    self.listener_thread.wait(1000)
                self.listener_thread = None

            extra = self.buffer.flush()
            for event in extra:
                self._append_action(event)
                self._update_hud(event)
        finally:
            self.overlay.hide()
            if self.hud is not None:
                self.hud.hide()
                self.hud.deleteLater()
                self.hud = None

            if self.parent_window is not None:
                self.parent_window.showNormal()
                self.parent_window.raise_()
                self.parent_window.activateWindow()

            event_count = len(self.buffer.events())
            with self._state_lock:
                self._is_stopping = False
            logger.info("Recording stopped, events=%s", event_count)
            self.recording_stopped.emit(event_count)

    def shutdown(self):
        if self.is_recording:
            self.stop()

    def _queue_stop(self):
        # Вызывается через QueuedConnection, поэтому уже в GUI thread.
        self.stop()

    def _on_listener_error(self, message: str):
        logger.error("Recording listener error: %s", message)
        self.recording_error.emit(message)
        self.stop()

    def _on_raw_event(self, raw: dict):
        produced = self.buffer.feed(raw)
        for event in produced:
            self._append_action(event)
            self._update_hud(event)

    def _append_action(self, event: RecordingEvent):
        if not self.target_row_id:
            return
        if event.type == "wait":
            action = Action(
                id=str(uuid.uuid4()),
                action_type=ActionType.WAIT_TIME,
                name=f"WAIT {event.delay_before}ms",
                delay_before_ms=event.delay_before,
            )
            self.backend.add_action(self.target_row_id, action)
            return

        if event.type in {"click", "double_click"}:
            action = Action(
                id=str(uuid.uuid4()),
                action_type=ActionType.MOUSE_CLICK,
                name="Двойной клик" if event.type == "double_click" else "Клик мышью",
                coordinates=Coordinates(event.x, event.y),
                mouse_button=event.button or "left",
                metadata={"click_count": 2 if event.type == "double_click" else 1},
            )
            self.backend.add_action(self.target_row_id, action)
            return

        if event.type == "key":
            action = Action(
                id=str(uuid.uuid4()),
                action_type=ActionType.KEY_PRESS,
                name=f"Клавиша: {event.key}",
                key=event.key,
            )
            self.backend.add_action(self.target_row_id, action)

    def _update_hud(self, event: RecordingEvent):
        if self.hud is not None:
            self.hud.add_event(event)
        self.hud_updated.emit(event.to_dict())

    def _rollback_start(self):
        self.is_recording = False
        self._is_stopping = False
        if self.listener_thread is not None:
            try:
                self.listener_thread.stop()
                self.listener_thread.wait(1000)
            except Exception:
                logger.exception("Failed to rollback listener thread")
            finally:
                self.listener_thread = None
        self.overlay.hide()
        if self.hud is not None:
            self.hud.hide()
            self.hud.deleteLater()
            self.hud = None
