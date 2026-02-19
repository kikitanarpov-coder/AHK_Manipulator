"""
Тесты для бэкенда AHK Manipulator
"""

import asyncio
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from backend.core import (
    CONFIG, ActionType, Coordinates, Color, Action, TaskRow, TaskBoard,
    ExecutionResult, ActionHandlerRegistry, ExecutionEngine, BackendApplication,
    MouseClickHandler, MouseMoveHandler, KeyPressHandler, WaitTimeHandler,
    BaseActionHandler,
    IMouseService, IKeyboardService, IScreenService, IDatabaseService
)


# =============================================================================
# ТЕСТЫ МОДЕЛЕЙ ДАННЫХ
# =============================================================================

class TestCoordinates(unittest.TestCase):
    """Тесты для модели Coordinates"""

    def test_create_coordinates(self):
        """Создание координат"""
        coord = Coordinates(x=100, y=200)
        self.assertEqual(coord.x, 100)
        self.assertEqual(coord.y, 200)

    def test_to_tuple(self):
        """Преобразование в кортеж"""
        coord = Coordinates(x=100, y=200)
        self.assertEqual(coord.to_tuple(), (100, 200))

    def test_to_dict(self):
        """Преобразование в словарь"""
        coord = Coordinates(x=100, y=200)
        result = coord.to_dict()
        self.assertEqual(result, {"x": 100, "y": 200})

    def test_from_dict(self):
        """Создание из словаря"""
        data = {"x": 100, "y": 200}
        coord = Coordinates.from_dict(data)
        self.assertEqual(coord.x, 100)
        self.assertEqual(coord.y, 200)


class TestColor(unittest.TestCase):
    """Тесты для модели Color"""

    def test_create_color(self):
        """Создание цвета"""
        color = Color(r=255, g=128, b=64)
        self.assertEqual(color.r, 255)
        self.assertEqual(color.g, 128)
        self.assertEqual(color.b, 64)
        self.assertEqual(color.tolerance, 10)  # Значение по умолчанию

    def test_matches_within_tolerance(self):
        """Сравнение цветов в пределах допуска"""
        color1 = Color(r=255, g=128, b=64, tolerance=10)
        color2 = Color(r=250, g=130, b=60, tolerance=10)
        self.assertTrue(color1.matches(color2))

    def test_matches_outside_tolerance(self):
        """Сравнение цветов вне допуска"""
        color1 = Color(r=255, g=128, b=64, tolerance=5)
        color2 = Color(r=200, g=128, b=64, tolerance=5)
        self.assertFalse(color1.matches(color2))

    def test_to_dict(self):
        """Преобразование в словарь"""
        color = Color(r=255, g=128, b=64, tolerance=15)
        result = color.to_dict()
        self.assertEqual(result, {"r": 255, "g": 128, "b": 64, "tolerance": 15})


class TestAction(unittest.TestCase):
    """Тесты для модели Action"""

    def test_create_action(self):
        """Создание действия"""
        action = Action(
            id="test_1",
            action_type=ActionType.MOUSE_CLICK,
            name="Тест клика"
        )
        self.assertEqual(action.id, "test_1")
        self.assertEqual(action.action_type, ActionType.MOUSE_CLICK)
        self.assertEqual(action.name, "Тест клика")
        self.assertTrue(action.enabled)
        self.assertEqual(action.delay_before_ms, 0)

    def test_action_with_coordinates(self):
        """Действие с координатами"""
        coord = Coordinates(x=100, y=200)
        action = Action(
            id="test_2",
            action_type=ActionType.MOUSE_CLICK,
            name="Клик",
            coordinates=coord
        )
        self.assertEqual(action.coordinates.x, 100)

    def test_action_to_dict(self):
        """Сериализация в словарь"""
        action = Action(
            id="test_3",
            action_type=ActionType.MOUSE_CLICK,
            name="Клик",
            coordinates=Coordinates(x=100, y=200),
            mouse_button="left",
            metadata={"key": "value"}
        )
        result = action.to_dict()
        self.assertEqual(result["id"], "test_3")
        self.assertEqual(result["action_type"], "MOUSE_CLICK")
        self.assertEqual(result["coordinates"]["x"], 100)
        self.assertEqual(result["metadata"]["key"], "value")

    def test_action_from_dict(self):
        """Десериализация из словаря"""
        data = {
            "id": "test_4",
            "action_type": "MOUSE_CLICK",
            "name": "Клик",
            "enabled": True,
            "coordinates": {"x": 100, "y": 200},
            "mouse_button": "left",
            "metadata": {}
        }
        action = Action.from_dict(data)
        self.assertEqual(action.id, "test_4")
        self.assertEqual(action.action_type, ActionType.MOUSE_CLICK)
        self.assertEqual(action.coordinates.x, 100)


