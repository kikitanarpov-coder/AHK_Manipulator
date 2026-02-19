"""
Виджет Task-доски - основная область с действиями
"""

import logging
import uuid

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFrame, QLabel, QPushButton, QCheckBox, QMenu, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QPoint, QMimeData
from PyQt6.QtGui import QDrag

from backend import BackendApplication, TaskBoard, TaskRow, Action, ActionType, Coordinates

logger = logging.getLogger(__name__)


class TaskBoardWidget(QWidget):
    """Виджет task-доски"""

    action_selected = pyqtSignal(object)  # Action
    row_selected = pyqtSignal(object)  # TaskRow
    board_modified = pyqtSignal()

    def __init__(self, backend: BackendApplication):
        super().__init__()
        self.backend = backend
        self._init_ui()
        self.refresh()
    
    def _init_ui(self):
        """Инициализация UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Заголовок
        header_layout = QHBoxLayout()

        self.title_label = QLabel("Task-доска")
        self.title_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold;
        """)
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Кнопка добавления строки
        self.add_row_btn = QPushButton("+ Добавить строку")
        self.add_row_btn.setMaximumHeight(28)
        self.add_row_btn.clicked.connect(self._add_row)
        header_layout.addWidget(self.add_row_btn)

        layout.addLayout(header_layout)

        # Scroll area для строк (горизонтальная прокрутка)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Контейнер для строк (горизонтальное расположение)
        self.rows_container = QWidget()
        self.rows_layout = QHBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(8)
        self.rows_layout.addStretch()

        self.scroll_area.setWidget(self.rows_container)
        layout.addWidget(self.scroll_area)
    
    def refresh(self):
        """Обновить отображение доски"""
        # Очистить текущие строки
        while self.rows_layout.count() > 1:  # 1 = stretch
            item = self.rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.backend.current_board:
            # Пустая доска
            empty_label = QLabel("Нет активной доски\nСоздайте новую или откройте существующую")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: gray; font-size: 14px;")
            self.rows_layout.insertWidget(0, empty_label)
            return

        # Обновить заголовок
        self.title_label.setText(f"Task-доска: {self.backend.current_board.name}")

        # Добавить строки
        for row in self.backend.current_board.rows:
            row_widget = TaskRowWidget(row, self.backend)
            row_widget.action_selected.connect(self.action_selected.emit)
            row_widget.row_selected.connect(self.row_selected.emit)
            row_widget.row_modified.connect(self.board_modified.emit)
            row_widget.delete_requested.connect(self._delete_row)
            self.rows_layout.insertWidget(
                self.rows_layout.count() - 1,
                row_widget
            )

    def _add_row(self):
        """Добавить новую строку"""
        row = self.backend.add_row()
        self.refresh()
        self.board_modified.emit()

    def _delete_row(self, row_id: str):
        """Удалить строку"""
        if self.backend.current_board:
            self.backend.current_board.remove_row(row_id)
            self.refresh()
            self.board_modified.emit()


