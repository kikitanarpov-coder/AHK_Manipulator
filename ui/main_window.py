"""
Главное окно приложения AHK Manipulator
Работает с BackendApplication через сигналы
"""
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QStatusBar, QSplitter, QSizePolicy,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence

from backend import BackendApplication, TaskBoard, ActionType, Action, Coordinates
from ui.task_board_widget import TaskBoardWidget
from ui.right_panel import RightPanel
from ui.screen_overlay import ScreenOverlay
from ui.settings_dialog import SettingsDialog
from ui.styles import get_stylesheet
from ui.recording_manager import RecordingManager
from ui.recording_manager import DEFAULT_RECORDING_STOP_COMBO

import uuid

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    run_requested = pyqtSignal(object)

    def __init__(self, backend: BackendApplication, worker, worker_thread=None):
        super().__init__()
        self.backend = backend
        self.worker = worker
        self.worker_thread = worker_thread
        self.screen_overlay = None
        self._is_running = False
        self.recording_manager = RecordingManager(self.backend, self)
        self.recording_manager.recording_started.connect(self._on_recording_started)
        self.recording_manager.recording_stopped.connect(self._on_recording_stopped)
        self.recording_manager.recording_error.connect(self._on_recording_error)
        self.recording_manager.hud_updated.connect(self._on_recording_event)

        # Подключаем сигналы от worker только если он есть
        if self.worker:
            self.worker.execution_started.connect(self._on_execution_started)
            self.worker.execution_finished.connect(self._on_execution_finished)
            self.worker.execution_error.connect(self._on_execution_error)
            self.run_requested.connect(self.worker.run_board)

        self._init_ui()
        self._create_toolbar()
        self._connect_signals()

    def _init_ui(self):
        """Инициализация UI"""
        self.setWindowTitle("AHK Manipulator")
        self.setMinimumSize(1024, 768)
        self.resize(1200, 800)
        
        # Применяем профессиональный стиль
        self.setStyleSheet(get_stylesheet("dark"))

        # Центральный виджет
        central_widget = QWidget()
        central_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter для task-доски и правой панели
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Task-доска (основная область)
        self.task_board_widget = TaskBoardWidget(self.backend)
        self.task_board_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        splitter.addWidget(self.task_board_widget)

        # Правая панель (контекстная)
        self.right_panel = RightPanel(self.backend)
        self.right_panel.setMinimumWidth(280)
        self.right_panel.setMaximumWidth(400)
        self.right_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        splitter.addWidget(self.right_panel)

        # Пропорции splitter (70% доска, 30% панель)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([800, 350])

        main_layout.addWidget(splitter)

        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готов")

        # Таймер обновления статуса
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)

    def _create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = QToolBar("Основная панель")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Новая доска
        self.action_new = QAction("📄 Новая", self)
        self.action_new.setShortcut(QKeySequence.StandardKey.New)
        self.action_new.triggered.connect(self._new_board)
        toolbar.addAction(self.action_new)

        # Открыть
        self.action_open = QAction("📂 Открыть", self)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open.triggered.connect(self._open_board)
        toolbar.addAction(self.action_open)

        # Сохранить
        self.action_save = QAction("💾 Сохранить", self)
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save.triggered.connect(self._save_board)
        toolbar.addAction(self.action_save)

        toolbar.addSeparator()

        # Запись
        self.action_record = QAction("🔴 Запись", self)
        self.action_record.setShortcut(QKeySequence("F9"))
        self.action_record.triggered.connect(self._toggle_recording)
        toolbar.addAction(self.action_record)

        # Запуск
        self.action_run = QAction("▶ Запуск", self)
        self.action_run.setShortcut(QKeySequence("F5"))
        self.action_run.triggered.connect(self._run_board)
        toolbar.addAction(self.action_run)

        # Стоп
        self.action_stop = QAction("⏹ Стоп", self)
        self.action_stop.setShortcut(QKeySequence("Shift+F5"))
        self.action_stop.triggered.connect(self._stop_execution)
        self.action_stop.setEnabled(False)
        toolbar.addAction(self.action_stop)

        toolbar.addSeparator()

        # Импорт из AHK
        self.action_import = QAction("📥 Импорт AHK", self)
        self.action_import.triggered.connect(self._import_ahk)
        toolbar.addAction(self.action_import)

        # Экспорт в AHK
        self.action_export = QAction("📜 Экспорт AHK", self)
        self.action_export.triggered.connect(self._export_ahk)
        toolbar.addAction(self.action_export)

        # Настройки
        self.action_settings = QAction("⚙ Настройки", self)
        self.action_settings.triggered.connect(self._show_settings)
        toolbar.addAction(self.action_settings)

    def _connect_signals(self):
        """Подключение сигналов"""
        # От task-доски
        self.task_board_widget.action_selected.connect(
            self.right_panel.set_action
        )
        self.task_board_widget.row_selected.connect(
            self.right_panel.set_row
        )
        self.task_board_widget.board_modified.connect(
            self._on_board_modified
        )

        # От правой панели
        self.right_panel.action_added.connect(
            self._on_action_added
        )
        self.right_panel.action_modified.connect(
            self._on_action_modified
        )
        self.right_panel.coordinates_captured.connect(
            self._on_coordinates_captured
        )
        self.right_panel.row_modified.connect(
            self._on_row_modified
        )

    # ===== Обработчики сигналов бэкенда =====

    def _on_execution_started(self):
        """Начало выполнения"""
        self._is_running = True
        self.action_run.setEnabled(False)
        self.action_stop.setEnabled(True)
        self.statusBar.showMessage("▶ Выполнение...")

    def _on_execution_finished(self, results):
        """Завершение выполнения"""
        self._is_running = False
        self.action_run.setEnabled(True)
        self.action_stop.setEnabled(False)
        
        success_count = sum(1 for r in results if r.success)
        self.statusBar.showMessage(f"✓ Выполнено: {success_count}/{len(results)}")

    def _on_execution_error(self, error_msg):
        """Ошибка выполнения"""
        self._is_running = False
        self.action_run.setEnabled(True)
        self.action_stop.setEnabled(False)
        self.statusBar.showMessage(f"✗ Ошибка: {error_msg}")
        QMessageBox.critical(self, "Ошибка выполнения", error_msg)

    # ===== Обработчики UI =====

    def _on_board_modified(self):
        """Обработчик изменения доски"""
        self.task_board_widget.refresh()
        self.statusBar.showMessage("Доска изменена")

    def _on_action_added(self, action):
        """Обработчик добавления действия"""
        self.task_board_widget.refresh()
        self.statusBar.showMessage(f"Добавлено: {action.name}")

    def _on_action_modified(self, action):
        """Обработчик изменения действия"""
        self.task_board_widget.refresh()
        self.statusBar.showMessage(f"Изменено: {action.name}")

    def _on_row_modified(self, row):
        """Обработчик изменения строки"""
        self.task_board_widget.refresh()
        self.statusBar.showMessage(f"Изменена строка: {row.name}")

    def _on_coordinates_captured(self, x, y):
        """Обработчик захвата координат"""
        self.statusBar.showMessage(f"Захвачены координаты: ({x}, {y})")

    def _update_status(self):
        """Обновление статус-бара"""
        if self.backend.engine.is_running:
            self.statusBar.showMessage("▶ Выполнение...")
        else:
            board_name = self.backend.current_board.name if self.backend.current_board else "Нет доски"
            self.statusBar.showMessage(f"Готов | {board_name}")

    # ===== Действия toolbar =====

    def _new_board(self):
        """Создать новую доску"""
        reply = QMessageBox.question(
            self, "Новая доска",
            "Создать новую task-доску? Несохранённые изменения будут потеряны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.backend.create_board("Без названия")
            self.task_board_widget.refresh()
            self.right_panel.reset()
            self.statusBar.showMessage("Создана новая доска")

    def _open_board(self):
        """Открыть доску"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Открыть доску", "", "JSON Files (*.json);;All Files (*)"
        )

        if filepath:
            try:
                board = self.backend.load_board(filepath)
                self.backend.current_board = board
                self.task_board_widget.refresh()
                self.right_panel.reset()
                self.statusBar.showMessage(f"Открыто: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")

    def _save_board(self):
        """Сохранить доску"""
        if not self.backend.current_board:
            QMessageBox.warning(self, "Предупреждение", "Нет активной доски")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Сохранить доску", "", "JSON Files (*.json);;All Files (*)"
        )

        if filepath:
            self.backend.save_board(self.backend.current_board, filepath)
            self.statusBar.showMessage(f"Сохранено: {filepath}")

    def _toggle_recording(self):
        """Переключить запись"""
        if hasattr(self, '_is_recording') and self._is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """Начать запись"""
        try:
            self.recording_manager.start()
        except Exception as e:
            logger.exception("Ошибка при начале записи")
            self.action_record.setText("🔴 Запись")

    def _stop_recording(self):
        """Остановить запись"""
        self.recording_manager.stop()
        self.task_board_widget.refresh()

    def _run_board(self):
        """Запустить доску"""
        if not self.backend.current_board:
            QMessageBox.warning(self, "Предупреждение", "Нет активной доски")
            return

        if not self.backend.current_board.rows:
            QMessageBox.warning(self, "Предупреждение", "Доска пуста — добавьте строки с действиями")
            return

        if self._is_running:
            QMessageBox.information(self, "Выполнение", "Доска уже выполняется")
            return

        if not self.worker:
            QMessageBox.critical(self, "Ошибка", "Worker не инициализирован")
            return

        # Запуск в worker thread (QueuedConnection)
        self.run_requested.emit(self.backend.current_board)

    def _stop_execution(self):
        """Остановить выполнение"""
        try:
            self.backend.stop_execution()
            self.action_run.setEnabled(True)
            self.action_stop.setEnabled(False)
            self.statusBar.showMessage("⏹ Остановлено")
        except Exception as e:
            logger.exception("Ошибка при остановке выполнения")
            self.action_run.setEnabled(True)
            self.action_stop.setEnabled(False)

    def _export_ahk(self):
        """Экспорт в AHK"""
        if not self.backend.current_board:
            QMessageBox.warning(self, "Предупреждение", "Нет активной доски")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Экспорт в AHK", "", "AHK Files (*.ahk);;All Files (*)"
        )

        if filepath:
            try:
                ahk_script = self.backend.export_to_ahk(self.backend.current_board)
                path = Path(filepath).expanduser()
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('w', encoding='utf-8') as f:
                    f.write(ahk_script)
                self.statusBar.showMessage(f"Экспортировано: {filepath}")
            except Exception as e:
                logger.exception("Ошибка при экспорте AHK")
                QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать файл:\n{e}")
    
    def _import_ahk(self):
        """Импорт из AHK"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Импорт из AHK", "", "AHK Files (*.ahk);;JSON Files (*.json);;All Files (*)"
        )

        if filepath:
            try:
                board = self.backend.import_from_file(filepath)
                self.backend.current_board = board
                self.task_board_widget.refresh()
                self.right_panel.reset()
                self.statusBar.showMessage(f"Импортировано: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать файл:\n{e}")

    def _show_settings(self):
        """Показать настройки"""
        try:
            dialog = SettingsDialog(self, databases=self.backend.databases)
            dialog.databases_changed.connect(self._on_databases_changed)
            dialog.exec()
        except Exception as e:
            logger.exception("Ошибка при открытии настроек")

    def _on_databases_changed(self, databases: list):
        """Обработчик изменения баз данных"""
        self.backend.databases = databases
        self.statusBar.showMessage(f"Базы данных обновлены: {len(databases)}")

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        self.recording_manager.shutdown()

        if self.backend.engine.is_running:
            self.backend.stop_execution()

        self.backend.shutdown()

        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait(3000)

        event.accept()

    def _on_recording_started(self):
        self._is_recording = True
        self.action_record.setText("⏹ Стоп запись")
        self.statusBar.showMessage(f"🔴 Recording... stop: {DEFAULT_RECORDING_STOP_COMBO.upper()}")

    def _on_recording_stopped(self, event_count: int):
        self._is_recording = False
        self.action_record.setText("🔴 Запись")
        self.task_board_widget.refresh()
        self.statusBar.showMessage(f"Запись остановлена ({event_count} событий)")

    def _on_recording_error(self, message: str):
        self._is_recording = False
        self.action_record.setText("🔴 Запись")
        if self.recording_manager.is_recording:
            self.recording_manager.stop()
        self.statusBar.showMessage(f"Ошибка записи: {message}")

    def _on_recording_event(self, event_data: dict):
        # Сразу отображаем новые действия в строке записи.
        self.task_board_widget.refresh()
        evt_type = event_data.get("type", "")
        if evt_type == "wait":
            self.statusBar.showMessage(f"Recording WAIT {event_data.get('delay_before', 0)}ms")
