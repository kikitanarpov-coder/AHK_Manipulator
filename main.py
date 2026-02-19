"""
AHK Manipulator - Точка входа приложения
Связующий слой между бэкендом и UI
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

from app_logging import configure_logging, install_global_exception_hooks
from backend import (
    BackendApplication, MouseService, KeyboardService, 
    ScreenService, DatabaseService, TaskBoard
)
from ui.main_window import MainWindow

logger = logging.getLogger(__name__)


class BackendWorker(QObject):
    """
    Рабочий объект для связи UI и бэкенда
    Обеспечивает связь через сигналы
    """
    
    # Сигналы для UI
    execution_started = pyqtSignal()
    execution_finished = pyqtSignal(list)  # List[ExecutionResult]
    execution_error = pyqtSignal(str)
    progress_updated = pyqtSignal(int, int)  # current, total
    
    def __init__(self, backend: BackendApplication):
        super().__init__()
        self.backend = backend
    
    @pyqtSlot(object)
    def run_board(self, board: TaskBoard):
        """Запустить доску"""
        import asyncio
        
        loop = None
        try:
            self.execution_started.emit()
            
            # Создаём event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запускаем выполнение
            results = loop.run_until_complete(self.backend.run_board(board))
            
            # Сигнал о завершении
            self.execution_finished.emit(results)
        except Exception as e:
            logger.exception("Ошибка выполнения доски в worker")
            self.execution_error.emit(str(e))
        finally:
            if loop is not None:
                loop.close()


def create_backend() -> BackendApplication:
    """Создать бэкенд приложения"""
    # Создаём сервисы
    mouse_service = MouseService()
    keyboard_service = KeyboardService()
    screen_service = ScreenService()
    database_service = DatabaseService()
    
    # Создаём приложение
    backend = BackendApplication(
        mouse=mouse_service,
        keyboard=keyboard_service,
        screen=screen_service,
        database=database_service
    )
    
    return backend


def run_gui():
    """Запуск GUI приложения"""
    configure_logging()
    install_global_exception_hooks()
    app = QApplication(sys.argv)
    
    # Создаём бэкенд
    backend = create_backend()
    
    # Создаём рабочий объект
    worker = BackendWorker(backend)
    worker_thread = QThread()
    worker.moveToThread(worker_thread)
    worker_thread.start()
    
    # Создаём главное окно с бэкендом
    window = MainWindow(backend, worker, worker_thread)
    window.show()
    
    sys.exit(app.exec())


def run_cli_demo():
    """CLI демонстрация бэкенда"""
    from backend import CONFIG, ActionType, Action, Coordinates
    
    print(f"Запуск {CONFIG['app_name']} v{CONFIG['version']}")
    print("=" * 50)
    
    # Создаём бэкенд
    backend = create_backend()
    
    # Создаём доску
    board = backend.create_board("Тестовая доска")
    row = backend.add_row("Действие 1")
    
    # Добавляем действия
    backend.add_action(row.id, Action(
        id="action_1",
        action_type=ActionType.MOUSE_CLICK,
        name="Клик в центр",
        coordinates=Coordinates(960, 540)
    ))
    
    backend.add_action(row.id, Action(
        id="action_2",
        action_type=ActionType.WAIT_TIME,
        name="Ожидание 1 сек",
        delay_before_ms=1000
    ))
    
    print(f"✓ Создана доска: {board.name}")
    print(f"✓ Строк: {len(board.rows)}")
    print(f"✓ Действий: {len(board.get_all_actions())}")
    
    # Экспорт в AHK
    ahk_script = backend.export_to_ahk(board)
    print("\n--- AHK Script ---")
    print(ahk_script)
    
    print("\n--- Для запуска GUI используйте: python main.py ---")


def main():
    """Точка входа приложения"""
    configure_logging()
    install_global_exception_hooks()
    # CLI демонстрация включается явно.
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        run_cli_demo()
    else:
        run_gui()


if __name__ == "__main__":
    main()
