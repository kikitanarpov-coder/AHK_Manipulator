"""
Правая панель - контекстно меняющаяся панель действий и свойств
"""
import logging
import uuid

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QComboBox, QCheckBox,
    QGroupBox, QFormLayout, QLineEdit,
    QFrame, QScrollArea, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut

from backend import BackendApplication, Action, ActionType, Coordinates, TaskRow
from ui.key_recorder_dialog import KeyRecorderDialog
from ui.action_property_panels import get_panel

logger = logging.getLogger(__name__)


class RightPanel(QWidget):
    """Контекстная правая панель"""

    action_added = pyqtSignal(object)  # Action
    action_modified = pyqtSignal(object)  # Action
    coordinates_captured = pyqtSignal(int, int)  # x, y
    row_modified = pyqtSignal(object)  # TaskRow

    def __init__(self, backend: BackendApplication):
        super().__init__()
        self.backend = backend
        self.current_action = None
        self.current_row = None

        self._init_ui()
        self._setup_shortcuts()
    
    def _init_ui(self):
        """Инициализация UI"""
        self.setWindowTitle("Панель")
        self.setMinimumWidth(280)
        self.setMaximumWidth(400)

        # Динамическая панель для текущего действия
        self.current_action_panel = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Stack widget для переключения между режимами
        self.stack = QStackedWidget()

        # Страница добавления действия
        self.add_action_widget = self._create_add_action_widget()
        self.stack.addWidget(self.add_action_widget)

        # Страница свойств действия (динамическая)
        self.properties_widget = self._create_properties_widget()
        self.stack.addWidget(self.properties_widget)

        # Страница свойств строки
        self.row_properties_widget = self._create_row_properties_widget()
        self.stack.addWidget(self.row_properties_widget)

        # Страница "нет выбора"
        self.empty_widget = self._create_empty_widget()
        self.stack.addWidget(self.empty_widget)

        layout.addWidget(self.stack)

        # По умолчанию показываем добавление действия
        self._show_add_action()
    
    def _setup_shortcuts(self):
        """Настройка горячих клавиш"""
        # Cmd+Shift+R (macOS) или Ctrl+Shift+R (Windows/Linux)
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+R"), self)
        shortcut.activated.connect(self._capture_coordinates)
    
    def _create_add_action_widget(self) -> QWidget:
        """Создать виджет добавления действия"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Заголовок
        title = QLabel("Добавить действие")
        title.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold;
        """)
        layout.addWidget(title)

        # Горячие клавиши подсказка
        self.add_shortcut_label = QLabel("Cmd+Shift+R — захват координат")
        self.add_shortcut_label.setStyleSheet("""
            color: #999999;
            font-size: 11px;
            padding: 4px;
        """)
        layout.addWidget(self.add_shortcut_label)

        # Разделитель
        layout.addWidget(self._create_separator())

        # Тип действия
        type_group = QGroupBox("Тип действия")
        type_layout = QFormLayout()

        self.action_type_combo = QComboBox()
        self._populate_action_types()
        self.action_type_combo.currentIndexChanged.connect(self._update_add_action_type_panel)
        type_layout.addRow("Тип:", self.action_type_combo)

        self.action_name_input = QLineEdit()
        self.action_name_input.setPlaceholderText("Название действия")
        type_layout.addRow("Название:", self.action_name_input)

        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Координаты
        coord_group = QGroupBox("Координаты")
        coord_layout = QFormLayout()

        self.x_spin = QSpinBox()
        self.x_spin.setRange(-32768, 32767)
        self.x_spin.setValue(0)

        self.y_spin = QSpinBox()
        self.y_spin.setRange(-32768, 32767)
        self.y_spin.setValue(0)

        self.capture_btn = QPushButton("Захватить")
        self.capture_btn.setToolTip("Cmd+Shift+R для захвата координат")
        self.capture_btn.setMinimumHeight(26)
        self.capture_btn.clicked.connect(self._capture_coordinates)

        coord_layout.addRow("X:", self.x_spin)
        coord_layout.addRow("Y:", self.y_spin)
        coord_layout.addRow(self.capture_btn)

        coord_group.setLayout(coord_layout)
        layout.addWidget(coord_group)
        
        # Параметры мыши
        mouse_group = QGroupBox("Параметры мыши")
        mouse_layout = QFormLayout()

        self.mouse_button_combo = QComboBox()
        self.mouse_button_combo.addItems(["left", "right", "middle"])
        mouse_layout.addRow("Кнопка:", self.mouse_button_combo)

        mouse_group.setLayout(mouse_layout)
        layout.addWidget(mouse_group)

        # Параметры клавиатуры
        keyboard_group = QGroupBox("Параметры клавиатуры")
        keyboard_layout = QFormLayout()

        keyboard_input_layout = QHBoxLayout()

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Нажмите кнопку записи")
        self.key_input.setReadOnly(False)

        # Кнопка очистки
        self.key_clear_btn = QPushButton("✕")
        self.key_clear_btn.setMaximumWidth(28)
        self.key_clear_btn.setToolTip("Очистить поле")
        self.key_clear_btn.clicked.connect(self._clear_key_input)

        self.key_record_btn = QPushButton("Записать")
        self.key_record_btn.clicked.connect(self._open_key_recorder)

        keyboard_input_layout.addWidget(self.key_input)
        keyboard_input_layout.addWidget(self.key_clear_btn)
        keyboard_input_layout.addWidget(self.key_record_btn)

        keyboard_layout.addRow("Клавиша:", keyboard_input_layout)

        keyboard_group.setLayout(keyboard_layout)
        layout.addWidget(keyboard_group)
        
        # Задержки
        delay_group = QGroupBox("Задержки (мс)")
        delay_layout = QFormLayout()

        self.delay_before_spin = QSpinBox()
        self.delay_before_spin.setRange(0, 60000)
        self.delay_before_spin.setValue(0)

        self.delay_after_spin = QSpinBox()
        self.delay_after_spin.setRange(0, 60000)
        self.delay_after_spin.setValue(0)

        delay_layout.addRow("Перед действием:", self.delay_before_spin)
        delay_layout.addRow("После действия:", self.delay_after_spin)

        delay_group.setLayout(delay_layout)
        layout.addWidget(delay_group)

        # Повторы
        repeat_group = QGroupBox("Повторы")
        repeat_layout = QFormLayout()

        self.repeat_spin = QSpinBox()
        self.repeat_spin.setRange(1, 1000)
        self.repeat_spin.setValue(1)
        repeat_layout.addRow("Количество:", self.repeat_spin)

        repeat_group.setLayout(repeat_layout)
        layout.addWidget(repeat_group)

        # Динамические свойства выбранного типа действия (в отдельном scroll)
        dynamic_group = QGroupBox("Дополнительные параметры")
        dynamic_group_layout = QVBoxLayout(dynamic_group)
        dynamic_group_layout.setContentsMargins(6, 6, 6, 6)
        dynamic_group_layout.setSpacing(4)

        self.add_dynamic_scroll = QScrollArea()
        self.add_dynamic_scroll.setWidgetResizable(True)
        self.add_dynamic_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.add_dynamic_scroll.setMinimumHeight(160)
        self.add_dynamic_scroll.setMaximumHeight(320)

        self.add_action_panel = None
        self.add_dynamic_container = QWidget()
        self.add_dynamic_layout = QVBoxLayout(self.add_dynamic_container)
        self.add_dynamic_layout.setContentsMargins(0, 0, 0, 0)
        self.add_dynamic_layout.setSpacing(6)
        self.add_dynamic_scroll.setWidget(self.add_dynamic_container)
        dynamic_group_layout.addWidget(self.add_dynamic_scroll)
        layout.addWidget(dynamic_group)

        layout.addStretch()

        # Кнопка добавления
        self.add_action_btn = QPushButton("Добавить действие")
        self.add_action_btn.setMinimumHeight(32)
        self.add_action_btn.clicked.connect(self._add_action)
        layout.addWidget(self.add_action_btn)

        self._update_add_action_type_panel()

        return widget

    def _update_add_action_type_panel(self):
        """Обновить динамический блок свойств для add-mode."""
        if not hasattr(self, "add_dynamic_layout"):
            return

        while self.add_dynamic_layout.count():
            item = self.add_dynamic_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        action_type = self.action_type_combo.currentData()
        self.add_action_panel = get_panel(action_type)
        if self.add_action_panel:
            try:
                panel_widget = self.add_action_panel.create_panel(self)
                self.add_dynamic_layout.addWidget(panel_widget)
            except Exception:
                logger.exception("Ошибка создания панели свойств для типа %s", action_type)
                self.add_action_panel = None
    
    def _create_properties_widget(self) -> QWidget:
        """Создать виджет свойств действия (динамический)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Заголовок
        self.prop_title = QLabel("⚙ Свойства действия")
        self.prop_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e67e22;")
        layout.addWidget(self.prop_title)
        
        # Горячие клавиши подсказка
        self.prop_shortcut_label = QLabel("Cmd+Shift+R — захват координат")
        self.prop_shortcut_label.setStyleSheet("""
            color: #999999;
            font-size: 11px;
            padding: 4px;
        """)
        layout.addWidget(self.prop_shortcut_label)
        layout.addWidget(self._create_separator())
        
        # Scroll area для динамического контента
        self.prop_scroll = QScrollArea()
        self.prop_scroll.setWidgetResizable(True)
        self.prop_scroll.setMinimumHeight(260)
        
        self.prop_content = QWidget()
        self.prop_content_layout = QVBoxLayout(self.prop_content)
        self.prop_content_layout.setSpacing(10)
        
        self.prop_scroll.setWidget(self.prop_content)
        layout.addWidget(self.prop_scroll)
        
        # Кнопка удаления
        delete_btn = QPushButton("🗑 Удалить действие")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
        """)
        delete_btn.clicked.connect(self._on_delete_action)
        layout.addWidget(delete_btn)
        
        return widget
    
    def _update_properties_panel(self):
        """Обновить панель свойств в соответствии с типом действия"""
        if not self.current_action:
            return
        
        # Проверка что layout существует
        if getattr(self, "prop_content_layout", None) is None:
            return

        # Сохранить текущие значения из панели перед обновлением
        if self.current_action_panel:
            try:
                self.current_action.metadata = self.current_action_panel.get_values()
            except Exception:
                pass

        # Очистить текущий контент
        while self.prop_content_layout.count():
            item = self.prop_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        action_type = self.current_action.action_type
        
        # Общие поля
        self.prop_name_input = QLineEdit(self.current_action.name)
        self.prop_name_input.textChanged.connect(self._on_name_changed)
        name_group = QGroupBox("Название")
        name_layout = QVBoxLayout()
        name_layout.addWidget(self.prop_name_input)
        name_group.setLayout(name_layout)
        self.prop_content_layout.addWidget(name_group)
        
        self.prop_enabled_cb = QCheckBox("Включено")
        self.prop_enabled_cb.setChecked(self.current_action.enabled)
        self.prop_enabled_cb.stateChanged.connect(self._on_enabled_changed)
        self.prop_content_layout.addWidget(self.prop_enabled_cb)
        
        # Поля для координат (для действий с координатами)
        if action_type in [ActionType.MOUSE_CLICK, ActionType.MOUSE_MOVE, 
                           ActionType.WAIT_PIXEL_COLOR, ActionType.WAIT_PIXEL_CHANGE]:
            coord_group = QGroupBox("📍 Координаты")
            coord_layout = QFormLayout()
            
            self.prop_x_spin = QSpinBox()
            self.prop_x_spin.setRange(-32768, 32767)
            
            self.prop_y_spin = QSpinBox()
            self.prop_y_spin.setRange(-32768, 32767)
            
            if self.current_action.coordinates:
                self.prop_x_spin.setValue(self.current_action.coordinates.x)
                self.prop_y_spin.setValue(self.current_action.coordinates.y)

            # Подключаем сигналы только после установки стартовых значений,
            # чтобы не затирать координаты при построении панели.
            self.prop_x_spin.valueChanged.connect(self._on_coordinates_changed)
            self.prop_y_spin.valueChanged.connect(self._on_coordinates_changed)
            
            self.prop_capture_btn = QPushButton("📍 Захватить")
            self.prop_capture_btn.setToolTip("Cmd+Shift+R для захвата координат")
            self.prop_capture_btn.setMinimumHeight(32)
            self.prop_capture_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            self.prop_capture_btn.clicked.connect(self._capture_coordinates)
            
            coord_layout.addRow("X:", self.prop_x_spin)
            coord_layout.addRow("Y:", self.prop_y_spin)
            coord_layout.addRow(self.prop_capture_btn)
            coord_group.setLayout(coord_layout)
            self.prop_content_layout.addWidget(coord_group)
        
        # Поле для клавиши (для KEY_PRESS)
        if action_type == ActionType.KEY_PRESS:
            key_group = QGroupBox("⌨ Клавиша")
            key_layout = QFormLayout()
            
            key_input_layout = QHBoxLayout()
            self.prop_key_input = QLineEdit()
            self.prop_key_input.setPlaceholderText("Введите или запишите клавишу")
            self.prop_key_input.setReadOnly(False)
            self.prop_key_input.textChanged.connect(self._on_key_changed)
            
            if self.current_action.key:
                self.prop_key_input.setText(self.current_action.key)
            
            self.prop_key_clear_btn = QPushButton("✕")
            self.prop_key_clear_btn.setMaximumWidth(30)
            self.prop_key_clear_btn.setToolTip("Очистить")
            self.prop_key_clear_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            self.prop_key_clear_btn.clicked.connect(self._clear_key_input)
            
            self.prop_key_record_btn = QPushButton("⌨ Записать")
            self.prop_key_record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9b59b6;
                    color: white;
                    padding: 8px 15px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #8e44ad;
                }
            """)
            self.prop_key_record_btn.clicked.connect(self._open_key_recorder)
            
            key_input_layout.addWidget(self.prop_key_input)
            key_input_layout.addWidget(self.prop_key_clear_btn)
            key_input_layout.addWidget(self.prop_key_record_btn)
            key_layout.addRow("Клавиша:", key_input_layout)
            key_group.setLayout(key_layout)
            self.prop_content_layout.addWidget(key_group)
        
        # Динамическая панель для типа действия
        self.current_action_panel = get_panel(action_type)
        if self.current_action_panel:
            try:
                panel_widget = self.current_action_panel.create_panel(self)
                self.prop_content_layout.addWidget(panel_widget)
                
                # Загрузить сохранённые значения
                if self.current_action.metadata:
                    self.current_action_panel.set_values(self.current_action.metadata)
            except Exception:
                logger.exception("Ошибка создания панели свойств для %s", action_type)
                self.current_action_panel = None
        else:
            fallback_group = QGroupBox("Параметры")
            fallback_layout = QVBoxLayout()
            fallback_label = QLabel("Для этого действия дополнительные параметры отсутствуют.")
            fallback_label.setWordWrap(True)
            fallback_layout.addWidget(fallback_label)
            fallback_group.setLayout(fallback_layout)
            self.prop_content_layout.addWidget(fallback_group)
        
        # Задержки
        delay_group = QGroupBox("⏱ Задержки (мс)")
        delay_layout = QFormLayout()
        
        self.prop_delay_before_spin = QSpinBox()
        self.prop_delay_before_spin.setRange(0, 60000)
        self.prop_delay_before_spin.setValue(self.current_action.delay_before_ms)
        self.prop_delay_before_spin.valueChanged.connect(self._on_delay_before_changed)
        
        self.prop_delay_after_spin = QSpinBox()
        self.prop_delay_after_spin.setRange(0, 60000)
        self.prop_delay_after_spin.setValue(self.current_action.delay_after_ms)
        self.prop_delay_after_spin.valueChanged.connect(self._on_delay_after_changed)
        
        delay_layout.addRow("Перед действием:", self.prop_delay_before_spin)
        delay_layout.addRow("После действия:", self.prop_delay_after_spin)
        delay_group.setLayout(delay_layout)
        self.prop_content_layout.addWidget(delay_group)
        
        # Повторы
        repeat_group = QGroupBox("🔁 Повторы")
        repeat_layout = QFormLayout()
        
        self.prop_repeat_spin = QSpinBox()
        self.prop_repeat_spin.setRange(1, 1000)
        self.prop_repeat_spin.setValue(self.current_action.repeat_count)
        self.prop_repeat_spin.valueChanged.connect(self._on_repeat_changed)
        
        repeat_layout.addRow("Количество:", self.prop_repeat_spin)
        repeat_group.setLayout(repeat_layout)
        self.prop_content_layout.addWidget(repeat_group)

        self.prop_content_layout.addStretch()

    def _create_row_properties_widget(self) -> QWidget:
        """Создать виджет свойств строки"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Заголовок
        title = QLabel("📋 Свойства строки")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #9b59b6;")
        layout.addWidget(title)
        
        # Разделитель
        layout.addWidget(self._create_separator())
        
        # Название строки
        self.row_name_input = QLineEdit()
        self.row_name_input.textChanged.connect(self._on_row_name_changed)
        name_group = QGroupBox("Название строки")
        name_layout = QVBoxLayout()
        name_layout.addWidget(self.row_name_input)
        name_group.setLayout(name_layout)
        layout.addWidget(name_group)
        
        # Enabled
        self.row_enabled_cb = QCheckBox("Включена")
        self.row_enabled_cb.stateChanged.connect(self._on_row_enabled_changed)
        layout.addWidget(self.row_enabled_cb)
        
        layout.addStretch()
        
        # Кнопка удаления строки
        delete_row_btn = QPushButton("🗑 Удалить строку")
        delete_row_btn.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
        """)
        delete_row_btn.clicked.connect(self._on_delete_row)
        layout.addWidget(delete_row_btn)
        
        return widget
    
    def _create_empty_widget(self) -> QWidget:
        """Создать пустой виджет"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        empty_label = QLabel("Выберите действие\nили строку для редактирования\n\nИли добавьте новое действие")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(empty_label)
        
        # Кнопка добавления действия
        add_btn = QPushButton("➕ Добавить действие")
        add_btn.clicked.connect(lambda: self._show_add_action())
        layout.addWidget(add_btn)
        
        layout.addStretch()
        
        return widget
    
    def _create_separator(self) -> QFrame:
        """Создать разделитель"""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #444;")
        line.setMaximumHeight(1)
        return line
    
    def _populate_action_types(self):
        """Заполнить комбобокс типами действий"""
        types = [
            (ActionType.MOUSE_CLICK, "🖱 Клик мышью"),
            (ActionType.MOUSE_MOVE, "➡ Перемещение мыши"),
            (ActionType.KEY_PRESS, "⌨ Нажатие клавиши"),
            (ActionType.WAIT_TIME, "⏱ Ожидание времени"),
            (ActionType.WAIT_PIXEL_COLOR, "🎨 Ожидание цвета пикселя"),
            (ActionType.WAIT_PIXEL_CHANGE, "🔄 Ожидание изменения"),
            (ActionType.WAIT_IMAGE, "🖼 Ожидание изображения"),
            (ActionType.WAIT_TEXT, "📝 Ожидание текста (OCR)"),
            (ActionType.CONDITIONAL, "❓ Условное действие"),
            (ActionType.LOOP, "🔁 Цикл"),
            (ActionType.SCREENSHOT, "📸 Скриншот"),
            (ActionType.LOG, "📋 Логирование"),
            # Действия с базами данных
            (ActionType.DB_SEARCH, "🔍 Поиск в БД"),
            (ActionType.DB_GET_VALUE, "📥 Получить из БД"),
            (ActionType.DB_ITERATE, "🔁 Пройти по БД"),
            (ActionType.DB_SAVE, "💾 Сохранить в БД"),
            (ActionType.CHECK_VALUE, "✅ Проверка значения"),
            # Управление
            (ActionType.RUN_ROW, "▶ Запустить строку"),
        ]

        for action_type, display_name in types:
            self.action_type_combo.addItem(display_name, action_type)
    
    def _capture_coordinates(self):
        """Захватить текущие координаты"""
        try:
            pos = self.backend.mouse.get_position()
            
            # Обновить координаты в зависимости от режима
            if hasattr(self, 'current_action') and self.current_action:
                # Режим свойств действия
                if self.current_action.coordinates:
                    self.current_action.coordinates.x = pos.x
                    self.current_action.coordinates.y = pos.y
                if hasattr(self, 'prop_x_spin'):
                    self.prop_x_spin.setValue(pos.x)
                if hasattr(self, 'prop_y_spin'):
                    self.prop_y_spin.setValue(pos.y)
            elif hasattr(self, 'x_spin'):
                # Режим добавления действия
                self.x_spin.setValue(pos.x)
                self.y_spin.setValue(pos.y)
            
            self.coordinates_captured.emit(pos.x, pos.y)
        except Exception as e:
            logger.exception("Ошибка захвата координат в RightPanel")

    def _open_key_recorder(self):
        """Открыть диалог записи клавиш"""
        dialog = KeyRecorderDialog(self)
        dialog.keys_recorded.connect(self._on_keys_recorded)
        dialog.exec()

    def _on_keys_recorded(self, keys_str: str):
        """Обработать записанные клавиши"""
        self.key_input.setText(keys_str)
        if hasattr(self, "prop_key_input"):
            self.prop_key_input.setText(keys_str)

    def _clear_key_input(self):
        """Очистить поле ввода клавиши"""
        self.key_input.clear()
        if hasattr(self, "prop_key_input"):
            self.prop_key_input.clear()
        if self.current_action:
            self.current_action.key = None
            self.action_modified.emit(self.current_action)
    
    def _add_action(self):
        """Добавить действие"""
        # Получить тип действия
        action_type = self.action_type_combo.currentData()

        # Создать действие
        action = Action(
            id=str(uuid.uuid4()),
            action_type=action_type,
            name=self.action_name_input.text() or self._get_default_name(action_type),
            enabled=True,
            coordinates=Coordinates(self.x_spin.value(), self.y_spin.value()),
            mouse_button=self.mouse_button_combo.currentText(),
            key=self.key_input.text() or None,
            delay_before_ms=self.delay_before_spin.value(),
            delay_after_ms=self.delay_after_spin.value(),
            repeat_count=self.repeat_spin.value(),
        )

        if self.add_action_panel:
            try:
                action.metadata.update(self.add_action_panel.get_values())
            except Exception:
                logger.exception("Ошибка чтения параметров add-панели")

        # Добавить в текущую строку (или создать новую)
        if not self.backend.current_board or not self.backend.current_board.rows:
            self.backend.add_row("Новая строка")

        # Добавить в последнюю строку
        row = self.backend.current_board.rows[-1]
        self.backend.add_action(row.id, action)

        self.action_added.emit(action)

        # Очистить форму
        self.action_name_input.clear()
    
    def _get_default_name(self, action_type: ActionType) -> str:
        """Получить имя по умолчанию"""
        names = {
            ActionType.MOUSE_CLICK: "Клик",
            ActionType.MOUSE_MOVE: "Перемещение",
            ActionType.KEY_PRESS: "Нажатие",
            ActionType.WAIT_TIME: "Ожидание",
            ActionType.WAIT_PIXEL_COLOR: "Ожидание цвета",
            ActionType.WAIT_PIXEL_CHANGE: "Ожидание изменения",
            ActionType.WAIT_IMAGE: "Ожидание изображения",
            ActionType.WAIT_TEXT: "Ожидание текста",
            ActionType.CONDITIONAL: "Условие",
            ActionType.LOOP: "Цикл",
            ActionType.SCREENSHOT: "Скриншот",
            ActionType.LOG: "Лог",
        }
        return names.get(action_type, "Действие")
    
    # ===== Переключение режимов =====
    
    def _show_add_action(self):
        """Показать режим добавления действия"""
        self.stack.setCurrentIndex(0)
    
    def _show_properties(self):
        """Показать режим свойств"""
        self.stack.setCurrentIndex(1)
    
    def _show_row_properties(self):
        """Показать режим свойств строки"""
        self.stack.setCurrentIndex(2)
    
    def _show_empty(self):
        """Показать пустой режим"""
        self.stack.setCurrentIndex(3)
    
    # ===== Публичные методы =====
    
    def set_action(self, action: Action):
        """Установить текущее действие для редактирования"""
        self.current_row = None
        self.current_action = action

        if not action:
            self._show_add_action()
            return

        # Принудительно создаём виджет свойств если нужно
        if getattr(self, "prop_content_layout", None) is None:
            # Пересоздаём виджет свойств
            old_widget = self.stack.widget(1)
            if old_widget:
                self.stack.removeWidget(old_widget)
                old_widget.deleteLater()
            
            new_widget = self._create_properties_widget()
            self.stack.insertWidget(1, new_widget)
            self.properties_widget = new_widget

        # Переключиться на страницу свойств
        self._show_properties()

        # Обновить заголовок
        if hasattr(self, 'prop_title'):
            self.prop_title.setText(f"⚙ Свойства: {action.name}")

        # Обновить панель свойств
        self._update_properties_panel()
    
    def set_row(self, row: TaskRow):
        """Установить текущую строку для редактирования"""
        self.current_action = None
        self.current_row = row
        
        if not row:
            self._show_add_action()
            return
        
        self.row_name_input.setText(row.name)
        self.row_enabled_cb.setChecked(row.enabled)
        
        self._show_row_properties()
    
    def reset(self):
        """Сбросить выбор"""
        self.current_action = None
        self.current_row = None
        self._show_add_action()
    
    # ===== Обработчики изменений свойств =====
    
    def _on_name_changed(self, text: str):
        if self.current_action:
            self.current_action.name = text
            self.prop_title.setText(f"⚙ Свойства: {text}")
            self.action_modified.emit(self.current_action)
    
    def _on_enabled_changed(self, state):
        if self.current_action:
            self.current_action.enabled = state == Qt.CheckState.Checked
            self.action_modified.emit(self.current_action)
    
    def _on_coordinates_changed(self):
        if self.current_action and self.current_action.coordinates:
            self.current_action.coordinates.x = self.prop_x_spin.value()
            self.current_action.coordinates.y = self.prop_y_spin.value()
            self.action_modified.emit(self.current_action)
    
    def _on_mouse_button_changed(self, text: str):
        if self.current_action:
            self.current_action.mouse_button = text
            self.action_modified.emit(self.current_action)
    
    def _on_key_changed(self, text: str):
        if self.current_action:
            self.current_action.key = text
            self.action_modified.emit(self.current_action)
    
    def _on_delay_before_changed(self, value: int):
        if self.current_action:
            self.current_action.delay_before_ms = value
            self.action_modified.emit(self.current_action)
    
    def _on_delay_after_changed(self, value: int):
        if self.current_action:
            self.current_action.delay_after_ms = value
            self.action_modified.emit(self.current_action)
    
    def _on_repeat_changed(self, value: int):
        if self.current_action:
            self.current_action.repeat_count = value
            self.action_modified.emit(self.current_action)
    
    def _on_delete_action(self):
        """Удалить действие"""
        if self.current_action and self.backend.current_board:
            for row in self.backend.current_board.rows:
                if row.remove_action(self.current_action.id):
                    self.backend.current_board.modified_at = __import__('datetime').datetime.now()
                    self.action_modified.emit(self.current_action)
                    self.reset()
                    break
    
    def _on_row_name_changed(self, text: str):
        if self.current_row:
            self.current_row.name = text
            self.row_modified.emit(self.current_row)
    
    def _on_row_enabled_changed(self, state):
        if self.current_row:
            self.current_row.enabled = state == Qt.CheckState.Checked
            self.row_modified.emit(self.current_row)
    
    def _on_delete_row(self):
        """Удалить строку"""
        if self.current_row and self.backend.current_board:
            self.backend.current_board.remove_row(self.current_row.id)
            self.reset()
