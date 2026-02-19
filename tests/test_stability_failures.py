import asyncio
import tempfile
import unittest
from pathlib import Path

from backend.core import (
    Action,
    ActionHandlerRegistry,
    ActionType,
    BackendApplication,
    Coordinates,
    ExecutionEngine,
    IKeyboardService,
    IMouseService,
    IScreenService,
    TaskBoard,
    TaskRow,
)
from backend.services import DatabaseService


class NoopMouse(IMouseService):
    def get_position(self):
        return Coordinates(0, 0)

    def move_to(self, x: int, y: int, duration_ms: int = 0):
        return None

    def click(self, button: str = "left"):
        return None


class NoopKeyboard(IKeyboardService):
    def press(self, key: str):
        return None

    def press_hotkey(self, keys):
        return None


class FlakyScreen(IScreenService):
    def __init__(self, screenshot_ok: bool = False):
        self.screenshot_ok = screenshot_ok

    def get_pixel_color(self, x: int, y: int):
        return None

    def take_screenshot(self, region=None):
        if self.screenshot_ok:
            return "/tmp/ok.png"
        return None

    def find_image(self, image_path: str, confidence: float = 0.9):
        return None


class TestStabilityAndFailures(unittest.TestCase):
    def test_backend_shutdown_closes_services(self):
        class Closable(NoopMouse):
            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True

        mouse = Closable()
        keyboard = Closable()
        screen = Closable()
        database = Closable()
        app = BackendApplication(mouse=mouse, keyboard=keyboard, screen=screen, database=database)
        app.shutdown()
        self.assertTrue(mouse.closed)
        self.assertTrue(keyboard.closed)
        self.assertTrue(screen.closed)
        self.assertTrue(database.closed)

    def test_database_missing_and_corrupt_files(self):
        svc = DatabaseService()
        self.assertFalse(svc.add_database("missing", "/definitely/missing/file.xlsx"))

        with tempfile.TemporaryDirectory() as td:
            bad_xlsx = Path(td) / "bad.xlsx"
            bad_xlsx.write_bytes(b"not a real xlsx")
            self.assertFalse(svc.add_database("bad", str(bad_xlsx)))

    def test_database_repeated_csv_loads(self):
        svc = DatabaseService()
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "db.csv"
            csv_path.write_text("id,name\n1,A\n2,B\n", encoding="utf-8")
            for i in range(100):
                ok = svc.add_database(f"csv{i}", str(csv_path))
                self.assertTrue(ok)

    def test_import_missing_file_raises_cleanly(self):
        app = BackendApplication()
        with self.assertRaises(FileNotFoundError):
            app.import_from_file("/definitely/missing/file.ahk")

    def test_screenshot_failure_returns_result_not_crash(self):
        registry = ActionHandlerRegistry(
            mouse=NoopMouse(),
            keyboard=NoopKeyboard(),
            screen=FlakyScreen(screenshot_ok=False),
            database=None,
        )
        engine = ExecutionEngine(registry)
        board = TaskBoard(id="b", name="b")
        row = TaskRow(id="r", name="r")
        row.add_action(Action(
            id="shot",
            action_type=ActionType.SCREENSHOT,
            name="s",
            metadata={"region_x": 0, "region_y": 0, "region_width": 10, "region_height": 10},
        ))
        board.add_row(row)
        results = asyncio.run(engine.execute_board(board))
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].success)

    def test_engine_repeated_runs_stability(self):
        registry = ActionHandlerRegistry(
            mouse=NoopMouse(),
            keyboard=NoopKeyboard(),
            screen=FlakyScreen(screenshot_ok=True),
            database=None,
        )
        engine = ExecutionEngine(registry)
        board = TaskBoard(id="b", name="b")
        row = TaskRow(id="r", name="r")
        row.add_action(Action(id="log", action_type=ActionType.LOG, name="log", metadata={"message": "ok"}))
        board.add_row(row)

        for _ in range(100):
            results = asyncio.run(engine.execute_board(board))
            self.assertEqual(len(results), 1)
            self.assertTrue(results[0].success)

    def test_engine_stop_during_execution(self):
        registry = ActionHandlerRegistry(
            mouse=NoopMouse(),
            keyboard=NoopKeyboard(),
            screen=FlakyScreen(),
            database=None,
        )
        engine = ExecutionEngine(registry)
        board = TaskBoard(id="b", name="b")
        row = TaskRow(id="r", name="r")
        for i in range(30):
            row.add_action(Action(
                id=f"w{i}",
                action_type=ActionType.WAIT_TIME,
                name=f"wait{i}",
                delay_before_ms=10,
            ))
        board.add_row(row)

        async def run_and_stop():
            task = asyncio.create_task(engine.execute_board(board))
            await asyncio.sleep(0.05)
            engine.stop()
            return await task

        results = asyncio.run(run_and_stop())
        self.assertLess(len(results), 30)
        self.assertFalse(engine.is_running)

    def test_conditional_break_stops_sequence(self):
        registry = ActionHandlerRegistry(
            mouse=NoopMouse(),
            keyboard=NoopKeyboard(),
            screen=FlakyScreen(),
            database=None,
        )
        engine = ExecutionEngine(registry)
        board = TaskBoard(id="b", name="b")
        row = TaskRow(id="r", name="r")
        row.add_action(Action(
            id="c1",
            action_type=ActionType.CONDITIONAL,
            name="cond",
            metadata={
                "condition_type": "variable_equals",
                "variable_name": "x",
                "condition_value": "",
                "if_true": "break",
                "if_false": "execute_next",
            },
        ))
        row.add_action(Action(
            id="after",
            action_type=ActionType.LOG,
            name="after",
            metadata={"message": "should not run"},
        ))
        board.add_row(row)

        results = asyncio.run(engine.execute_board(board))
        self.assertEqual([r.action_id for r in results], ["c1"])


if __name__ == "__main__":
    unittest.main()