class TestTaskRow(unittest.TestCase):
    """Тесты для модели TaskRow"""

    def test_create_row(self):
        """Создание строки"""
        row = TaskRow(id="row_1", name="Тестовая строка")
        self.assertEqual(row.id, "row_1")
        self.assertEqual(row.name, "Тестовая строка")
        self.assertTrue(row.enabled)
        self.assertEqual(len(row.actions), 0)

    def test_add_action(self):
        """Добавление действия"""
        row = TaskRow(id="row_2", name="Строка")
        action = Action(id="act_1", action_type=ActionType.MOUSE_CLICK, name="Клик")
        row.add_action(action)
        self.assertEqual(len(row.actions), 1)
        self.assertEqual(row.actions[0].name, "Клик")

    def test_remove_action(self):
        """Удаление действия"""
        row = TaskRow(id="row_3", name="Строка")
        action1 = Action(id="act_1", action_type=ActionType.MOUSE_CLICK, name="Клик 1")
        action2 = Action(id="act_2", action_type=ActionType.MOUSE_CLICK, name="Клик 2")
        row.add_action(action1)
        row.add_action(action2)

        result = row.remove_action("act_1")
        self.assertTrue(result)
        self.assertEqual(len(row.actions), 1)
        self.assertEqual(row.actions[0].id, "act_2")

    def test_remove_nonexistent_action(self):
        """Удаление несуществующего действия"""
        row = TaskRow(id="row_4", name="Строка")
        result = row.remove_action("nonexistent")
        self.assertFalse(result)


class TestTaskBoard(unittest.TestCase):
    """Тесты для модели TaskBoard"""

    def test_create_board(self):
        """Создание доски"""
        board = TaskBoard(id="board_1", name="Тестовая доска")
        self.assertEqual(board.id, "board_1")
        self.assertEqual(board.name, "Тестовая доска")
        self.assertEqual(len(board.rows), 0)

    def test_add_row(self):
        """Добавление строки"""
        board = TaskBoard(id="board_2", name="Доска")
        row = TaskRow(id="row_1", name="Строка 1")
        board.add_row(row)
        self.assertEqual(len(board.rows), 1)

    def test_get_all_actions(self):
        """Получение всех действий"""
        board = TaskBoard(id="board_3", name="Доска")
        
        row1 = TaskRow(id="row_1", name="Строка 1", enabled=True)
        row1.add_action(Action(id="act_1", action_type=ActionType.MOUSE_CLICK, name="Клик 1", enabled=True))
        row1.add_action(Action(id="act_2", action_type=ActionType.MOUSE_CLICK, name="Клик 2", enabled=False))
        
        row2 = TaskRow(id="row_2", name="Строка 2", enabled=True)
        row2.add_action(Action(id="act_3", action_type=ActionType.WAIT_TIME, name="Ожидание", enabled=True))
        
        board.add_row(row1)
        board.add_row(row2)

        actions = board.get_all_actions()
        self.assertEqual(len(actions), 2)  # Только включённые действия

    def test_board_to_dict(self):
        """Сериализация доски"""
        board = TaskBoard(id="board_4", name="Доска")
        row = TaskRow(id="row_1", name="Строка")
        row.add_action(Action(id="act_1", action_type=ActionType.MOUSE_CLICK, name="Клик"))
        board.add_row(row)

        result = board.to_dict()
        self.assertEqual(result["id"], "board_4")
        self.assertEqual(len(result["rows"]), 1)
        self.assertEqual(len(result["rows"][0]["actions"]), 1)


# =============================================================================
# ТЕСТЫ ОБРАБОТЧИКОВ ДЕЙСТВИЙ
# =============================================================================

