"""
Модальное окно для записи сочетаний клавиш
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence


class KeyRecorderDialog(QDialog):
    """Модальное окно для записи клавиш"""
    
    keys_recorded = pyqtSignal(str)  # Сигнал с записанным сочетанием
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Запись клавиш")
        self.setModal(True)
        self.setFixedSize(450, 320)
        
        self.recorded_keys = []
        self.is_recording = True
        
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title = QLabel("Нажмите сочетание клавиш")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Подсказка
        hint = QLabel("Нажмите нужные клавиши на клавиатуре.\nМышь не записывается.")
        hint.setStyleSheet("color: #888; font-size: 12px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
        
        # Визуализация нажатых клавиш
        self.keys_display = QLabel("Ожидание...")
        self.keys_display.setStyleSheet("""
            QLabel {
                background-color: #1a1a2e;
                color: #00ff88;
                font-size: 24px;
                font-weight: bold;
                padding: 20px;
                border-radius: 8px;
                border: 2px solid #00ff88;
            }
        """)
        self.keys_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.keys_display.setMinimumHeight(80)
        layout.addWidget(self.keys_display)
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #444;")
        line.setMaximumHeight(1)
        layout.addWidget(line)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        btn_layout.addStretch()
        
        self.confirm_btn = QPushButton("Продолжить")
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.confirm_btn.clicked.connect(self._confirm_keys)
        self.confirm_btn.setEnabled(False)
        btn_layout.addWidget(self.confirm_btn)
        
        layout.addLayout(btn_layout)
        
        # Фокус на окно
        self.keys_display.setFocus()
    
    def _confirm_keys(self):
        """Подтвердить запись"""
        if self.recorded_keys:
            keys_str = "+".join(self.recorded_keys)
            self.keys_recorded.emit(keys_str)
            self.accept()
    
    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        if not self.is_recording:
            return
        
        key = event.key()
        
        # Игнорируем модификаторы сами по себе (только для отображения)
        modifier_only = key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, 
                                Qt.Key.Key_Alt, Qt.Key.Key_Meta, Qt.Key.Key_AltGr)
        
        # Получаем название клавиши
        key_name = self._get_key_name(key)
        
        # Собираем текущие модификаторы
        current_modifiers = []
        modifiers = event.modifiers()
        
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            current_modifiers.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            current_modifiers.append("Shift")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            current_modifiers.append("Alt")
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            current_modifiers.append("Win")
        
        # Если нажат только модификатор - показываем его но не добавляем
        if modifier_only:
            display_keys = current_modifiers.copy()
            if key_name and key_name not in current_modifiers:
                display_keys.append(key_name)
            self._update_display(display_keys)
            return
        
        # Формируем итоговый список клавиш
        final_keys = current_modifiers.copy()
        
        # Добавляем саму клавишу если она есть и не дублирует модификатор
        if key_name and key_name not in current_modifiers:
            final_keys.append(key_name)
        
        # Если клавиша не распознана, используем код
        if not key_name:
            final_keys.append(f"Key{key}")
        
        self.recorded_keys = final_keys
        self._update_display(self.recorded_keys)
        self.confirm_btn.setEnabled(len(self.recorded_keys) > 0)
    
    def _get_key_name(self, key) -> str:
        """Получить имя клавиши"""
        # Специальные клавиши
        special_keys = {
            Qt.Key.Key_Space: "Space",
            Qt.Key.Key_Tab: "Tab",
            Qt.Key.Key_Return: "Enter",
            Qt.Key.Key_Enter: "Enter",
            Qt.Key.Key_Backspace: "Backspace",
            Qt.Key.Key_Delete: "Delete",
            Qt.Key.Key_Insert: "Insert",
            Qt.Key.Key_Home: "Home",
            Qt.Key.Key_End: "End",
            Qt.Key.Key_PageUp: "PageUp",
            Qt.Key.Key_PageDown: "PageDown",
            Qt.Key.Key_Left: "Left",
            Qt.Key.Key_Right: "Right",
            Qt.Key.Key_Up: "Up",
            Qt.Key.Key_Down: "Down",
            Qt.Key.Key_Escape: "Esc",
            Qt.Key.Key_CapsLock: "CapsLock",
            Qt.Key.Key_NumLock: "NumLock",
            Qt.Key.Key_ScrollLock: "ScrollLock",
            Qt.Key.Key_Print: "PrintScreen",
            Qt.Key.Key_Pause: "Pause",
        }
        
        if key in special_keys:
            return special_keys[key]
        
        # F-клавиши
        if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F24:
            return f"F{key - Qt.Key.Key_F1 + 1}"
        
        # Буквы (A-Z)
        if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            return chr(ord('A') + (key - Qt.Key.Key_A))
        
        # Цифры (0-9)
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            return str(key - Qt.Key.Key_0)
        
        # Клавиши NumPad
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            return f"Num{key - Qt.Key.Key_0}"
        
        return ""
    
    def _update_display(self, keys: list = None):
        """Обновить отображение"""
        if keys:
            self.keys_display.setText("+".join(keys))
        elif self.recorded_keys:
            self.keys_display.setText("+".join(self.recorded_keys))
        else:
            self.keys_display.setText("Ожидание...")
    
    def keyReleaseEvent(self, event):
        """Отпускание клавиш - не делаем ничего"""
        pass
    
    def showEvent(self, event):
        """При показе окна - фокус на поле ввода"""
        super().showEvent(event)
        self.keys_display.setFocus()
