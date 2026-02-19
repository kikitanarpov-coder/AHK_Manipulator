import unittest

try:
    from ui.recording_manager import ActionBuffer
    HAS_PYQT = True
except ModuleNotFoundError:
    HAS_PYQT = False


@unittest.skipUnless(HAS_PYQT, "PyQt6 is not installed in the current environment")
class TestRecordingBuffer(unittest.TestCase):
    def test_inserts_wait_between_actions(self):
        b = ActionBuffer(min_wait_ms=50, double_click_ms=350)
        produced = []
        produced.extend(b.feed({"type": "key", "key": "ctrl+s", "ts": 1000}))
        produced.extend(b.feed({"type": "key", "key": "enter", "ts": 1200}))

        self.assertEqual([e.type for e in produced], ["key", "wait", "key"])
        self.assertEqual(produced[1].delay_before, 200)

    def test_merges_double_click(self):
        b = ActionBuffer(min_wait_ms=50, double_click_ms=350)
        produced = []
        produced.extend(b.feed({"type": "click", "button": "left", "x": 100, "y": 100, "ts": 1000}))
        produced.extend(b.feed({"type": "click", "button": "left", "x": 101, "y": 101, "ts": 1150}))
        produced.extend(b.flush())

        self.assertEqual(len(produced), 1)
        self.assertEqual(produced[0].type, "double_click")

    def test_flush_single_click(self):
        b = ActionBuffer(min_wait_ms=50, double_click_ms=350)
        produced = []
        produced.extend(b.feed({"type": "click", "button": "left", "x": 10, "y": 20, "ts": 1000}))
        produced.extend(b.flush())
        self.assertEqual(len(produced), 1)
        self.assertEqual(produced[0].type, "click")


if __name__ == "__main__":
    unittest.main()
