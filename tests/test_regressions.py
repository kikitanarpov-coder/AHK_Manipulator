import asyncio
import unittest

from backend.core import (
    Action,
    ActionHandlerRegistry,
    ActionType,
    BackendApplication,
    ExecutionEngine,
    IDatabaseService,
    TaskBoard,
    TaskRow,
)


class FakeDatabaseService(IDatabaseService):
    def search(self, db_name: str, column: str, value: str):
        if db_name == "db1" and column == "code" and value == "42":
            return {"code": "42", "name": "Answer"}
        return None

    def get_columns(self, db_name: str):
        return ["code", "name"]


class TestDbHandlersContext(unittest.TestCase):
    def test_db_search_then_get_value_uses_shared_engine_variables(self):
        registry = ActionHandlerRegistry(database=FakeDatabaseService())
        engine = ExecutionEngine(registry)

        board = TaskBoard(id="b1", name="board")
        row = TaskRow(id="r1", name="row")
        row.add_action(Action(
            id="a1",
            action_type=ActionType.DB_SEARCH,
            name="search",
            metadata={
                "database": "db1",
                "search_column": "code",
                "search_value": "42",
                "result_variable": "record",
            },
        ))
        row.add_action(Action(
            id="a2",
            action_type=ActionType.DB_GET_VALUE,
            name="extract",
            metadata={
                "variable": "record",
                "column": "name",
                "result_variable": "record_name",
            },
        ))
        board.add_row(row)

        results = asyncio.run(engine.execute_board(board))

        self.assertEqual(len(results), 2)
        self.assertTrue(results[0].success)
        self.assertTrue(results[1].success)
        self.assertEqual(engine.get_variable("record_name"), "Answer")


class TestExportRegression(unittest.TestCase):
    def test_ahk_export_closes_runscript_block(self):
        app = BackendApplication()
        board = app.create_board("test")
        row = app.add_row("r")
        row.add_action(Action(id="a1", action_type=ActionType.WAIT_TIME, name="wait", delay_before_ms=10))

        script = app.export_to_ahk(board, include_comments=True)
        self.assertIn("RunScript() {", script)
        self.assertTrue(script.strip().endswith("}"))


if __name__ == "__main__":
    unittest.main()
