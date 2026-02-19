import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow

from backend import BackendApplication
from backend.core import IDatabaseService, IKeyboardService, IMouseService, IScreenService
from ui.recording_manager import RecordingManager


class _DummyMouse(IMouseService):
    def get_position(self):
        from backend import Coordinates
        return Coordinates(1, 1)

    def move_to(self, x: int, y: int, duration_ms: int = 0):
        return None

    def click(self, button: str = "left"):
        return None


class _DummyKeyboard(IKeyboardService):
    def press(self, key: str):
        return None

    def press_hotkey(self, keys):
        return None


class _DummyScreen(IScreenService):
    def get_pixel_color(self, x: int, y: int):
        return None

    def take_screenshot(self, region=None):
        return None

    def find_image(self, template_path: str, threshold: float = 0.9):
        return None


class _DummyDb(IDatabaseService):
    def add_database(self, name: str, filepath: str):
        return None

    def search(self, database_name: str, query: str):
        return []

    def get_value(self, database_name: str, row: int, column: str):
        return None

    def get_columns(self, database_name: str):
        return []


class _FakeInputListenerThread(QThread):
    input_event = pyqtSignal(dict)
    stop_requested = pyqtSignal()
    listener_error = pyqtSignal(str)
    scenario = "idle"

    def __init__(self, *args, **kwargs):
        super().__init__()

    def start(self):
        if self.scenario == "error":
            QTimer.singleShot(0, lambda: self.listener_error.emit("listener boom"))
        elif self.scenario == "stop":
            QTimer.singleShot(0, self.stop_requested.emit)
        elif self.scenario == "event_and_stop":
            QTimer.singleShot(0, lambda: self.input_event.emit({"type": "click", "x": 12, "y": 34, "button": "left", "ts": 1000}))
            QTimer.singleShot(1, self.stop_requested.emit)

    def stop(self):
        return None

    def wait(self, msecs: int = 0):
        return True


class TestRecordingManagerStability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.backend = BackendApplication(
            mouse=_DummyMouse(),
            keyboard=_DummyKeyboard(),
            screen=_DummyScreen(),
            database=_DummyDb(),
        )
        self.window = QMainWindow()
        self.window.show()
        self.manager = RecordingManager(self.backend, self.window)

    def tearDown(self):
        self.manager.shutdown()
        self.backend.shutdown()
        self.window.close()
        self._drain_events()

    def _drain_events(self, cycles: int = 8):
        for _ in range(cycles):
            self.app.processEvents()

    @patch("ui.recording_manager.InputListenerThread", _FakeInputListenerThread)
    def test_start_stop_idempotent(self):
        _FakeInputListenerThread.scenario = "idle"
        self.manager.start()
        self.manager.start()  # no-op
        self._drain_events()
        self.assertTrue(self.manager.is_recording)
        self.manager.stop()
        self.manager.stop()  # no-op
        self._drain_events()
        self.assertFalse(self.manager.is_recording)

    @patch("ui.recording_manager.InputListenerThread", _FakeInputListenerThread)
    def test_listener_error_does_not_crash_and_stops(self):
        _FakeInputListenerThread.scenario = "error"
        captured = []
        self.manager.recording_error.connect(captured.append)
        self.manager.start()
        self._drain_events()
        self.assertFalse(self.manager.is_recording)
        self.assertTrue(captured)
        self.assertIn("listener boom", captured[0])

    @patch("ui.recording_manager.InputListenerThread", _FakeInputListenerThread)
    def test_stop_requested_path_is_safe(self):
        _FakeInputListenerThread.scenario = "event_and_stop"
        self.manager.start()
        self._drain_events(24)
        self.assertFalse(self.manager.is_recording)
        board = self.backend.current_board
        self.assertIsNotNone(board)
        self.assertGreaterEqual(len(board.rows), 1)


if __name__ == "__main__":
    unittest.main()
