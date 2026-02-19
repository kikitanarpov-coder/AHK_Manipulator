#!/usr/bin/env python3
"""
Полный тест функционала AHK Manipulator
"""

import sys
import os
import unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt6.QtWidgets import QApplication
except ModuleNotFoundError:
    raise unittest.SkipTest("PyQt6 is not installed in the current environment")
from backend import (
    BackendApplication, ActionType, Action, Coordinates,
    MouseService, KeyboardService, ScreenService, DatabaseService
)
from ui.main_window import MainWindow
from main import BackendWorker


def test_backend():
    """Тест бэкенда"""
    print("=" * 60)
    print("ТЕСТ 1: БЭКЕНД")
    print("=" * 60)
    
    # Создание бэкенда
    backend = BackendApplication(
        mouse=MouseService(),
        keyboard=KeyboardService(),
        screen=ScreenService(),
        database=DatabaseService()
    )
    print("✓ Бэкенд создан")
    
    # Создание доски
    board = backend.create_board("Тестовая доска")
    print(f"✓ Доска создана: {board.name}")
    
    # Добавление строки
    row = backend.add_row("Тестовая строка")
    print(f"✓ Строка добавлена: {row.name}")
    
    # Добавление действия
    action = Action(
        id="test_1",
        action_type=ActionType.MOUSE_CLICK,
        name="Тест клика",
        coordinates=Coordinates(100, 200)
    )
    backend.add_action(row.id, action)
    print(f"✓ Действие добавлено: {action.name}")
    
    # Проверка
    assert len(board.rows) == 1
    assert len(row.actions) == 1
    print("✓ Проверка прошла успешно")
    
    return backend


def test_ui(backend):
    """Тест UI"""
    print("\n" + "=" * 60)
    print("ТЕСТ 2: UI")
    print("=" * 60)
    
    # Создание worker
    worker = BackendWorker(backend)
    print("✓ Worker создан")
    
    # Создание окна
    try:
        window = MainWindow(backend, worker)
        print("✓ Окно создано успешно")
    except Exception as e:
        print(f"✗ Ошибка создания окна: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Тест refresh
    try:
        window.task_board_widget.refresh()
        print("✓ Refresh доски успешен")
    except Exception as e:
        print(f"✗ Ошибка refresh: {e}")
        import traceback
        traceback.print_exc()
    
    return window


def test_action_types(backend):
    """Тест всех типов действий"""
    print("\n" + "=" * 60)
    print("ТЕСТ 3: ВСЕ ТИПЫ ДЕЙСТВИЙ")
    print("=" * 60)
    
    board = backend.create_board("All Actions Test")
    row = backend.add_row("Test Row")
    
    test_actions = [
        (ActionType.MOUSE_CLICK, {"coordinates": Coordinates(100, 100)}),
        (ActionType.MOUSE_MOVE, {"coordinates": Coordinates(200, 200)}),
        (ActionType.KEY_PRESS, {"key": "enter"}),
        (ActionType.WAIT_TIME, {"delay_before_ms": 1000}),
        (ActionType.LOG, {"metadata": {"message": "Test log"}}),
    ]
    
    for action_type, kwargs in test_actions:
        try:
            action = Action(
                id=f"test_{action_type.name}",
                action_type=action_type,
                name=action_type.name,
                **kwargs
            )
            backend.add_action(row.id, action)
            print(f"✓ {action_type.name}")
        except Exception as e:
            print(f"✗ {action_type.name}: {e}")
    
    print(f"✓ Добавлено {len(row.actions)} действий")


def test_export(backend):
    """Тест экспорта"""
    print("\n" + "=" * 60)
    print("ТЕСТ 4: ЭКСПОРТ")
    print("=" * 60)
    
    board = backend.current_board
    
    # Экспорт в AHK
    try:
        ahk = backend.export_to_ahk(board)
        print(f"✓ Экспорт в AHK: {len(ahk)} символов")
        print(f"  Пример:\n{ahk[:200]}...")
    except Exception as e:
        print(f"✗ Экспорт в AHK: {e}")
    
    # Экспорт в Python
    try:
        py = backend.export_to_python(board)
        print(f"✓ Экспорт в Python: {len(py)} символов")
    except Exception as e:
        print(f"✗ Экспорт в Python: {e}")


def test_import(backend):
    """Тест импорта"""
    print("\n" + "=" * 60)
    print("ТЕСТ 5: ИМПОРТ")
    print("=" * 60)
    
    # Импорт из AHK строки
    ahk_text = """
Click, left, 100, 200
MouseMove, 300, 400
Send, {Enter}
Sleep, 1000
"""
    
    try:
        board = backend.import_from_ahk(ahk_text, "Imported Test")
        print(f"✓ Импорт из AHK: {len(board.rows[0].actions)} действий")
        for action in board.rows[0].actions:
            print(f"  - {action.action_type.name}")
    except Exception as e:
        print(f"✗ Импорт из AHK: {e}")
        import traceback
        traceback.print_exc()


def run_full_test():
    """Запуск всех тестов"""
    print("\n" + "=" * 60)
    print("ПОЛНЫЙ ТЕСТ ФУНКЦИОНАЛА AHK MANIPULATOR")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # Тест 1: Бэкенд
    backend = test_backend()
    
    # Тест 2: UI
    window = test_ui(backend)
    
    # Тест 3: Типы действий
    test_action_types(backend)
    
    # Тест 4: Экспорт
    test_export(backend)
    
    # Тест 5: Импорт
    test_import(backend)
    
    print("\n" + "=" * 60)
    print("ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 60)
    
    if window:
        window.show()
        print("\nПриложение запущено. Нажмите Ctrl+C для выхода.")
        try:
            app.exec()
        except KeyboardInterrupt:
            print("\nВыход...")


if __name__ == "__main__":
    run_full_test()
