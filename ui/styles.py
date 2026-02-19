"""
Профессиональные стили для приложения AHK Manipulator
Спокойные тона, хорошая читаемость, масштабируемость
"""

# ===== Профессиональная тёмная тема =====
PROFESSIONAL_DARK_STYLESHEET = """
/* ===== Глобальные стили ===== */
* {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

QMainWindow {
    background-color: #2b2b2b;
}

QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
    font-size: 13px;
}

/* ===== Toolbar ===== */
QToolBar {
    background-color: #3c3f41;
    border-bottom: 1px solid #5c6265;
    padding: 4px;
    spacing: 4px;
}

QToolBar QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 6px 12px;
    color: #ffffff;
}

QToolBar QToolButton:hover {
    background-color: #4c5052;
    border-color: #5c6265;
}

QToolBar QToolButton:pressed {
    background-color: #5c6265;
}

/* ===== Status Bar ===== */
QStatusBar {
    background-color: #3c3f41;
    border-top: 1px solid #5c6265;
    color: #bbbbbb;
}

/* ===== Кнопки ===== */
QPushButton {
    background-color: #4c5052;
    border: 1px solid #5c6265;
    border-radius: 4px;
    padding: 6px 16px;
    color: #ffffff;
}

QPushButton:hover {
    background-color: #5c6265;
}

QPushButton:pressed {
    background-color: #6c7275;
}

QPushButton:disabled {
    background-color: #3c3f41;
    color: #777777;
}

/* Акцентные кнопки */
QPushButton#primaryButton {
    background-color: #365880;
    border-color: #4a6d8c;
}

QPushButton#primaryButton:hover {
    background-color: #4a6d8c;
}

QPushButton#successButton {
    background-color: #3a7a3a;
    border-color: #4a8a4a;
}

QPushButton#successButton:hover {
    background-color: #4a8a4a;
}

QPushButton#dangerButton {
    background-color: #8b3a3a;
    border-color: #9b4a4a;
}

QPushButton#dangerButton:hover {
    background-color: #9b4a4a;
}

/* ===== ScrollArea ===== */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 14px;
}

QScrollBar::handle:vertical {
    background-color: #5c6265;
    border-radius: 7px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6c7275;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #2b2b2b;
    height: 14px;
}

QScrollBar::handle:horizontal {
    background-color: #5c6265;
    border-radius: 7px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #6c7275;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ===== Splitter ===== */
QSplitter::handle {
    background-color: #3c3f41;
    width: 3px;
}

QSplitter::handle:horizontal {
    width: 3px;
}

QSplitter::handle:vertical {
    height: 3px;
}

/* ===== GroupBox ===== */
QGroupBox {
    background-color: #323232;
    border: 1px solid #5c6265;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 12px;
    font-weight: bold;
    color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    top: 0px;
    padding: 0 6px;
    color: #ffffff;
}

/* ===== Labels ===== */
QLabel {
    color: #ffffff;
    background-color: transparent;
}

QLabel#titleLabel {
    font-size: 16px;
    font-weight: bold;
    color: #ffffff;
}

/* ===== LineEdit ===== */
QLineEdit {
    background-color: #1e1e1e;
    border: 1px solid #5c6265;
    border-radius: 3px;
    padding: 5px 8px;
    color: #ffffff;
    selection-background-color: #365880;
    selection-color: #ffffff;
}

QLineEdit:focus {
    border-color: #365880;
}

QLineEdit:disabled {
    background-color: #2b2b2b;
    color: #777777;
}

/* ===== SpinBox ===== */
QSpinBox, QDoubleSpinBox {
    background-color: #1e1e1e;
    border: 1px solid #5c6265;
    border-radius: 3px;
    padding: 4px 6px;
    color: #ffffff;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #365880;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #3c3f41;
    border: 1px solid #5c6265;
    width: 16px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #4c5052;
}

/* ===== ComboBox ===== */
QComboBox {
    background-color: #1e1e1e;
    border: 1px solid #5c6265;
    border-radius: 3px;
    padding: 5px 8px;
    color: #ffffff;
}

QComboBox:focus {
    border-color: #365880;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #ffffff;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #2b2b2b;
    border: 1px solid #5c6265;
    selection-background-color: #3c3f41;
    selection-color: #ffffff;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 4px 8px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #3c3f41;
}

/* ===== CheckBox ===== */
QCheckBox {
    color: #ffffff;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #5c6265;
    background-color: #1e1e1e;
}

QCheckBox::indicator:checked {
    background-color: #365880;
    border-color: #365880;
}

QCheckBox::indicator:hover {
    border-color: #365880;
}

/* ===== Menu ===== */
QMenu {
    background-color: #2b2b2b;
    border: 1px solid #5c6265;
    padding: 4px;
}

QMenu::item {
    padding: 6px 12px;
    border-radius: 3px;
    color: #ffffff;
}

QMenu::item:selected {
    background-color: #3c3f41;
}

QMenu::separator {
    height: 1px;
    background-color: #5c6265;
    margin: 4px 0;
}

/* ===== Dialog ===== */
QDialog {
    background-color: #2b2b2b;
}

QMessageBox {
    background-color: #2b2b2b;
}

QMessageBox QLabel {
    color: #ffffff;
}

/* ===== ToolTip ===== */
QToolTip {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #5c6265;
    padding: 4px 8px;
}

/* ===== TabWidget ===== */
QTabWidget::pane {
    background-color: #323232;
    border: 1px solid #5c6265;
    border-radius: 4px;
    padding: 8px;
}

QTabBar::tab {
    background-color: #2b2b2b;
    border: 1px solid #5c6265;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 6px 12px;
    margin-right: 2px;
    color: #bbbbbb;
}

QTabBar::tab:selected {
    background-color: #323232;
    color: #ffffff;
}

QTabBar::tab:hover {
    background-color: #3c3f41;
}

/* ===== ListWidget ===== */
QListWidget {
    background-color: #1e1e1e;
    border: 1px solid #5c6265;
    border-radius: 4px;
    outline: none;
    padding: 2px;
}

QListWidget::item {
    padding: 4px 8px;
    border-radius: 3px;
    margin: 1px 0;
}

QListWidget::item:selected {
    background-color: #365880;
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: #3c3f41;
}

/* ===== Frame ===== */
QFrame {
    background-color: transparent;
}

QFrame#taskRowFrame {
    background-color: #323232;
    border: 1px solid #5c6265;
    border-radius: 6px;
}

QFrame#actionChipFrame {
    background-color: #3c3f41;
    border: 1px solid #5c6265;
    border-radius: 4px;
}

QFrame#actionChipFrame:hover {
    background-color: #4c5052;
    border-color: #6c7275;
}
"""