class TestMouseClickHandler(unittest.TestCase):
    """Тесты для MouseClickHandler"""

    def setUp(self):
        """Настройка тестов"""
        self.mock_mouse = Mock(spec=IMouseService)
        self.handler = MouseClickHandler(mouse=self.mock_mouse)

    def test_successful_click(self):
        """Успешный клик"""
        action = Action(
            id="click_1",
            action_type=ActionType.MOUSE_CLICK,
            name="Клик",
            coordinates=Coordinates(x=100, y=200),
            mouse_button="left"
        )

        result = asyncio.run(self.handler.execute(action))

        self.assertTrue(result.success)
        self.assertEqual(result.action_id, "click_1")
        self.assertIn("Клик left в (100, 200)", result.message)
        self.mock_mouse.move_to.assert_called_once_with(100, 200)
        self.mock_mouse.click.assert_called_once_with("left")

    def test_click_without_coordinates(self):
        """Клик без координат"""
        action = Action(
            id="click_2",
            action_type=ActionType.MOUSE_CLICK,
            name="Клик",
            coordinates=None
        )

        result = asyncio.run(self.handler.execute(action))

        self.assertFalse(result.success)
        self.assertIn("Не указаны координаты", result.error)

    def test_click_without_mouse_service(self):
        """Клик без сервиса мыши"""
        handler = MouseClickHandler(mouse=None)
        action = Action(
            id="click_3",
            action_type=ActionType.MOUSE_CLICK,
            name="Клик",
            coordinates=Coordinates(x=100, y=200)
        )

        result = asyncio.run(handler.execute(action))

        self.assertFalse(result.success)
        self.assertIn("Сервис мыши не инициализирован", result.error)


class TestMouseMoveHandler(unittest.TestCase):
    """Тесты для MouseMoveHandler"""

    def setUp(self):
        """Настройка тестов"""
        self.mock_mouse = Mock(spec=IMouseService)
        self.handler = MouseMoveHandler(mouse=self.mock_mouse)

    def test_successful_move(self):
        """Успешное перемещение"""
        action = Action(
            id="move_1",
            action_type=ActionType.MOUSE_MOVE,
            name="Перемещение",
            coordinates=Coordinates(x=300, y=400)
        )

        result = asyncio.run(self.handler.execute(action))

        self.assertTrue(result.success)
        self.mock_mouse.move_to.assert_called_once_with(300, 400, 0)

    def test_move_with_duration(self):
        """Перемещение с длительностью"""
        action = Action(
            id="move_2",
            action_type=ActionType.MOUSE_MOVE,
            name="Перемещение",
            coordinates=Coordinates(x=300, y=400),
            metadata={"move_duration_ms": 500}
        )

        result = asyncio.run(self.handler.execute(action))

        self.assertTrue(result.success)
        self.mock_mouse.move_to.assert_called_once_with(300, 400, 500)


class TestKeyPressHandler(unittest.TestCase):
    """Тесты для KeyPressHandler"""

    def setUp(self):
        """Настройка тестов"""
        self.mock_keyboard = Mock(spec=IKeyboardService)
        self.handler = KeyPressHandler(keyboard=self.mock_keyboard)

    def test_successful_key_press(self):
        """Успешное нажатие клавиши"""
        action = Action(
            id="key_1",
            action_type=ActionType.KEY_PRESS,
            name="Нажатие",
            key="enter"
        )

        result = asyncio.run(self.handler.execute(action))

        self.assertTrue(result.success)
        self.mock_keyboard.press.assert_called_once_with("enter")

    def test_key_press_without_key(self):
        """Нажатие без клавиши"""
        action = Action(
            id="key_2",
            action_type=ActionType.KEY_PRESS,
            name="Нажатие",
            key=None
        )

        result = asyncio.run(self.handler.execute(action))

        self.assertFalse(result.success)
        self.assertIn("Не указана клавиша", result.error)


class TestWaitTimeHandler(unittest.TestCase):
    """Тесты для WaitTimeHandler"""

    def setUp(self):
        """Настройка тестов"""
        self.handler = WaitTimeHandler()

    def test_wait_time(self):
        """Ожидание времени"""
        action = Action(
            id="wait_1",
            action_type=ActionType.WAIT_TIME,
            name="Ожидание",
            delay_before_ms=100
        )

        start = datetime.now()
        result = asyncio.run(self.handler.execute(action))
        elapsed = (datetime.now() - start).total_seconds() * 1000

        self.assertTrue(result.success)
        self.assertGreaterEqual(elapsed, 90)  # С небольшим допуском

    def test_wait_time_from_metadata(self):
        """Ожидание из metadata"""
        action = Action(
            id="wait_2",
            action_type=ActionType.WAIT_TIME,
            name="Ожидание",
            delay_before_ms=0,
            metadata={"wait_ms": 150}
        )

        start = datetime.now()
        result = asyncio.run(self.handler.execute(action))
        elapsed = (datetime.now() - start).total_seconds() * 1000

        self.assertTrue(result.success)
        self.assertGreaterEqual(elapsed, 140)


