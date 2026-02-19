#!/usr/bin/env python3
"""
Тест исправлений:
1. MOUSE_CLICK действие
2. Кнопка "Запись"
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

def test_all():
    """Тест всех исправлений"""
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
    print("=" * 50)
    print("ТЕСТ ИСПРАВЛЕНИЙ")
    print("=" * 50)

    print("\n1. Создание тестовой доски...")
    board = backend.create_board('Тест исправлений')
    row = backend.add_row('Тестовая строка')

    # Добавить MOUSE_CLICK действие
    print("2. Добавление MOUSE_CLICK действия...")
    click_action = Action(
        id=str(uuid.uuid4()),
        action_type=ActionType.MOUSE_CLICK,
        name='Тест клика',
        enabled=True,
        coordinates=Coordinates(500, 500),
        mouse_button='left'
    )
    backend.add_action(row.id, click_action)

    # Добавить WAIT_TIME действие
    print("3. Добавление WAIT_TIME действия...")
    wait_action = Action(
        id=str(uuid.uuid4()),
        action_type=ActionType.WAIT_TIME,
        name='Ожидание 1 сек',
        enabled=True,
        delay_before_ms=1000
    )
    backend.add_action(row.id, wait_action)

    # Добавить ещё один клик
    print("4. Добавление ещё одного клика...")
    click_action2 = Action(
        id=str(uuid.uuid4()),
        action_type=ActionType.MOUSE_CLICK,
        name='Тест клика 2',
        enabled=True,
        coordinates=Coordinates(600, 600),
        mouse_button='left'
    )
    backend.add_action(row.id, click_action2)

    print(f"\n✓ Доска создана: {board.name}")
    print(f"✓ Строк: {len(board.rows)}")
    print(f"✓ Действий: {len(board.get_all_actions())}")

    # Обновить UI
    window.task_board_widget.refresh()
    
    print("\n" + "=" * 50)
    print("ТЕСТ 1: Кнопка ЗАПУСК (F5)")
    print("=" * 50)
    print("\nНажмите '▶ Запуск' или F5")
    print("Ожидаемый результат:")
    print("  - Мышь переместится в (500, 500) и кликнет")
    print("  - Ожидание 1 секунда")
    print("  - Мышь переместится в (600, 600) и кликнет")
    print("  - Сообщение '✓ Выполнение завершено'")
    print("  - Приложение НЕ вылетит")
    
    print("\n" + "=" * 50)
    print("ТЕСТ 2: Кнопка ЗАПИСЬ (F9)")
    print("=" * 50)
    print("\nНажмите '🔴 Запись' или F9")
    print("Ожидаемый результат:")
    print("  - Появится оверлей с координатами")
    print("  - Сообщение '🔴 Запись...'")
    print("  - Приложение НЕ вылетит")
    print("\nДля остановки нажмите F9 ещё раз")
    
    print("\n" + "=" * 50)
    print("Приложение запущено. Тестирование...")
    print("=" * 50)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_all()