class TaskRowWidget(QFrame):
    """Виджет одной строки task-доски"""

    action_selected = pyqtSignal(object)  # Action
    row_selected = pyqtSignal(object)  # TaskRow
    row_modified = pyqtSignal()
    delete_requested = pyqtSignal(str)  # row_id

    def __init__(self, row: TaskRow, backend: BackendApplication):
        super().__init__()
        self.row = row
        self.backend = backend
        self._drag_hover_index = -1

        self._init_ui()
        self._update_style()

    def _init_ui(self):
        """Инициализация UI"""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setAcceptDrops(True)
        self.setMinimumWidth(280)  # Минимальная ширина строки
        self.setMaximumWidth(350)  # Максимальная ширина строки

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)

        # Заголовок строки
        header_layout = QHBoxLayout()

        # Checkbox enabled
        self.enabled_cb = QCheckBox()
        self.enabled_cb.setChecked(self.row.enabled)
        self.enabled_cb.stateChanged.connect(self._on_enabled_changed)
        header_layout.addWidget(self.enabled_cb)

        # Название строки (кликом можно выбрать строку)
        self.name_label = QLabel(self.row.name)
        self.name_label.setStyleSheet("font-weight: bold; cursor: pointer;")
        self.name_label.mousePressEvent = lambda e: self._on_row_click()
        header_layout.addWidget(self.name_label)

        header_layout.addStretch()

        # Кнопка добавления действия
        add_action_btn = QPushButton("+ Действие")
        add_action_btn.clicked.connect(self._show_add_action_menu)
        header_layout.addWidget(add_action_btn)

        # Кнопка удаления строки
        delete_btn = QPushButton("🗑")
        delete_btn.setMaximumWidth(30)
        delete_btn.clicked.connect(self._on_delete)
        header_layout.addWidget(delete_btn)

        layout.addLayout(header_layout)

        # Контейнер действий (вертикальное расположение)
        self.actions_layout = QVBoxLayout()
        self.actions_layout.setSpacing(5)
        layout.addLayout(self.actions_layout)

        # Обновить действия
        self._refresh_actions()

    def _update_style(self):
        """Обновить стиль в зависимости от состояния"""
        if self.row.enabled:
            self.setStyleSheet("""
                TaskRowWidget {
                    background-color: #323232;
                    border: 1px solid #5c6265;
                    border-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                TaskRowWidget {
                    background-color: #2b2b2b;
                    border: 1px dashed #5c6265;
                    border-radius: 4px;
                }
            """)
    
    def _refresh_actions(self):
        """Обновить отображение действий"""
        # Очистить
        while self.actions_layout.count():
            item = self.actions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Добавить действия
        for action in self.row.actions:
            action_widget = ActionChip(action, self.backend, self.row)
            action_widget.selected.connect(self.action_selected.emit)
            action_widget.modified.connect(self.row_modified.emit)
            action_widget.delete_requested.connect(self._delete_action)
            self.actions_layout.addWidget(action_widget)

        self.actions_layout.addStretch()
    
    def _show_add_action_menu(self):
        """Показать меню добавления действия"""
        menu = QMenu(self)

        actions = [
            ("🖱 Клик", ActionType.MOUSE_CLICK),
            ("➡ Перемещение", ActionType.MOUSE_MOVE),
            ("⌨ Клавиша", ActionType.KEY_PRESS),
            ("⏱ Ожидание времени", ActionType.WAIT_TIME),
            ("🎨 Ожидание цвета", ActionType.WAIT_PIXEL_COLOR),
            ("🔄 Ожидание изменения", ActionType.WAIT_PIXEL_CHANGE),
            ("🖼 Ожидание изображения", ActionType.WAIT_IMAGE),
            ("📝 Текст (OCR)", ActionType.WAIT_TEXT),
            ("❓ Условие", ActionType.CONDITIONAL),
            ("🔁 Цикл", ActionType.LOOP),
            ("📸 Скриншот", ActionType.SCREENSHOT),
            ("📋 Лог", ActionType.LOG),
            # Действия с базами данных
            ("🔍 Поиск в БД", ActionType.DB_SEARCH),
            ("📥 Получить из БД", ActionType.DB_GET_VALUE),
            ("🔁 Пройти по БД", ActionType.DB_ITERATE),
            ("💾 Сохранить в БД", ActionType.DB_SAVE),
            ("✅ Проверка значения", ActionType.CHECK_VALUE),
            # Управление
            ("▶ Запустить строку", ActionType.RUN_ROW),
        ]

        for text, action_type in actions:
            action = menu.addAction(text)
            action.triggered.connect(lambda checked, at=action_type: self._add_action(at))

        # Показать меню под кнопкой "+ Действие"
        # Используем фиксированную позицию вместо sender()
        menu.exec(self.mapToGlobal(self.pos()))
    
    def _add_action(self, action_type: ActionType):
        """Добавить действие"""
        action = Action(
            id=str(uuid.uuid4()),
            action_type=action_type,
            name=self._get_action_name(action_type),
            enabled=True,
        )

        # Если требуется координата - получить текущую позицию мыши
        if action_type in [ActionType.MOUSE_CLICK, ActionType.MOUSE_MOVE,
                           ActionType.WAIT_PIXEL_COLOR, ActionType.WAIT_PIXEL_CHANGE]:
            action.coordinates = self.backend.mouse.get_position()

        # Добавляем действие напрямую в строку
        self.row.add_action(action)
        self._refresh_actions()
        self.row_modified.emit()
    
    def _get_action_name(self, action_type: ActionType) -> str:
        """Получить имя действия по типу"""
        names = {
            ActionType.MOUSE_CLICK: "Клик мышью",
            ActionType.MOUSE_MOVE: "Перемещение",
            ActionType.KEY_PRESS: "Нажатие клавиши",
            ActionType.WAIT_TIME: "Ожидание",
            ActionType.WAIT_PIXEL_COLOR: "Ожидание цвета",
            ActionType.WAIT_PIXEL_CHANGE: "Ожидание изменения",
            ActionType.WAIT_IMAGE: "Ожидание изображения",
            ActionType.WAIT_TEXT: "Ожидание текста",
            ActionType.CONDITIONAL: "Условие",
            ActionType.LOOP: "Цикл",
            ActionType.SCREENSHOT: "Скриншот",
            ActionType.LOG: "Лог",
            ActionType.DB_SEARCH: "Поиск в БД",
            ActionType.DB_GET_VALUE: "Получить из БД",
            ActionType.DB_ITERATE: "Пройти по БД",
            ActionType.DB_SAVE: "Сохранить в БД",
            ActionType.CHECK_VALUE: "Проверка значения",
            ActionType.RUN_ROW: "Запустить строку",
        }
        return names.get(action_type, "Действие")
    
    def _delete_action(self, action_id: str):
        """Удалить действие"""
        self.row.remove_action(action_id)
        self._refresh_actions()
        self.row_modified.emit()
    
    def _on_enabled_changed(self, state):
        """Изменение enabled"""
        self.row.enabled = state == Qt.CheckState.Checked
        self._update_style()
        self.row_modified.emit()

    def _on_row_click(self):
        """Клик по строке - выбрать строку"""
        self.row_selected.emit(self.row)

    def _on_delete(self):
        """Удалить строку"""
        self.delete_requested.emit(self.row.id)

    def _action_widgets(self):
        widgets = []
        for i in range(self.actions_layout.count()):
            item = self.actions_layout.itemAt(i)
            widget = item.widget() if item else None
            if isinstance(widget, ActionChip):
                widgets.append(widget)
        return widgets

    def _drop_index_for_pos(self, pos: QPoint) -> int:
        widgets = self._action_widgets()
        for idx, widget in enumerate(widgets):
            if pos.y() < widget.geometry().center().y():
                return idx
        return len(widgets)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-ahk-action-id"):
            event.acceptProposedAction()
            return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-ahk-action-id"):
            self._drag_hover_index = self._drop_index_for_pos(event.position().toPoint())
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event):
        mime = event.mimeData()
        if not mime.hasFormat("application/x-ahk-action-id"):
            event.ignore()
            return

        action_id = bytes(mime.data("application/x-ahk-action-id")).decode("utf-8", errors="ignore")
        source_row_id = bytes(mime.data("application/x-ahk-source-row")).decode("utf-8", errors="ignore")
        if not action_id or source_row_id != self.row.id:
            event.ignore()
            return

        try:
            current_index = next((i for i, a in enumerate(self.row.actions) if a.id == action_id), -1)
            if current_index < 0:
                event.ignore()
                return

            target_index = self._drop_index_for_pos(event.position().toPoint())
            if current_index < target_index:
                target_index -= 1
            target_index = max(0, min(target_index, len(self.row.actions) - 1))

            if current_index == target_index:
                event.acceptProposedAction()
                return

            action = self.row.actions.pop(current_index)
            self.row.actions.insert(target_index, action)
            self._refresh_actions()
            self.row_modified.emit()
            self.action_selected.emit(action)
            event.acceptProposedAction()
        except Exception:
            logger.exception("Ошибка drag-and-drop reorder")
            event.ignore()


