#!/usr/bin/env python3
"""
Полная диагностика и тестирование AHK Manipulator
"""

import sys
import os
import time
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


def test_1_backend():
    """Тест 1: Бэкенд"""
    print("=" * 70)
    print("ТЕСТ 1: БЭКЕНД")
    print("=" * 70)
    
    backend = BackendApplication(
        mouse=MouseService(),
        keyboard=KeyboardService(),
        screen=ScreenService(),
        database=DatabaseService()
    )
    
    board = backend.create_board("Тестовая доска")
    row = backend.add_row("Тестовая строка")
    
    action = Action(
        id="test_1",
        action_type=ActionType.MOUSE_CLICK,
        name="Клик",
        coordinates=Coordinates(x=100, y=100),
        delay_before_ms=500,
        delay_after_ms=500
    )
    backend.add_action(row.id, action)
    
    print(f"✓ Доска: {board.name}")
    print(f"✓ Строка: {row.name}")
    print(f"✓ Действие: {action.name}")
    print(f"  - Тип: {action.action_type}")
    print(f"  - Координаты: {action.coordinates}")
    print(f"  - Задержка до: {action.delay_before_ms}мс")
    print(f"  - Задержка после: {action.delay_after_ms}мс")
    
    return backend


def test_2_ui(backend):
    """Тест 2: UI"""
    print("\n" + "=" * 70)
    print("ТЕСТ 2: UI")
    print("=" * 70)
    
    worker = BackendWorker(backend)
    window = MainWindow(backend, worker)
    
    print("✓ Окно создано")
    
    window.task_board_widget.refresh()
    print("✓ Refresh доски успешен")
    
    # Проверка ActionChip
    from ui.task_board_widget import ActionChip
    action = backend.current_board.rows[0].actions[0]
    chip = ActionChip(action, backend, backend.current_board.rows[0])
    print(f"✓ ActionChip создан")
    print(f"  - Название: {chip.action.name}")
    print(f"  - Координаты отображаются: {chip.action.coordinates is not None}")
    
    return window, worker


def test_3_properties(window, backend):
    """Тест 3: Окно свойств"""
    print("\n" + "=" * 70)
    print("ТЕСТ 3: ОКНО СВОЙСТВ")
    print("=" * 70)
    
    action = backend.current_board.rows[0].actions[0]
    
    try:
        window.right_panel.set_action(action)
        print("✓ set_action вызван")
        
        # Проверка что виджеты созданы
        if hasattr(window.right_panel, 'prop_content_layout'):
            count = window.right_panel.prop_content_layout.count()
            print(f"✓ prop_content_layout: {count} элементов")
        else:
            print("✗ prop_content_layout не существует")
            
        # Проверка координат
        if hasattr(window.right_panel, 'prop_x_spin'):
            print(f"✓ prop_x_spin: {window.right_panel.prop_x_spin.value()}")
        else:
            print("✗ prop_x_spin не существует (это нормально для начала)")
            
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()


def test_4_execution(backend):
    """Тест 4: Выполнение с таймингами"""
    print("\n" + "=" * 70)
    print("ТЕСТ 4: ВЫПОЛНЕНИЕ С ТАЙМИНГАМИ")
    print("=" * 70)
    
    board = backend.create_board("Timing Test")
    row = backend.add_row("Timing Row")
    
    # Создаём последовательность действий
    actions = [
        Action(id="t1", action_type=ActionType.MOUSE_CLICK, name="Клик 1", 
               coordinates=Coordinates(100, 100), delay_before_ms=100),
        Action(id="t2", action_type=ActionType.WAIT_TIME, name="Ожидание 1с", 
               delay_before_ms=1000),
        Action(id="t3", action_type=ActionType.MOUSE_CLICK, name="Клик 2", 
               coordinates=Coordinates(200, 200), delay_before_ms=100),
    ]
    
    for action in actions:
        backend.add_action(row.id, action)
    
    print(f"✓ Добавлено {len(row.actions)} действий")
    
    # Запуск выполнения
    import asyncio
    
    start_time = time.time()
    
    async def run():
        results = await backend.run_board(board)
        return results
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(run())
    loop.close()
    
    elapsed = (time.time() - start_time) * 1000
    
    print(f"✓ Выполнение завершено за {elapsed:.0f}мс")
    print(f"  - Ожидаемое время: ~1300мс (100+1000+100+задержки)")
    print(f"  - Результаты:")
    for r in results:
        status = "✓" if r.success else "✗"
        print(f"    {status} {r.action_name}: {r.message or r.error}")


def test_5_coordinates_display(backend):
    """Тест 5: Отображение координат"""
    print("\n" + "=" * 70)
    print("ТЕСТ 5: ОТОБРАЖЕНИЕ КООРДИНАТ")
    print("=" * 70)
    
    action = backend.current_board.rows[0].actions[0]
    
    if action.coordinates:
        print(f"✓ Координаты установлены: ({action.coordinates.x}, {action.coordinates.y})")
    else:
        print("✗ Координаты не установлены")
        
    # Проверка что координаты отображаются в ActionChip
    from ui.task_board_widget import ActionChip
    chip = ActionChip(action, backend, backend.current_board.rows[0])
    
    # Проверяем что координаты есть в action
    if chip.action.coordinates:
        print(f"✓ ActionChip имеет координаты: ({chip.action.coordinates.x}, {chip.action.coordinates.y})")
    else:
        print("✗ ActionChip не имеет координат")


def run_full_diagnostic():
    """Запуск полной диагностики"""
    print("\n" + "=" * 70)
    print("ПОЛНАЯ ДИАГНОСТИКА AHK MANIPULATOR")
    print("=" * 70)
    
    app = QApplication(sys.argv)
    
    # Тест 1
    backend = test_1_backend()
    
    # Тест 2
    window, worker = test_2_ui(backend)
    
    # Тест 3
    test_3_properties(window, backend)
    
    # Тест 4
    test_4_execution(backend)
    
    # Тест 5
    test_5_coordinates_display(backend)
    
    print("\n" + "=" * 70)
    print("ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("=" * 70)
    
    # Показать окно
    window.show()
    print("\nПриложение запущено.")
    print("Проверьте:")
    print("1. Окно свойств открывается при клике на действие")
    print("2. Координаты отображаются под названием действия")
    print("3. Тайминги выполняются последовательно")
    
    app.exec()


if __name__ == "__main__":
    run_full_diagnostic()
