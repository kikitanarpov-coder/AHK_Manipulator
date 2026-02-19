"""
Адаптивные панели свойств для каждого типа действий
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QComboBox, QCheckBox,
    QGroupBox, QFormLayout, QLineEdit, QDoubleSpinBox,
    QFileDialog, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt

from backend import ActionType


class BaseActionPanel:
    """Базовый класс панели свойств действия"""
    
    def __init__(self):
        self.widgets = {}
    
    def create_panel(self, parent_widget) -> QGroupBox:
        raise NotImplementedError
    
    def get_values(self) -> dict:
        raise NotImplementedError
    
    def set_values(self, values: dict):
        raise NotImplementedError


class MouseClickPanel(BaseActionPanel):
    """Панель для клика мышью"""
    
    def create_panel(self, parent_widget) -> QGroupBox:
        group = QGroupBox("🖱 Параметры клика")
        layout = QFormLayout()
        
        self.button_combo = QComboBox()
        self.button_combo.addItems(["left", "right", "middle", "x1", "x2"])
        layout.addRow("Кнопка:", self.button_combo)
        
        self.clicks_spin = QSpinBox()
        self.clicks_spin.setRange(1, 10)
        self.clicks_spin.setValue(1)
        layout.addRow("Количество кликов:", self.clicks_spin)
        
        group.setLayout(layout)
        return group
    
    def get_values(self) -> dict:
        return {
            "mouse_button": self.button_combo.currentText(),
            "click_count": self.clicks_spin.value(),
        }
    
    def set_values(self, values: dict):
        if "mouse_button" in values:
            self.button_combo.setCurrentText(values["mouse_button"])
        if "click_count" in values:
            self.clicks_spin.setValue(values["click_count"])


class MouseMovePanel(BaseActionPanel):
    """Панель для перемещения мыши"""
    
    def create_panel(self, parent_widget) -> QGroupBox:
        group = QGroupBox("➡ Параметры перемещения")
        layout = QFormLayout()
        
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 5000)
        self.duration_spin.setValue(100)
        layout.addRow("Время перемещения (мс):", self.duration_spin)
        
        group.setLayout(layout)
        return group
    
    def get_values(self) -> dict:
        return {"move_duration_ms": self.duration_spin.value()}
    
    def set_values(self, values: dict):
        if "move_duration_ms" in values:
            self.duration_spin.setValue(values["move_duration_ms"])


class KeyPressPanel(BaseActionPanel):
    """Панель для нажатия клавиши"""
    
    def create_panel(self, parent_widget) -> QGroupBox:
        group = QGroupBox("⌨ Параметры нажатия")
        layout = QFormLayout()
        
        self.press_count_spin = QSpinBox()
        self.press_count_spin.setRange(1, 100)
        self.press_count_spin.setValue(1)
        layout.addRow("Количество нажатий:", self.press_count_spin)
        
        self.press_duration_spin = QSpinBox()
        self.press_duration_spin.setRange(1, 1000)
        self.press_duration_spin.setValue(50)
        layout.addRow("Длительность (мс):", self.press_duration_spin)
        
        group.setLayout(layout)
        return group
    
    def get_values(self) -> dict:
        return {
            "press_count": self.press_count_spin.value(),
            "press_duration_ms": self.press_duration_spin.value(),
        }
    
    def set_values(self, values: dict):
        if "press_count" in values:
            self.press_count_spin.setValue(values["press_count"])
        if "press_duration_ms" in values:
            self.press_duration_spin.setValue(values["press_duration_ms"])


class WaitTimePanel(BaseActionPanel):
    """Панель для ожидания времени"""
    
    def create_panel(self, parent_widget) -> QGroupBox:
        group = QGroupBox("⏱ Параметры ожидания")
        layout = QFormLayout()
        
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 300000)
        self.duration_spin.setValue(1000)
        layout.addRow("Продолжительность (мс):", self.duration_spin)
        
        self.continue_on_complete = QCheckBox("Перейти к следующему действию после завершения")
        self.continue_on_complete.setChecked(True)
        layout.addRow("", self.continue_on_complete)
        
        group.setLayout(layout)
        return group
    
    def get_values(self) -> dict:
        return {
            "wait_ms": self.duration_spin.value(),
            "continue_on_complete": self.continue_on_complete.isChecked(),
        }
    
    def set_values(self, values: dict):
        if "wait_ms" in values:
            self.duration_spin.setValue(values["wait_ms"])
        if "continue_on_complete" in values:
            self.continue_on_complete.setChecked(values["continue_on_complete"])


class WaitPixelColorPanel(BaseActionPanel):
    """Панель для ожидания цвета пикселя"""
    
    def create_panel(self, parent_widget) -> QGroupBox:
        group = QGroupBox("🎨 Параметры цвета")
        layout = QFormLayout()
        
        # RGB цвет
        color_layout = QHBoxLayout()
        self.color_r = QSpinBox()
        self.color_r.setRange(0, 255)
        self.color_r.setValue(255)
        color_layout.addWidget(QLabel("R:"))
        color_layout.addWidget(self.color_r)
        
        self.color_g = QSpinBox()
        self.color_g.setRange(0, 255)
        self.color_g.setValue(0)
        color_layout.addWidget(QLabel("G:"))
        color_layout.addWidget(self.color_g)
        
        self.color_b = QSpinBox()
        self.color_b.setRange(0, 255)
        self.color_b.setValue(0)
        color_layout.addWidget(QLabel("B:"))
        color_layout.addWidget(self.color_b)
        
        layout.addRow("Ожидаемый цвет:", color_layout)

        # Чекбокс "любое изменение"
        self.any_change_check = QCheckBox("Любое изменение (не конкретный цвет)")
        self.any_change_check.setToolTip("Если отмечено, действие завершится при любом изменении пикселя")
        self.any_change_check.stateChanged.connect(self._on_any_change_changed)
        layout.addRow("", self.any_change_check)

        self.tolerance_spin = QSpinBox()
        self.tolerance_spin.setRange(0, 255)
        self.tolerance_spin.setValue(10)
        layout.addRow("Допуск:", self.tolerance_spin)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 60000)
        self.timeout_spin.setValue(5000)
        layout.addRow("Таймаут (мс):", self.timeout_spin)

        group.setLayout(layout)
        return group

    def _on_any_change_changed(self, state):
        """Включить/выключить поля цвета"""
        checked = state == Qt.CheckState.Checked
        self.color_r.setEnabled(not checked)
        self.color_g.setEnabled(not checked)
        self.color_b.setEnabled(not checked)
        self.tolerance_spin.setEnabled(not checked)

    def get_values(self) -> dict:
        return {
            "color_r": self.color_r.value(),
            "color_g": self.color_g.value(),
            "color_b": self.color_b.value(),
            "tolerance": self.tolerance_spin.value(),
            "timeout_ms": self.timeout_spin.value(),
            "any_change": self.any_change_check.isChecked(),
        }

    def set_values(self, values: dict):
        if "any_change" in values:
            self.any_change_check.setChecked(values["any_change"])
            # Обновить состояние полей
            checked = values["any_change"]
            self.color_r.setEnabled(not checked)
            self.color_g.setEnabled(not checked)
            self.color_b.setEnabled(not checked)
            self.tolerance_spin.setEnabled(not checked)
        
        if "color_r" in values:
            self.color_r.setValue(values["color_r"])
        if "color_g" in values:
            self.color_g.setValue(values["color_g"])
        if "color_b" in values:
            self.color_b.setValue(values["color_b"])
        if "tolerance" in values:
            self.tolerance_spin.setValue(values["tolerance"])
        if "timeout_ms" in values:
            self.timeout_spin.setValue(values["timeout_ms"])


class WaitPixelChangePanel(BaseActionPanel):
    """Панель для ожидания изменения пикселя"""
    
    def create_panel(self, parent_widget) -> QGroupBox:
        group = QGroupBox("🔄 Параметры изменения")
        layout = QFormLayout()
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 60000)
        self.timeout_spin.setValue(5000)
        layout.addRow("Таймаут (мс):", self.timeout_spin)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 1000)
        self.interval_spin.setValue(100)
        layout.addRow("Интервал проверки (мс):", self.interval_spin)
        
        group.setLayout(layout)
        return group
    
    def get_values(self) -> dict:
        return {
            "timeout_ms": self.timeout_spin.value(),
            "check_interval_ms": self.interval_spin.value(),
        }
    
    def set_values(self, values: dict):
        if "timeout_ms" in values:
            self.timeout_spin.setValue(values["timeout_ms"])
        if "check_interval_ms" in values:
            self.interval_spin.setValue(values["check_interval_ms"])


class WaitImagePanel(BaseActionPanel):
    """Панель для ожидания изображения"""
    
    def __init__(self):
        super().__init__()
        self.parent_widget = None
    
    def create_panel(self, parent_widget) -> QGroupBox:
        self.parent_widget = parent_widget
        group = QGroupBox("🖼 Параметры изображения")
        layout = QFormLayout()
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Путь к изображению...")
        layout.addRow("Изображение:", self.path_input)
        
        self.browse_btn = QPushButton("📁 Выбрать")
        self.browse_btn.clicked.connect(self._browse_image)
        layout.addRow("", self.browse_btn)
        
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.0, 1.0)
        self.confidence_spin.setValue(0.9)
        self.confidence_spin.setSingleStep(0.05)
        layout.addRow("Точность:", self.confidence_spin)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 60000)
        self.timeout_spin.setValue(5000)
        layout.addRow("Таймаут (мс):", self.timeout_spin)
        
        group.setLayout(layout)
        return group
    
    def _browse_image(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self.parent_widget, "Выберите изображение", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        if filepath:
            self.path_input.setText(filepath)
    
    def get_values(self) -> dict:
        return {
            "image_path": self.path_input.text(),
            "confidence": self.confidence_spin.value(),
            "timeout_ms": self.timeout_spin.value(),
        }
    
    def set_values(self, values: dict):
        if "image_path" in values:
            self.path_input.setText(values["image_path"])
        if "confidence" in values:
            self.confidence_spin.setValue(values["confidence"])
        if "timeout_ms" in values:
            self.timeout_spin.setValue(values["timeout_ms"])


class WaitTextPanel(BaseActionPanel):
    """Панель для ожидания текста (OCR)"""
    
    def create_panel(self, parent_widget) -> QGroupBox:
        group = QGroupBox("📝 Параметры текста")
        layout = QFormLayout()
        
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Текст для поиска...")
        layout.addRow("Текст:", self.text_input)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 60000)
        self.timeout_spin.setValue(5000)
        layout.addRow("Таймаут (мс):", self.timeout_spin)
        
        group.setLayout(layout)
        return group
    
    def get_values(self) -> dict:
        return {
            "search_text": self.text_input.text(),
            "timeout_ms": self.timeout_spin.value(),
        }
    
    def set_values(self, values: dict):
        if "search_text" in values:
            self.text_input.setText(values["search_text"])
        if "timeout_ms" in values:
            self.timeout_spin.setValue(values["timeout_ms"])


class ConditionalPanel(BaseActionPanel):
    """Панель для условного действия"""
    
    def create_panel(self, parent_widget) -> QGroupBox:
        group = QGroupBox("❓ Условие")
        layout = QFormLayout()
        
        self.condition_type = QComboBox()
        self.condition_type.addItems(["pixel_color", "image_exists", "text_exists"])
        layout.addRow("Тип условия:", self.condition_type)
        
        self.condition_value = QLineEdit()
        layout.addRow("Значение:", self.condition_value)
        
        self.if_true = QComboBox()
        self.if_true.addItems(["execute_next", "skip_next", "break"])
        layout.addRow("Если true:", self.if_true)
        
        self.if_false = QComboBox()
        self.if_false.addItems(["skip_next", "execute_next", "break"])
        layout.addRow("Если false:", self.if_false)
        
        group.setLayout(layout)
        return group
    
    def get_values(self) -> dict:
        return {
            "condition_type": self.condition_type.currentText(),
            "condition_value": self.condition_value.text(),
            "if_true": self.if_true.currentText(),
            "if_false": self.if_false.currentText(),
        }
    
    def set_values(self, values: dict):
        if "condition_type" in values:
            self.condition_type.setCurrentText(values["condition_type"])
        if "condition_value" in values:
            self.condition_value.setText(values["condition_value"])
        if "if_true" in values:
            self.if_true.setCurrentText(values["if_true"])
        if "if_false" in values:
            self.if_false.setCurrentText(values["if_false"])


class LoopPanel(BaseActionPanel):
    """Панель для цикла"""
    
    def create_panel(self, parent_widget) -> QGroupBox:
        group = QGroupBox("🔁 Параметры цикла")
        layout = QFormLayout()
        
        self.loop_type = QComboBox()
        self.loop_type.addItems(["count", "while", "until"])
        layout.addRow("Тип цикла:", self.loop_type)
        
        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(1, 10000)
        self.iterations_spin.setValue(1)
        layout.addRow("Количество итераций:", self.iterations_spin)
        
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 10000)
        self.delay_spin.setValue(0)
        layout.addRow("Задержка между итерациями (мс):", self.delay_spin)
        
        group.setLayout(layout)
        return group
    
    def get_values(self) -> dict:
        return {
            "loop_type": self.loop_type.currentText(),
            "iterations": self.iterations_spin.value(),
            "delay_ms": self.delay_spin.value(),
        }
    
    def set_values(self, values: dict):
        if "loop_type" in values:
            self.loop_type.setCurrentText(values["loop_type"])
        if "iterations" in values:
            self.iterations_spin.setValue(values["iterations"])
        if "delay_ms" in values:
            self.delay_spin.setValue(values["delay_ms"])


class ScreenshotPanel(BaseActionPanel):
    """Панель для скриншота"""
    
    def __init__(self):
        super().__init__()
        self.parent_widget = None
    
    def create_panel(self, parent_widget) -> QGroupBox:
        self.parent_widget = parent_widget
        group = QGroupBox("📸 Параметры скриншота")
        layout = QFormLayout()
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Путь для сохранения...")
        layout.addRow("Сохранить в:", self.path_input)
        
        self.browse_btn = QPushButton("📁 Выбрать")
        self.browse_btn.clicked.connect(self._browse_path)
        layout.addRow("", self.browse_btn)
        
        region_layout = QHBoxLayout()
        self.region_x = QSpinBox()
        self.region_x.setRange(-32768, 32767)
        self.region_x.setValue(0)
        region_layout.addWidget(QLabel("X:"))
        region_layout.addWidget(self.region_x)
        
        self.region_y = QSpinBox()
        self.region_y.setRange(-32768, 32767)
        self.region_y.setValue(0)
        region_layout.addWidget(QLabel("Y:"))
        region_layout.addWidget(self.region_y)
        
        self.region_w = QSpinBox()
        self.region_w.setRange(0, 32767)
        self.region_w.setValue(0)
        region_layout.addWidget(QLabel("Ш:"))
        region_layout.addWidget(self.region_w)
        
        self.region_h = QSpinBox()
        self.region_h.setRange(0, 32767)
        self.region_h.setValue(0)
        region_layout.addWidget(QLabel("В:"))
        region_layout.addWidget(self.region_h)
        
        layout.addRow("Область (0=весь экран):", region_layout)
        
        group.setLayout(layout)
        return group
    
    def _browse_path(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self.parent_widget, "Сохранить скриншот", "",
            "PNG Files (*.png);;All Files (*)"
        )
        if filepath:
            self.path_input.setText(filepath)
    
    def get_values(self) -> dict:
        return {
            "save_path": self.path_input.text(),
            "region_x": self.region_x.value(),
            "region_y": self.region_y.value(),
            "region_width": self.region_w.value(),
            "region_height": self.region_h.value(),
        }
    
    def set_values(self, values: dict):
        if "save_path" in values:
            self.path_input.setText(values["save_path"])
        if "region_x" in values:
            self.region_x.setValue(values["region_x"])
        if "region_y" in values:
            self.region_y.setValue(values["region_y"])
        if "region_width" in values:
            self.region_w.setValue(values["region_width"])
        if "region_height" in values:
            self.region_h.setValue(values["region_height"])


class LogPanel(BaseActionPanel):
    """Панель для логирования"""
    
    def create_panel(self, parent_widget) -> QGroupBox:
        group = QGroupBox("📋 Параметры лога")
        layout = QFormLayout()
        
        self.level_combo = QComboBox()
        self.level_combo.addItems(["INFO", "DEBUG", "WARNING", "ERROR"])
        layout.addRow("Уровень:", self.level_combo)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Сообщение в лог...")
        layout.addRow("Сообщение:", self.message_input)
        
        group.setLayout(layout)
        return group
    
    def get_values(self) -> dict:
        return {
            "log_level": self.level_combo.currentText(),
            "message": self.message_input.text(),
        }
    
    def set_values(self, values: dict):
        if "log_level" in values:
            self.level_combo.setCurrentText(values["log_level"])
        if "message" in values:
            self.message_input.setText(values["message"])


class DBSearchPanel(BaseActionPanel):
    """Панель для поиска в базе данных"""

    def __init__(self):
        super().__init__()
        self.parent_widget = None

    def create_panel(self, parent_widget) -> QGroupBox:
        self.parent_widget = parent_widget
        group = QGroupBox("🔍 Поиск в базе данных")
        layout = QFormLayout()

        # Выбор базы данных
        self.db_combo = QComboBox()
        self.db_combo.setEditable(False)
        self.db_combo.setToolTip("Выберите базу данных из списка")
        layout.addRow("База данных:", self.db_combo)

        # Кнопка обновления списка БД
        self.refresh_btn = QPushButton("🔄 Обновить список")
        self.refresh_btn.clicked.connect(self._refresh_databases)
        layout.addRow("", self.refresh_btn)

        # Колонка для поиска
        self.search_column_input = QLineEdit()
        self.search_column_input.setPlaceholderText("Например: Акт")
        layout.addRow("Колонка поиска:", self.search_column_input)

        # Значение для поиска
        self.search_value_input = QLineEdit()
        self.search_value_input.setPlaceholderText("Например: 123")
        layout.addRow("Искомое значение:", self.search_value_input)

        # Колонка для получения результата
        self.result_column_input = QLineEdit()
        self.result_column_input.setPlaceholderText("Например: Счет-фактура")
        layout.addRow("Колонка результата:", self.result_column_input)

        # Переменная для сохранения результата
        self.result_variable_input = QLineEdit()
        self.result_variable_input.setPlaceholderText("Например: invoice_number")
        self.result_variable_input.setToolTip("Имя переменной для сохранения результата")
        layout.addRow("Переменная:", self.result_variable_input)

        group.setLayout(layout)
        return group

    def _refresh_databases(self):
        """Обновить список баз данных"""
        if self.parent_widget and hasattr(self.parent_widget, 'backend'):
            self.db_combo.clear()
            for db_path in self.parent_widget.backend.databases:
                name = os.path.basename(db_path)
                self.db_combo.addItem(name, db_path)

    def get_values(self) -> dict:
        return {
            "database": self.db_combo.currentText(),
            "search_column": self.search_column_input.text(),
            "search_value": self.search_value_input.text(),
            "result_column": self.result_column_input.text(),
            "result_variable": self.result_variable_input.text(),
        }

    def set_values(self, values: dict):
        if "database" in values:
            self.db_combo.setCurrentText(values["database"])
        if "search_column" in values:
            self.search_column_input.setText(values["search_column"])
        if "search_value" in values:
            self.search_value_input.setText(values["search_value"])
        if "result_column" in values:
            self.result_column_input.setText(values["result_column"])
        if "result_variable" in values:
            self.result_variable_input.setText(values["result_variable"])


class DBGetValuePanel(BaseActionPanel):
    """Панель для получения значения из БД по переменной"""

    def __init__(self):
        super().__init__()
        self.parent_widget = None

    def create_panel(self, parent_widget) -> QGroupBox:
        self.parent_widget = parent_widget
        group = QGroupBox("📥 Получить значение из БД")
        layout = QFormLayout()

        # Выбор базы данных
        self.db_combo = QComboBox()
        self.db_combo.setEditable(False)
        self.db_combo.setToolTip("Выберите базу данных")
        layout.addRow("База данных:", self.db_combo)

        # Кнопка обновления
        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self._refresh_databases)
        layout.addRow("", self.refresh_btn)

        # Переменная с результатом поиска
        self.variable_input = QLineEdit()
        self.variable_input.setPlaceholderText("Например: invoice_number")
        self.variable_input.setToolTip("Переменная, в которой хранится результат поиска")
        layout.addRow("Переменная:", self.variable_input)

        # Колонка для получения
        self.column_input = QLineEdit()
        self.column_input.setPlaceholderText("Например: Контрагент")
        layout.addRow("Колонка:", self.column_input)

        # Переменная для сохранения
        self.result_variable_input = QLineEdit()
        self.result_variable_input.setPlaceholderText("Например: contractor")
        self.result_variable_input.setToolTip("Имя переменной для сохранения результата")
        layout.addRow("Сохранить в:", self.result_variable_input)

        group.setLayout(layout)
        
        # Обновить список БД
        self._refresh_databases()
        
        return group

    def _refresh_databases(self):
        """Обновить список баз данных"""
        if self.parent_widget and hasattr(self.parent_widget, 'backend'):
            self.db_combo.clear()
            for db_path in self.parent_widget.backend.databases:
                name = os.path.basename(db_path)
                self.db_combo.addItem(name, db_path)

    def get_values(self) -> dict:
        return {
            "database": self.db_combo.currentText(),
            "variable": self.variable_input.text(),
            "column": self.column_input.text(),
            "result_variable": self.result_variable_input.text(),
        }

    def set_values(self, values: dict):
        if "database" in values:
            self.db_combo.setCurrentText(values["database"])
        if "variable" in values:
            self.variable_input.setText(values["variable"])
        if "column" in values:
            self.column_input.setText(values["column"])
        if "result_variable" in values:
            self.result_variable_input.setText(values["result_variable"])


class DBIteratePanel(BaseActionPanel):
    """Панель для итерации по строкам БД"""

    def __init__(self):
        super().__init__()
        self.parent_widget = None

    def create_panel(self, parent_widget) -> QGroupBox:
        self.parent_widget = parent_widget
        group = QGroupBox("🔁 Пройти по строкам БД")
        layout = QFormLayout()

        # Выбор базы данных
        self.db_combo = QComboBox()
        self.db_combo.setEditable(False)
        self.db_combo.setToolTip("Выберите базу данных из списка")
        layout.addRow("База данных:", self.db_combo)

        # Кнопка обновления списка БД
        self.refresh_btn = QPushButton("🔄 Обновить список")
        self.refresh_btn.clicked.connect(self._refresh_databases)
        layout.addRow("", self.refresh_btn)

        # Колонка для фильтрации (опционально)
        self.filter_column_input = QLineEdit()
        self.filter_column_input.setPlaceholderText("Например: Акт (оставьте пустым для всех)")
        layout.addRow("Фильтр по колонке:", self.filter_column_input)

        # Значение фильтра
        self.filter_value_input = QLineEdit()
        self.filter_value_input.setPlaceholderText("Например: 123")
        layout.addRow("Значение фильтра:", self.filter_value_input)

        # Переменная для текущего номера строки
        self.row_variable_input = QLineEdit()
        self.row_variable_input.setPlaceholderText("Например: current_row")
        self.row_variable_input.setToolTip("Переменная для хранения текущего номера строки")
        layout.addRow("Переменная строки:", self.row_variable_input)

        # Переменная для хранения текущего значения
        self.value_variable_input = QLineEdit()
        self.value_variable_input.setPlaceholderText("Например: current_invoice")
        self.value_variable_input.setToolTip("Переменная для хранения значения из колонки")
        layout.addRow("Переменная значения:", self.value_variable_input)

        # Колонка для получения значения
        self.value_column_input = QLineEdit()
        self.value_column_input.setPlaceholderText("Например: Счет-фактура")
        self.value_column_input.setToolTip("Колонка, из которой брать значение для переменной")
        layout.addRow("Колонка значения:", self.value_column_input)

        group.setLayout(layout)
        
        # Обновить список БД при создании
        self._refresh_databases()
        
        return group

    def _refresh_databases(self):
        """Обновить список баз данных"""
        if self.parent_widget and hasattr(self.parent_widget, 'backend'):
            self.db_combo.clear()
            for db_path in self.parent_widget.backend.databases:
                name = os.path.basename(db_path)
                self.db_combo.addItem(name, db_path)

    def get_values(self) -> dict:
        return {
            "database": self.db_combo.currentText(),
            "filter_column": self.filter_column_input.text(),
            "filter_value": self.filter_value_input.text(),
            "row_variable": self.row_variable_input.text(),
            "value_variable": self.value_variable_input.text(),
            "value_column": self.value_column_input.text(),
        }

    def set_values(self, values: dict):
        if "database" in values:
            self.db_combo.setCurrentText(values["database"])
        if "filter_column" in values:
            self.filter_column_input.setText(values["filter_column"])
        if "filter_value" in values:
            self.filter_value_input.setText(values["filter_value"])
        if "row_variable" in values:
            self.row_variable_input.setText(values["row_variable"])
        if "value_variable" in values:
            self.value_variable_input.setText(values["value_variable"])
        if "value_column" in values:
            self.value_column_input.setText(values["value_column"])


class RunRowPanel(BaseActionPanel):
    """Панель для запуска другой строки (подпрограммы)"""

    def __init__(self):
        super().__init__()
        self.parent_widget = None

    def create_panel(self, parent_widget) -> QGroupBox:
        self.parent_widget = parent_widget
        group = QGroupBox("▶ Запустить строку (подпрограмму)")
        layout = QFormLayout()

        # Выбор строки
        self.row_combo = QComboBox()
        self.row_combo.setEditable(False)
        self.row_combo.setToolTip("Выберите строку для запуска")
        layout.addRow("Строка:", self.row_combo)

        # Кнопка обновления
        self.refresh_btn = QPushButton("🔄 Обновить список")
        self.refresh_btn.clicked.connect(self._refresh_rows)
        layout.addRow("", self.refresh_btn)

        # Режим ожидания
        self.wait_check = QCheckBox("Ждать завершения перед продолжением")
        self.wait_check.setChecked(True)
        layout.addRow("", self.wait_check)

        # Описание
        desc_label = QLabel("Запускает другую строку как подпрограмму.\nПосле завершения выполнение вернётся к следующему действию.")
        desc_label.setStyleSheet("color: #888; font-size: 11px;")
        desc_label.setWordWrap(True)
        layout.addRow("", desc_label)

        group.setLayout(layout)
        
        # Обновить список строк с задержкой
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._refresh_rows)
        
        return group

    def _refresh_rows(self):
        """Обновить список строк в текущей доске"""
        if self.parent_widget and hasattr(self.parent_widget, 'backend'):
            self.row_combo.clear()
            current_board = self.parent_widget.backend.current_board
            if current_board:
                for row in current_board.rows:
                    # Не показывать текущую строку (если можно определить)
                    self.row_combo.addItem(row.name, row.id)
            else:
                self.row_combo.addItem("Нет доступных строк", None)
    
    def get_values(self) -> dict:
        return {
            "row_id": self.row_combo.currentData(),
            "row_name": self.row_combo.currentText(),
            "wait_complete": self.wait_check.isChecked(),
        }
    
    def set_values(self, values: dict):
        # Обновить список строк перед установкой значения
        self._refresh_rows()
        
        if "row_id" in values:
            idx = self.row_combo.findData(values["row_id"])
            if idx >= 0:
                self.row_combo.setCurrentIndex(idx)
        if "wait_complete" in values:
            self.wait_check.setChecked(values["wait_complete"])


class DBSavePanel(BaseActionPanel):
    """Панель для сохранения в БД"""

    def __init__(self):
        super().__init__()
        self.parent_widget = None

    def create_panel(self, parent_widget) -> QGroupBox:
        self.parent_widget = parent_widget
        group = QGroupBox("💾 Сохранить в БД")
        layout = QFormLayout()

        # Выбор базы данных
        self.db_combo = QComboBox()
        self.db_combo.setEditable(False)
        layout.addRow("База данных:", self.db_combo)

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self._refresh_databases)
        layout.addRow("", self.refresh_btn)

        # Поиск по колонке
        self.search_column_input = QLineEdit()
        self.search_column_input.setPlaceholderText("Например: Акт")
        layout.addRow("Поиск по колонке:", self.search_column_input)

        # Значение для поиска
        self.search_value_input = QLineEdit()
        self.search_value_input.setPlaceholderText("Например: 123 или {variable}")
        layout.addRow("Значение поиска:", self.search_value_input)

        # Колонка для обновления
        self.update_column_input = QLineEdit()
        self.update_column_input.setPlaceholderText("Например: Контрагент")
        layout.addRow("Обновить колонку:", self.update_column_input)

        # Значение для сохранения
        self.save_value_input = QLineEdit()
        self.save_value_input.setPlaceholderText("Например: {contractor} или текст")
        layout.addRow("Значение:", self.save_value_input)

        group.setLayout(layout)
        
        self._refresh_databases()
        
        return group

    def _refresh_databases(self):
        """Обновить список БД"""
        if self.parent_widget and hasattr(self.parent_widget, 'backend'):
            self.db_combo.clear()
            for db_path in self.parent_widget.backend.databases:
                name = os.path.basename(db_path)
                self.db_combo.addItem(name, db_path)

    def get_values(self) -> dict:
        return {
            "database": self.db_combo.currentText(),
            "search_column": self.search_column_input.text(),
            "search_value": self.search_value_input.text(),
            "update_column": self.update_column_input.text(),
            "save_value": self.save_value_input.text(),
        }

    def set_values(self, values: dict):
        if "database" in values:
            self.db_combo.setCurrentText(values["database"])
        if "search_column" in values:
            self.search_column_input.setText(values["search_column"])
        if "search_value" in values:
            self.search_value_input.setText(values["search_value"])
        if "update_column" in values:
            self.update_column_input.setText(values["update_column"])
        if "save_value" in values:
            self.save_value_input.setText(values["save_value"])


class CheckValuePanel(BaseActionPanel):
    """Панель для проверки значения (замена сумм)"""

    def __init__(self):
        super().__init__()
        self.parent_widget = None

    def create_panel(self, parent_widget) -> QGroupBox:
        self.parent_widget = parent_widget
        group = QGroupBox("✅ Проверка значения")
        layout = QFormLayout()

        # Выбор базы данных замен
        self.db_combo = QComboBox()
        self.db_combo.setEditable(False)
        layout.addRow("База замен:", self.db_combo)

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self._refresh_databases)
        layout.addRow("", self.refresh_btn)

        # Колонка с исходным значением
        self.from_column_input = QLineEdit()
        self.from_column_input.setPlaceholderText("Например: Старая_сумма")
        layout.addRow("Колонка 'От':", self.from_column_input)

        # Колонка с новым значением
        self.to_column_input = QLineEdit()
        self.to_column_input.setPlaceholderText("Например: Новая_сумма")
        layout.addRow("Колонка 'До':", self.to_column_input)

        # Переменная для проверки
        self.check_variable_input = QLineEdit()
        self.check_variable_input.setPlaceholderText("Например: current_sum")
        layout.addRow("Проверить переменную:", self.check_variable_input)

        # Переменная для результата
        self.result_variable_input = QLineEdit()
        self.result_variable_input.setPlaceholderText("Например: new_sum")
        layout.addRow("Результат в переменную:", self.result_variable_input)

        group.setLayout(layout)
        
        self._refresh_databases()
        
        return group

    def _refresh_databases(self):
        """Обновить список БД"""
        if self.parent_widget and hasattr(self.parent_widget, 'backend'):
            self.db_combo.clear()
            for db_path in self.parent_widget.backend.databases:
                name = os.path.basename(db_path)
                self.db_combo.addItem(name, db_path)

    def get_values(self) -> dict:
        return {
            "database": self.db_combo.currentText(),
            "from_column": self.from_column_input.text(),
            "to_column": self.to_column_input.text(),
            "check_variable": self.check_variable_input.text(),
            "result_variable": self.result_variable_input.text(),
        }

    def set_values(self, values: dict):
        if "database" in values:
            self.db_combo.setCurrentText(values["database"])
        if "from_column" in values:
            self.from_column_input.setText(values["from_column"])
        if "to_column" in values:
            self.to_column_input.setText(values["to_column"])
        if "check_variable" in values:
            self.check_variable_input.setText(values["check_variable"])
        if "result_variable" in values:
            self.result_variable_input.setText(values["result_variable"])


# =============================================================================
# ФАБРИКА ПАНЕЛЕЙ (должна быть после всех классов)
# =============================================================================

PANELS = {
    ActionType.MOUSE_CLICK: MouseClickPanel,
    ActionType.MOUSE_MOVE: MouseMovePanel,
    ActionType.KEY_PRESS: KeyPressPanel,
    ActionType.WAIT_TIME: WaitTimePanel,
    ActionType.WAIT_PIXEL_COLOR: WaitPixelColorPanel,
    ActionType.WAIT_PIXEL_CHANGE: WaitPixelChangePanel,
    ActionType.WAIT_IMAGE: WaitImagePanel,
    ActionType.WAIT_TEXT: WaitTextPanel,
    ActionType.CONDITIONAL: ConditionalPanel,
    ActionType.LOOP: LoopPanel,
    ActionType.SCREENSHOT: ScreenshotPanel,
    ActionType.LOG: LogPanel,
    ActionType.DB_SEARCH: DBSearchPanel,
    ActionType.DB_GET_VALUE: DBGetValuePanel,
    ActionType.DB_ITERATE: DBIteratePanel,
    ActionType.DB_SAVE: DBSavePanel,
    ActionType.RUN_ROW: RunRowPanel,
    ActionType.CHECK_VALUE: CheckValuePanel,
}


def get_panel(action_type: ActionType) -> BaseActionPanel:
    """Получить панель для типа действия"""
    panel_class = PANELS.get(action_type)
    if panel_class:
        return panel_class()
    return None