class ActionChip(QFrame):
    """Виджет действия в виде 'чипа'"""

    selected = pyqtSignal(object)  # Action
    modified = pyqtSignal()
    delete_requested = pyqtSignal(str)  # action_id

    def __init__(self, action: Action, backend: BackendApplication, row=None):
        super().__init__()
        self.action = action
        self.backend = backend
        self.row = row  # Сохраняем ссылку на строку
        self._drag_start_pos = QPoint()

        self._init_ui()
        self._update_style()

    def _init_ui(self):
        """Инициализация UI"""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(5)

        # Иконка типа
        icon_label = QLabel(self._get_action_icon())
        layout.addWidget(icon_label)
        icon_label.installEventFilter(self)

        # Название и информация
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        # Название
        name_label = QLabel(self.action.name)
        name_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        info_layout.addWidget(name_label)
        name_label.installEventFilter(self)

        # Доп информация (координаты или клавиша)
        if self.action.coordinates:
            coord_label = QLabel(f"({self.action.coordinates.x}, {self.action.coordinates.y})")
            coord_label.setStyleSheet("color: #888; font-size: 10px;")
            info_layout.addWidget(coord_label)
            coord_label.installEventFilter(self)
        elif self.action.key:
            key_label = QLabel(f"⌨ {self.action.key}")
            key_label.setStyleSheet("color: #888; font-size: 10px;")
            info_layout.addWidget(key_label)
            key_label.installEventFilter(self)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Кнопка удаления
        delete_btn = QPushButton("×")
        delete_btn.setMaximumWidth(20)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
                color: white;
                border-radius: 3px;
            }
        """)
        delete_btn.clicked.connect(self._on_delete)
        layout.addWidget(delete_btn)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setMaximumHeight(50)
        
        # Контекстное меню для перемещения
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        """Показать контекстное меню для перемещения"""
        menu = QMenu(self)
        
        # Пункты для перемещения вверх/вниз
        move_up = menu.addAction("⬆ Переместить выше")
        move_up.triggered.connect(self._move_up)
        move_up.setEnabled(self._can_move_up())
        
        move_down = menu.addAction("⬇ Переместить ниже")
        move_down.triggered.connect(self._move_down)
        move_down.setEnabled(self._can_move_down())
        
        # Разделитель
        menu.addSeparator()
        
        # Копировать/Удалить
        copy_action = menu.addAction("📋 Копировать")
        copy_action.triggered.connect(self._copy_action)
        
        delete_action = menu.addAction("🗑 Удалить")
        delete_action.triggered.connect(self._on_delete)
        
        menu.exec(self.mapToGlobal(pos))

    def _can_move_up(self) -> bool:
        """Можно ли переместить выше"""
        if not self.row:
            return False
        idx = self.row.actions.index(self.action) if self.action in self.row.actions else -1
        return idx > 0

    def _can_move_down(self) -> bool:
        """Можно ли переместить ниже"""
        if not self.row:
            return False
        idx = self.row.actions.index(self.action) if self.action in self.row.actions else -1
        return idx >= 0 and idx < len(self.row.actions) - 1

    def _move_up(self):
        """Переместить действие выше"""
        try:
            if self.row and self.action in self.row.actions:
                actions = self.row.actions
                idx = actions.index(self.action)
                if idx > 0:
                    # Поменять местами с предыдущим
                    actions[idx], actions[idx - 1] = actions[idx - 1], actions[idx]
                    self.modified.emit()
        except Exception as e:
            logger.exception("Ошибка перемещения действия вверх")

    def _move_down(self):
        """Переместить действие ниже"""
        try:
            if self.row and self.action in self.row.actions:
                actions = self.row.actions
                idx = actions.index(self.action)
                if idx >= 0 and idx < len(actions) - 1:
                    # Поменять местами со следующим
                    actions[idx], actions[idx + 1] = actions[idx + 1], actions[idx]
                    self.modified.emit()
        except Exception as e:
            logger.exception("Ошибка перемещения действия вниз")

    def _copy_action(self):
        """Копировать действие"""
        if not self.row:
            return
        try:
            copy_action = Action(
                id=str(uuid.uuid4()),
                action_type=self.action.action_type,
                name=f"{self.action.name} (copy)",
                enabled=self.action.enabled,
                delay_before_ms=self.action.delay_before_ms,
                delay_after_ms=self.action.delay_after_ms,
                repeat_count=self.action.repeat_count,
                coordinates=Coordinates(self.action.coordinates.x, self.action.coordinates.y) if self.action.coordinates else None,
                color=self.action.color,
                key=self.action.key,
                mouse_button=self.action.mouse_button,
                metadata=dict(self.action.metadata),
            )
            idx = self.row.actions.index(self.action) if self.action in self.row.actions else len(self.row.actions)
            self.row.actions.insert(idx + 1, copy_action)
            self.modified.emit()
        except Exception:
            logger.exception("Ошибка копирования действия")

    def _update_style(self):
        """Обновить стиль"""
        if self.action.enabled:
            self.setStyleSheet("""
                ActionChip {
                    background-color: #3c3f41;
                    border: 1px solid #5c6265;
                    border-radius: 3px;
                }
                ActionChip:hover {
                    background-color: #4c5052;
                }
            """)
        else:
            self.setStyleSheet("""
                ActionChip {
                    background-color: #2b2b2b;
                    border: 1px dashed #5c6265;
                    border-radius: 3px;
                }
            """)
    
    def _get_action_icon(self) -> str:
        """Получить иконку действия"""
        icons = {
            ActionType.MOUSE_CLICK: "🖱",
            ActionType.MOUSE_MOVE: "➡",
            ActionType.KEY_PRESS: "⌨",
            ActionType.WAIT_TIME: "⏱",
            ActionType.WAIT_PIXEL_COLOR: "🎨",
            ActionType.WAIT_PIXEL_CHANGE: "🔄",
            ActionType.WAIT_IMAGE: "🖼",
            ActionType.WAIT_TEXT: "📝",
            ActionType.CONDITIONAL: "❓",
            ActionType.LOOP: "🔁",
            ActionType.SCREENSHOT: "📸",
            ActionType.LOG: "📋",
            # Действия с базами данных
            ActionType.DB_SEARCH: "🔍",
            ActionType.DB_GET_VALUE: "📥",
            ActionType.DB_ITERATE: "🔁",
            ActionType.DB_SAVE: "💾",
            ActionType.CHECK_VALUE: "✅",
            # Управление
            ActionType.RUN_ROW: "▶",
        }
        return icons.get(self.action.action_type, "•")
    
    def mousePressEvent(self, event):
        """Обработка клика"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self.selected.emit(self.action)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(event)
            return

        if (event.pos() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        if not self.row or not self.action.id:
            super().mouseMoveEvent(event)
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData("application/x-ahk-action-id", self.action.id.encode("utf-8"))
        mime.setData("application/x-ahk-source-row", self.row.id.encode("utf-8"))
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.MoveAction)

    def eventFilter(self, obj, event):
        """Клик по дочерним виджетам также выбирает действие."""
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.action)
            return True
        return super().eventFilter(obj, event)
    
    def _on_delete(self):
        """Удалить действие"""
        self.delete_requested.emit(self.action.id)