# ===== Светлая тема =====
PROFESSIONAL_LIGHT_STYLESHEET = """
/* ===== Глобальные стили ===== */
* {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

QMainWindow {
    background-color: #f5f5f5;
}

QWidget {
    background-color: #f5f5f5;
    color: #333333;
    font-size: 13px;
}

/* ===== Toolbar ===== */
QToolBar {
    background-color: #e8e8e8;
    border-bottom: 1px solid #cccccc;
    padding: 4px;
    spacing: 4px;
}

QToolBar QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 6px 12px;
    color: #333333;
}

QToolBar QToolButton:hover {
    background-color: #d8d8d8;
    border-color: #cccccc;
}

QToolBar QToolButton:pressed {
    background-color: #cccccc;
}

/* ===== Status Bar ===== */
QStatusBar {
    background-color: #e8e8e8;
    border-top: 1px solid #cccccc;
    color: #666666;
}

/* ===== Кнопки ===== */
QPushButton {
    background-color: #e0e0e0;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px 16px;
    color: #333333;
}

QPushButton:hover {
    background-color: #d0d0d0;
}

QPushButton:pressed {
    background-color: #c0c0c0;
}

/* Акцентные кнопки */
QPushButton#primaryButton {
    background-color: #4a90d9;
    border-color: #3a7bc8;
    color: #ffffff;
}

QPushButton#primaryButton:hover {
    background-color: #5a9fe9;
}

QPushButton#successButton {
    background-color: #4caf50;
    border-color: #3d8b40;
    color: #ffffff;
}

QPushButton#successButton:hover {
    background-color: #5ebc5f;
}

QPushButton#dangerButton {
    background-color: #d32f2f;
    border-color: #b71c1c;
    color: #ffffff;
}

QPushButton#dangerButton:hover {
    background-color: #e53935;
}
"""


def get_stylesheet(theme: str = "dark") -> str:
    """Получить stylesheet по теме"""
    if theme == "light":
        return PROFESSIONAL_LIGHT_STYLESHEET
    return PROFESSIONAL_DARK_STYLESHEET