# =============================================================================
# ТЕСТЫ РЕЕСТРА ОБРАБОТЧИКОВ
# =============================================================================

class TestActionHandlerRegistry(unittest.TestCase):
    """Тесты для ActionHandlerRegistry"""

    def test_create_registry(self):
        """Создание реестра"""
        registry = ActionHandlerRegistry()
        
        # Проверка регистрации обработчиков по умолчанию
        self.assertIsNotNone(registry.get_handler(ActionType.MOUSE_CLICK))
        self.assertIsNotNone(registry.get_handler(ActionType.MOUSE_MOVE))
        self.assertIsNotNone(registry.get_handler(ActionType.KEY_PRESS))
        self.assertIsNotNone(registry.get_handler(ActionType.WAIT_TIME))

    def test_get_handler(self):
        """Получение обработчика"""
        registry = ActionHandlerRegistry()
        handler = registry.get_handler(ActionType.MOUSE_CLICK)
        self.assertIsInstance(handler, MouseClickHandler)

    def test_register_custom_handler(self):
        """Регистрация пользовательского обработчика"""
        registry = ActionHandlerRegistry()
        custom_handler = Mock(spec=BaseActionHandler)
        
        registry.register_handler(ActionType.LOOP, custom_handler)
        self.assertEqual(registry.get_handler(ActionType.LOOP), custom_handler)


# =============================================================================
# ТЕСТЫ EXECUTION ENGINE
# =============================================================================

class TestExecutionEngine(unittest.TestCase):
    """Тесты для ExecutionEngine"""

    def setUp(self):
        """Настройка тестов"""
        self.mock_mouse = Mock(spec=IMouseService)
        registry = ActionHandlerRegistry(mouse=self.mock_mouse)
        self.engine = ExecutionEngine(registry)

    def test_execute_single_action(self):
        """Выполнение одного действия"""
        board = TaskBoard(id="board_1", name="Доска")
        row = TaskRow(id="row_1", name="Строка")
        row.add_action(Action(
            id="act_1",
            action_type=ActionType.MOUSE_CLICK,
            name="Клик",
            enabled=True,
            coordinates=Coordinates(x=100, y=100)
        ))
        board.add_row(row)

        results = asyncio.run(self.engine.execute_board(board))

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].success)

    def test_execute_multiple_actions(self):
        """Выполнение нескольких действий"""
        board = TaskBoard(id="board_2", name="Доска")
        row = TaskRow(id="row_1", name="Строка")
        
        row.add_action(Action(
            id="act_1",
            action_type=ActionType.MOUSE_CLICK,
            name="Клик 1",
            enabled=True,
            coordinates=Coordinates(x=100, y=100)
        ))
        row.add_action(Action(
            id="act_2",
            action_type=ActionType.WAIT_TIME,
            name="Ожидание",
            enabled=True,
            delay_before_ms=50
        ))
        
        board.add_row(row)

        results = asyncio.run(self.engine.execute_board(board))

        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.success for r in results))

    def test_skip_disabled_actions(self):
        """Пропуск отключённых действий"""
        board = TaskBoard(id="board_3", name="Доска")
        row = TaskRow(id="row_1", name="Строка")
        
        row.add_action(Action(
            id="act_1",
            action_type=ActionType.MOUSE_CLICK,
            name="Клик",
            enabled=False,  # Отключено
            coordinates=Coordinates(x=100, y=100)
        ))
        
        board.add_row(row)

        results = asyncio.run(self.engine.execute_board(board))

        self.assertEqual(len(results), 0)

    def test_stop_execution(self):
        """Остановка выполнения"""
        self.engine.is_running = True
        self.engine.stop()
        self.assertFalse(self.engine.is_running)

    def test_pause_resume(self):
        """Пауза и продолжение"""
        self.engine.pause()
        self.assertTrue(self.engine.is_paused)
        
        self.engine.resume()
        self.assertFalse(self.engine.is_paused)

    def test_variables(self):
        """Переменные"""
        self.engine.set_variable("test_var", "test_value")
        value = self.engine.get_variable("test_var")
        self.assertEqual(value, "test_value")


# =============================================================================
# ТЕСТЫ BACKEND APPLICATION
# =============================================================================

