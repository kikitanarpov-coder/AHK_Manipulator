import tempfile
import unittest
from pathlib import Path

from backend import (
    AhkRunner,
    AhkV2Parser,
    AhkValidator,
    BackendApplication,
    Coordinates,
    IKeyboardService,
    IMouseService,
    IScreenService,
)


class FakeMouse(IMouseService):
    def __init__(self):
        self.pos = Coordinates(0, 0)
        self.clicks = 0

    def get_position(self):
        return self.pos

    def move_to(self, x: int, y: int, duration_ms: int = 0):
        self.pos = Coordinates(x, y)

    def click(self, button: str = "left"):
        self.clicks += 1


class FakeKeyboard(IKeyboardService):
    def __init__(self):
        self.pressed = []

    def press(self, key: str):
        self.pressed.append(key)

    def press_hotkey(self, keys):
        self.pressed.append("+".join(keys))


class FakeScreen(IScreenService):
    def get_pixel_color(self, x: int, y: int):
        return None

    def take_screenshot(self, region=None):
        return "/tmp/shot.png"

    def find_image(self, image_path: str, confidence: float = 0.9):
        return None


SAMPLE_AHK_V2 = """#Requires AutoHotkey v2.0
global SapSession := "PRD"
global LastFile := "out.txt"

F2:: {
    Click(100, 200)
    Sleep(5)
    Send("{Enter}")
    WinActivate("SAP Logon")
}

DoExcelLookup(path) {
    Try {
        FileRead(path)
    } Catch Error as err {
        Throw Error("Read failed")
    }
}
"""


class TestAhkV2Integration(unittest.TestCase):
    def setUp(self):
        self.backend = BackendApplication(
            mouse=FakeMouse(),
            keyboard=FakeKeyboard(),
            screen=FakeScreen(),
            database=None,
        )

    def test_parser_extracts_requires_globals_hotkeys_functions(self):
        parser = AhkV2Parser()
        script = parser.parse_text(SAMPLE_AHK_V2)

        self.assertEqual(script.requires, "2.0")
        self.assertIn("SapSession", script.globals)
        self.assertIn("F2", script.hotkeys)
        self.assertIn("DoExcelLookup", script.functions)
        self.assertGreaterEqual(len(script.hotkeys["F2"]), 4)

    def test_validator_accepts_v2_and_reports_windows_specific(self):
        parser = AhkV2Parser()
        validator = AhkValidator()
        script = parser.parse_text(SAMPLE_AHK_V2)
        result = validator.validate(script)

        self.assertTrue(result.is_valid)
        self.assertTrue(any("Windows-specific command" in d.message for d in result.diagnostics))

    def test_backend_api_parse_validate_execute(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sample.ahk"
            path.write_text(SAMPLE_AHK_V2, encoding="utf-8-sig")

            parsed = self.backend.parse_ahk_file(str(path))
            self.assertEqual(parsed.requires, "2.0")

            validation = self.backend.validate_ahk_file(str(path))
            self.assertTrue(validation.is_valid)

            result = self.backend.execute_ahk_file(str(path), mode="emulated", allowed_root=td)
            self.assertTrue(result.success)
            self.assertEqual(result.mode, "emulated")
            self.assertIsNotNone(result.board)
            self.assertEqual(self.backend.mouse.pos.to_tuple(), (100, 200))

    def test_import_from_file_falls_back_to_ahk_v2_translator(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sample.ahk"
            path.write_text(SAMPLE_AHK_V2, encoding="utf-8")
            board = self.backend.import_from_file(str(path))
            self.assertGreaterEqual(len(board.rows), 1)
            self.assertGreaterEqual(sum(len(r.actions) for r in board.rows), 1)

    def test_execute_rejects_outside_allowed_root(self):
        with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
            path = Path(td1) / "sample.ahk"
            path.write_text(SAMPLE_AHK_V2, encoding="utf-8")
            result = self.backend.execute_ahk_file(str(path), mode="emulated", allowed_root=td2)
            self.assertFalse(result.success)
            self.assertTrue(any("outside allowed root" in d.message for d in result.diagnostics))

    def test_utf8_bom_file_parses(self):
        parser = AhkV2Parser()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bom.ahk"
            path.write_text(SAMPLE_AHK_V2, encoding="utf-8-sig")
            script = parser.parse_file(path)
            self.assertEqual(script.requires, "2.0")

    def test_native_mode_without_exe_fails_gracefully(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sample.ahk"
            path.write_text(SAMPLE_AHK_V2, encoding="utf-8")
            runner = AhkRunner(self.backend)
            original = runner.find_ahk_executable
            runner.find_ahk_executable = lambda: None
            try:
                result = runner.execute_file(path, mode="native")
            finally:
                runner.find_ahk_executable = original

            self.assertFalse(result.success)
            self.assertEqual(result.mode, "native")
            self.assertTrue(any("executable not found" in d.message for d in result.diagnostics))


if __name__ == "__main__":
    unittest.main()
