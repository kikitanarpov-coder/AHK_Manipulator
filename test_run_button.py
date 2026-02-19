#!/usr/bin/env python3
"""
Тест кнопки "Запуск"
"""

import sys
import os
import unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt6.QtWidgets import QApplication
except ModuleNotFoundError:
    raise unittest.SkipTest("PyQt6 is not installed in the current environment")
from backend import BackendApplication, Action, ActionType, Coordinates, MouseService, KeyboardService, ScreenService, DatabaseService
from ui.main_window import MainWindow
from main import BackendWorker
import uuid
import time

def test_run_button():
    """Тест кнопки запуска"""
    app = QApplication(sys.argv)
    
    # Создаём бэкенд с сервисами
    backend = BackendApplication(
        mouse=MouseService(),
        keyboard=KeyboardService(),
        screen=ScreenService(),
        database=DatabaseService()
    )
    
    # Создаём worker
    worker = BackendWorker(backend)
    
    window = MainWindow(backend, worker)
    window.show()
    
    # Создать тестовую доску
    print("Создание тестовой доски...")
    board = backend.create_board('Тест запуск')
    row = backend.add_row('Тестовая строка')
    
    # Добавить действие
    action = Action(
        id=str(uuid.uuid4()),
        action_type=ActionType.WAIT_TIME,
        name='Ожидание 1 сек',
        enabled=True,
        delay_before_ms=1000
    )
    backend.add_action(row.id, action)
    
    # Добавить ещё одно действие
    action2 = Action(
        id=str(uuid.uuid4()),
        action_type=ActionType.MOUSE_CLICK,
        name='Клик',
        enabled=True,
        coordinates=Coordinates(500, 500)
    )
    backend.add_action(row.id, action2)
    
    print(f"✓ Доска создана: {board.name}")
    print(f"✓ Строк: {len(board.rows)}")
    print(f"✓ Действий: {len(board.get_all_actions())}")
    
    # Обновить UI
    window.task_board_widget.refresh()
    
    print("\n=== ТЕСТ КНОПКИ ЗАПУСКА ===")
    print("Нажмите кнопку '▶ Запуск' в приложении")
    print("Или нажмите F5")
    print("\nОжидаемый результат:")
    print("1. Выполнение начнётся")
    print("2. Действия выполнятся по порядку")
    print("3. Не будет вылета приложения")
    print("4. Появится сообщение '✓ Выполнение завершено'")
    
    print("\nПриложение запущено. Тестирование...")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_run_button()