class TestBackendApplication(unittest.TestCase):
    """Тесты для BackendApplication"""

    def setUp(self):
        """Настройка тестов"""
        self.mock_mouse = Mock(spec=IMouseService)
        self.app = BackendApplication(mouse=self.mock_mouse)

    def test_create_board(self):
        """Создание доски"""
        board = self.app.create_board("Тестовая доска")
        self.assertEqual(board.name, "Тестовая доска")
        self.assertEqual(self.app.current_board, board)
        self.assertIn(board, self.app.boards)

    def test_add_row(self):
        """Добавление строки"""
        self.app.create_board("Доска")
        row = self.app.add_row("Тестовая строка")
        self.assertEqual(row.name, "Тестовая строка")
        self.assertIn(row, self.app.current_board.rows)

    def test_add_action(self):
        """Добавление действия"""
        self.app.create_board("Доска")
        row = self.app.add_row("Строка")
        
        action = Action(
            id="act_1",
            action_type=ActionType.MOUSE_CLICK,
            name="Клик"
        )
        
        self.app.add_action(row.id, action)
        self.assertIn(action, row.actions)

    def test_add_action_to_nonexistent_row(self):
        """Добавление действия в несуществующую строку"""
        self.app.create_board("Доска")
        
        with self.assertRaises(ValueError):
            self.app.add_action("nonexistent_row", Action(
                id="act_1",
                action_type=ActionType.MOUSE_CLICK,
                name="Клик"
            ))

    def test_save_and_load_board(self):
        """Сохранение и загрузка доски"""
        import tempfile
        import os

        # Создать доску
        self.app.create_board("Тест")
        row = self.app.add_row("Строка")
        self.app.add_action(row.id, Action(
            id="act_1",
            action_type=ActionType.MOUSE_CLICK,
            name="Клик",
            coordinates=Coordinates(x=100, y=100)
        ))

        # Сохранить
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            self.app.save_board(self.app.current_board, filepath)

            # Загрузить
            loaded_board = self.app.load_board(filepath)

            self.assertEqual(loaded_board.name, "Тест")
            self.assertEqual(len(loaded_board.rows), 1)
            self.assertEqual(len(loaded_board.rows[0].actions), 1)
            self.assertEqual(loaded_board.rows[0].actions[0].name, "Клик")
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_export_to_ahk(self):
        """Экспорт в AHK"""
        self.app.create_board("Тест")
        row = self.app.add_row("Строка")
        
        row.add_action(Action(
            id="act_1",
            action_type=ActionType.MOUSE_CLICK,
            name="Клик",
            coordinates=Coordinates(x=100, y=200)
        ))
        row.add_action(Action(
            id="act_2",
            action_type=ActionType.WAIT_TIME,
            name="Ожидание",
            delay_before_ms=1000
        ))

        ahk = self.app.export_to_ahk(self.app.current_board)

        self.assertIn("Click, left, 100, 200", ahk)
        self.assertIn("Sleep, 1000", ahk)


# =============================================================================
# ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# =============================================================================

class TestIntegration(unittest.TestCase):
    """Интеграционные тесты"""

    def test_full_workflow(self):
        """Полный рабочий процесс"""
        # Создание приложения с моками
        mock_mouse = Mock(spec=IMouseService)
        mock_keyboard = Mock(spec=IKeyboardService)
        app = BackendApplication(mouse=mock_mouse, keyboard=mock_keyboard)

        # Создание доски
        board = app.create_board("Рабочая доска")

        # Добавление строк
        row1 = app.add_row("Действие 1")
        row2 = app.add_row("Действие 2")

        # Добавление действий
        app.add_action(row1.id, Action(
            id="act_1",
            action_type=ActionType.MOUSE_CLICK,
            name="Клик",
            coordinates=Coordinates(x=500, y=500)
        ))

        app.add_action(row1.id, Action(
            id="act_2",
            action_type=ActionType.WAIT_TIME,
            name="Ожидание",
            delay_before_ms=100
        ))

        app.add_action(row2.id, Action(
            id="act_3",
            action_type=ActionType.KEY_PRESS,
            name="Enter",
            key="enter"
        ))

        # Проверка структуры
        self.assertEqual(len(board.rows), 2)
        self.assertEqual(len(row1.actions), 2)
        self.assertEqual(len(row2.actions), 1)

        # Выполнение
        results = asyncio.run(app.run_board(board))

        # Проверка результатов
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r.success for r in results))


if __name__ == "__main__":
    unittest.main()
