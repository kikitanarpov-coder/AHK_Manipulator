"""
Окно настроек приложения
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QGroupBox, QFormLayout, QFileDialog, QComboBox,
    QScrollArea, QWidget, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices


class SettingsDialog(QDialog):
    """Окно настроек приложения"""
    
    databases_changed = pyqtSignal(list)  # Список путей к БД
    
    def __init__(self, parent=None, databases: list = None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        self.databases = databases or []
        self.db_list = None  # Будет создан при показе панели БД
        
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title = QLabel("⚙ Настройки")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        
        # Список категорий настроек
        self.settings_list = QListWidget()
        self.settings_list.setMaximumHeight(120)
        
        self.settings_list.addItem("📊 Базы данных (Excel)")
        self.settings_list.addItem("🎨 Тема оформления")
        self.settings_list.addItem("⌨ Горячие клавиши")
        self.settings_list.addItem("📁 Пути по умолчанию")
        
        self.settings_list.currentRowChanged.connect(self._on_category_changed)
        layout.addWidget(self.settings_list)
        
        # Scroll area для панелей настроек
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        
        self.settings_content = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_content)
        
        self.scroll.setWidget(self.settings_content)
        layout.addWidget(self.scroll)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Сохранить")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        # Показать первую категорию по умолчанию
        self.settings_list.setCurrentRow(0)
    
    def _clear_settings_layout(self):
        """Очистить layout настроек"""
        while self.settings_layout.count():
            item = self.settings_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _on_category_changed(self, index: int):
        """Изменение категории настроек"""
        self._clear_settings_layout()
        
        # Показать нужную панель
        if index == 0:
            self._show_database_settings()
        elif index == 1:
            self._show_theme_settings()
        elif index == 2:
            self._show_hotkey_settings()
        elif index == 3:
            self._show_path_settings()
    
    def _show_database_settings(self):
        """Показать настройки баз данных"""
        # Сначала очистить текущий layout
        self._clear_settings_layout()
        
        group = QGroupBox("📊 Базы данных (Excel)")
        layout = QVBoxLayout()

        # Описание
        desc = QLabel("Добавьте Excel файлы для использования в качестве баз данных.\n"
                      "Поддерживаются форматы: .xlsx, .xls, .csv")
        desc.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(desc)

        # Список баз данных
        self.db_list = QListWidget()
        self.db_list.setMinimumHeight(200)

        for db_path in self.databases:
            item = QListWidgetItem(f"📄 {os.path.basename(db_path)}")
            item.setToolTip(db_path)
            item.setData(Qt.ItemDataRole.UserRole, db_path)
            self.db_list.addItem(item)

        layout.addWidget(self.db_list)

        # Кнопки управления
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("➕ Добавить")
        add_btn.clicked.connect(self._add_database)
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("🗑 Удалить")
        remove_btn.clicked.connect(self._remove_database)
        btn_layout.addWidget(remove_btn)

        view_btn = QPushButton("👁 Просмотр")
        view_btn.clicked.connect(self._view_database)
        btn_layout.addWidget(view_btn)

        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        group.setLayout(layout)

        self.settings_layout.addWidget(group)
    
    def _add_database(self):
        """Добавить базу данных"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Выберите базу данных", "",
            "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
        )
        
        if filepath:
            if filepath not in self.databases:
                self.databases.append(filepath)
                # Полностью пересоздать панель настроек БД
                self._show_database_settings()
    
    def _remove_database(self):
        """Удалить базу данных"""
        if not self.db_list:
            return
            
        current_item = self.db_list.currentItem()
        if current_item:
            db_path = current_item.data(Qt.ItemDataRole.UserRole)
            if db_path in self.databases:
                self.databases.remove(db_path)
            row = self.db_list.row(current_item)
            self.db_list.takeItem(row)
    
    def _view_database(self):
        """Открыть базу данных в приложении по умолчанию"""
        if not self.db_list:
            return
            
        current_item = self.db_list.currentItem()
        if current_item:
            db_path = current_item.data(Qt.ItemDataRole.UserRole)
            if db_path and os.path.exists(db_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(db_path))
    
    def _show_theme_settings(self):
        """Показать настройки темы"""
        group = QGroupBox("🎨 Тема оформления")
        layout = QFormLayout()
        
        theme_combo = QComboBox()
        theme_combo.addItems(["Тёмная", "Светлая", "Системная"])
        theme_combo.setCurrentIndex(0)
        layout.addRow("Тема:", theme_combo)
        
        accent_label = QLabel("Акцентный цвет:")
        layout.addRow(accent_label)
        
        color_layout = QHBoxLayout()
        colors = ["#3498db", "#27ae60", "#e67e22", "#9b59b6", "#e74c3c"]
        for color in colors:
            btn = QPushButton()
            btn.setMaximumWidth(40)
            btn.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
            color_layout.addWidget(btn)
        
        layout.addRow(color_layout)
        group.setLayout(layout)
        self.settings_layout.addWidget(group)
    
    def _show_hotkey_settings(self):
        """Показать настройки горячих клавиш"""
        group = QGroupBox("⌨ Горячие клавиши")
        layout = QFormLayout()
        
        hotkeys = [
            ("Запуск выполнения:", "F5"),
            ("Остановка:", "Shift+F5"),
            ("Начать запись:", "F9"),
            ("Захват координат:", "Cmd+Shift+R"),
            ("Новая доска:", "Ctrl+N"),
            ("Сохранить:", "Ctrl+S"),
        ]
        
        for label, default in hotkeys:
            edit = QLineEdit(default)
            edit.setReadOnly(True)
            layout.addRow(label, edit)
        
        note = QLabel("💡 Для изменения нажмите на поле и введите новое сочетание")
        note.setStyleSheet("color: #888; font-size: 11px;")
        layout.addRow(note)
        
        group.setLayout(layout)
        self.settings_layout.addWidget(group)
    
    def _show_path_settings(self):
        """Показать настройки путей"""
        group = QGroupBox("📁 Пути по умолчанию")
        layout = QFormLayout()
        
        self.screenshot_path_input = QLineEdit()
        self.screenshot_path_input.setPlaceholderText("~/Pictures/AHK_Screenshots")
        browse_ss_btn = QPushButton("📁 Обзор")
        ss_layout = QHBoxLayout()
        ss_layout.addWidget(self.screenshot_path_input)
        ss_layout.addWidget(browse_ss_btn)
        layout.addRow("Скриншоты:", ss_layout)
        
        self.export_path_input = QLineEdit()
        self.export_path_input.setPlaceholderText("~/Documents/AHK_Scripts")
        browse_exp_btn = QPushButton("📁 Обзор")
        exp_layout = QHBoxLayout()
        exp_layout.addWidget(self.export_path_input)
        exp_layout.addWidget(browse_exp_btn)
        layout.addRow("Экспорт AHK:", exp_layout)
        
        self.project_path_input = QLineEdit()
        self.project_path_input.setPlaceholderText("~/Documents/AHK_Projects")
        browse_proj_btn = QPushButton("📁 Обзор")
        proj_layout = QHBoxLayout()
        proj_layout.addWidget(self.project_path_input)
        proj_layout.addWidget(browse_proj_btn)
        layout.addRow("Проекты:", proj_layout)
        
        group.setLayout(layout)
        self.settings_layout.addWidget(group)
    
    def _save_settings(self):
        """Сохранить настройки"""
        self.databases_changed.emit(self.databases)
        self.accept()
    
    def get_databases(self) -> list:
        """Получить список баз данных"""
        return self.databases
