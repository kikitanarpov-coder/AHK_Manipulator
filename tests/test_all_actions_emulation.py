import asyncio
import tempfile
import unittest
from pathlib import Path

from backend.core import (
    Action,
    ActionHandlerRegistry,
    ActionType,
    BackendApplication,
    Color,
    Coordinates,
    ExecutionEngine,
    IDatabaseService,
    IKeyboardService,
    IMouseService,
    IScreenService,
    TaskBoard,
    TaskRow,
)


class FakeMouse(IMouseService):
    def __init__(self):
        self.pos = Coordinates(0, 0)
        self.clicks = []

    def get_position(self) -> Coordinates:
        return self.pos

    def move_to(self, x: int, y: int, duration_ms: int = 0) -> None:
        self.pos = Coordinates(x, y)

    def click(self, button: str = "left") -> None:
        self.clicks.append(button)


class FakeKeyboard(IKeyboardService):
    def __init__(self):
        self.keys = []

    def press(self, key: str) -> None:
        self.keys.append(key)

    def press_hotkey(self, keys):
        self.keys.append("+".join(keys))


class FakeScreen(IScreenService):
    def __init__(self):
        self.pixel_calls = 0
        self.image_calls = 0
        self.screenshot_calls = 0
        self.last_region = None

    def get_pixel_color(self, x: int, y: int):
        self.pixel_calls += 1
        if self.pixel_calls < 3:
            return Color(10, 10, 10, tolerance=0)
        return Color(20, 20, 20, tolerance=0)

    def take_screenshot(self, region=None):
        self.screenshot_calls += 1
        self.last_region = region
        return f"/tmp/fake_screen_{self.screenshot_calls}.png"

    def find_image(self, image_path: str, confidence: float = 0.9):
        self.image_calls += 1
        if self.image_calls >= 2:
            return Coordinates(300, 400)
        return None


class FakeDatabase(IDatabaseService):
    def __init__(self):
        self.databases = {
            "db_main": {
                "columns": ["code", "name", "value", "new_value"],
                "data": [
                    {"code": "42", "name": "Answer", "value": "100", "new_value": ""},
                    {"code": "43", "name": "Other", "value": "200", "new_value": ""},
                ],
            },
            "db_replace": {
                "columns": ["from", "to"],
                "data": [
                    {"from": "100", "to": "999"},
                ],
            },
        }

    def search(self, db_name: str, column: str, value: str):
        db = self.databases.get(db_name, {})
        for row in db.get("data", []):
            if str(row.get(column, "")).strip() == str(value).strip():
                return row
        return None

    def get_columns(self, db_name: str):
        return self.databases.get(db_name, {}).get("columns", [])


class TestAllActionsEmulation(unittest.TestCase):
    def test_registry_has_handler_for_every_action_type(self):
        registry = ActionHandlerRegistry(
            mouse=FakeMouse(),
            keyboard=FakeKeyboard(),
            screen=FakeScreen(),
            database=FakeDatabase(),
        )
        missing = [at.name for at in ActionType if registry.get_handler(at) is None]
        self.assertEqual(missing, [], msg=f"Missing handlers: {missing}")

    def test_execute_every_action_type(self):
        mouse = FakeMouse()
        keyboard = FakeKeyboard()
        screen = FakeScreen()
        database = FakeDatabase()
        registry = ActionHandlerRegistry(mouse=mouse, keyboard=keyboard, screen=screen, database=database)
        engine = ExecutionEngine(registry)

        board = TaskBoard(id="b1", name="all-actions")
        row = TaskRow(id="r1", name="main")
        sub_row = TaskRow(id="r2", name="sub")

        # Подпрограмма для RUN_ROW
        sub_row.add_action(Action(
            id="sub_log",
            action_type=ActionType.LOG,
            name="sub-log",
            metadata={"message": "subrow executed"},
        ))

        row.add_action(Action(
            id="a1",
            action_type=ActionType.MOUSE_MOVE,
            name="move",
            coordinates=Coordinates(10, 20),
            metadata={"move_duration_ms": 1},
        ))
        row.add_action(Action(
            id="a2",
            action_type=ActionType.MOUSE_CLICK,
            name="click",
            coordinates=Coordinates(10, 20),
            mouse_button="left",
        ))
        row.add_action(Action(
            id="a3",
            action_type=ActionType.KEY_PRESS,
            name="key",
            key="enter",
        ))
        row.add_action(Action(
            id="a4",
            action_type=ActionType.WAIT_TIME,
            name="wait",
            delay_before_ms=1,
        ))
        row.add_action(Action(
            id="a5",
            action_type=ActionType.WAIT_PIXEL_COLOR,
            name="wait-color",
            coordinates=Coordinates(1, 1),
            metadata={"any_change": True, "timeout_ms": 200, "check_interval_ms": 1},
        ))
        row.add_action(Action(
            id="a6",
            action_type=ActionType.WAIT_PIXEL_CHANGE,
            name="wait-change",
            coordinates=Coordinates(1, 1),
            metadata={"timeout_ms": 200, "check_interval_ms": 1},
        ))
        row.add_action(Action(
            id="a7",
            action_type=ActionType.WAIT_IMAGE,
            name="wait-image",
            metadata={"image_path": "dummy.png", "confidence": 0.8, "timeout_ms": 200, "check_interval_ms": 1},
        ))
        row.add_action(Action(
            id="a8",
            action_type=ActionType.DB_SEARCH,
            name="db-search",
            metadata={
                "database": "db_main",
                "search_column": "code",
                "search_value": "42",
                "result_variable": "record",
            },
        ))
        row.add_action(Action(
            id="a9",
            action_type=ActionType.DB_GET_VALUE,
            name="db-get",
            metadata={
                "variable": "record",
                "column": "name",
                "result_variable": "ocr_text",
            },
        ))
        row.add_action(Action(
            id="a10",
            action_type=ActionType.WAIT_TEXT,
            name="wait-text",
            metadata={"search_text": "Answer"},
        ))
        row.add_action(Action(
            id="a11",
            action_type=ActionType.CONDITIONAL,
            name="cond",
            metadata={
                "condition_type": "variable_equals",
                "variable_name": "ocr_text",
                "condition_value": "Answer",
                "if_true": "skip_next",
                "if_false": "execute_next",
            },
        ))
        row.add_action(Action(
            id="a12",
            action_type=ActionType.LOG,
            name="must-skip",
            metadata={"message": "this should be skipped"},
        ))
        row.add_action(Action(
            id="a13",
            action_type=ActionType.LOOP,
            name="loop",
            metadata={"iterations": 2, "delay_ms": 0},
        ))
        row.add_action(Action(
            id="a14",
            action_type=ActionType.SCREENSHOT,
            name="shot",
            metadata={"region_x": 0, "region_y": 0, "region_width": 100, "region_height": 100},
        ))
        row.add_action(Action(
            id="a15",
            action_type=ActionType.DB_SAVE,
            name="db-save",
            metadata={
                "database": "db_main",
                "search_column": "code",
                "search_value": "42",
                "update_column": "new_value",
                "save_value": "{ocr_text}",
            },
        ))
        row.add_action(Action(
            id="a16",
            action_type=ActionType.CHECK_VALUE,
            name="check-value",
            metadata={
                "database": "db_replace",
                "from_column": "from",
                "to_column": "to",
                "check_variable": "record.value",
                "result_variable": "checked_value",
            },
        ))
        # Корректная переменная для CHECK_VALUE
        row.add_action(Action(
            id="a16b",
            action_type=ActionType.DB_GET_VALUE,
            name="db-get-value",
            metadata={"variable": "record", "column": "value", "result_variable": "old_value"},
        ))
        row.add_action(Action(
            id="a16c",
            action_type=ActionType.CHECK_VALUE,
            name="check-value-2",
            metadata={
                "database": "db_replace",
                "from_column": "from",
                "to_column": "to",
                "check_variable": "old_value",
                "result_variable": "checked_value",
            },
        ))
        row.add_action(Action(
            id="a17",
            action_type=ActionType.RUN_ROW,
            name="run-row",
            metadata={"row_id": "r2", "wait_complete": True},
        ))

        board.add_row(row)
        board.add_row(sub_row)

        results = asyncio.run(engine.execute_board(board))

        self.assertGreaterEqual(len(results), 18)
        self.assertTrue(any(r.action_id == "a1" and r.success for r in results))
        self.assertTrue(any(r.action_id == "a2" and r.success for r in results))
        self.assertTrue(any(r.action_id == "a7" and r.success for r in results))
        self.assertTrue(any(r.action_id == "a10" and r.success for r in results))
        self.assertTrue(any(r.action_id == "a14" and r.success for r in results))
        self.assertTrue(any(r.action_id == "a15" and r.success for r in results))
        self.assertTrue(any(r.action_id == "a17" and r.success for r in results))

        self.assertEqual(mouse.pos.x, 10)
        self.assertIn("left", mouse.clicks)
        self.assertIn("enter", keyboard.keys)
        self.assertEqual(engine.get_variable("last_image_x"), 300)
        self.assertEqual(engine.get_variable("last_image_y"), 400)
        self.assertEqual(engine.get_variable("ocr_text"), "Answer")
        self.assertEqual(engine.get_variable("checked_value"), "999")
        self.assertTrue(str(engine.get_variable("last_screenshot")).endswith(".png"))
        self.assertEqual(database.databases["db_main"]["data"][0]["new_value"], "Answer")

    def test_backend_save_load_export_import_cycle(self):
        app = BackendApplication()
        board = app.create_board("cycle")
        row = app.add_row("row")
        row.add_action(Action(id="a1", action_type=ActionType.LOG, name="log", metadata={"message": "ok"}))

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            json_path = td_path / "board.json"
            ahk_path = td_path / "board.ahk"

            app.save_board(board, str(json_path))
            loaded = app.load_board(str(json_path))
            self.assertEqual(loaded.name, "cycle")

            ahk = app.export_to_ahk(loaded, include_comments=True)
            ahk_path.write_text(ahk, encoding="utf-8")
            imported = app.import_from_file(str(ahk_path))
            self.assertGreaterEqual(len(imported.rows), 1)


if __name__ == "__main__":
    unittest.main()
