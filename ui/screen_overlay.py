"""
Экранный оверлей для захвата координат и визуализации
"""
import logging

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont

from backend import BackendApplication

logger = logging.getLogger(__name__)


class ScreenOverlay(QWidget):
    """Прозрачный оверлей на весь экран"""

    def __init__(self, backend: BackendApplication, interactive: bool = True):
        super().__init__()
        self.backend = backend
        self.interactive = interactive

        # Настройка окна на весь экран
        flags = (
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        if not self.interactive:
            flags |= getattr(Qt.WindowType, "WindowTransparentForInput", Qt.WindowType(0))
            flags |= getattr(Qt.WindowType, "WindowDoesNotAcceptFocus", Qt.WindowType(0))
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        if not self.interactive:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Получаем размер экрана безопасно
        try:
            screen = self.screen()
            if screen:
                self.setGeometry(screen.geometry())
            else:
                # Если экран не найден, используем первый монитор
                from PyQt6.QtGui import QGuiApplication
                self.setGeometry(QGuiApplication.primaryScreen().geometry())
        except Exception as e:
            logger.exception("Ошибка получения размера экрана")
            # Устанавливаем разумный размер по умолчанию
            self.setGeometry(0, 0, 1920, 1080)

        # Состояние
        self.mouse_pos = QPoint(0, 0)
        self.is_capturing = True

        # Таймер обновления
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_mouse_pos)
        self.update_timer.start(50)  # 50ms
    
    def _update_mouse_pos(self):
        """Обновить позицию мыши"""
        try:
            pos = self.backend.mouse.get_position()
            self.mouse_pos = self.mapFromGlobal(QPoint(pos.x, pos.y))
            self.update()  # Перерисовать
        except Exception as e:
            logger.exception("Ошибка обновления позиции мыши")
    
    def paintEvent(self, event):
        """Отрисовка оверлея"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Полупрозрачный фон
        painter.fillRect(self.rect(), QColor(0, 0, 0, 50))
        
        # Прицел на курсоре
        self._draw_crosshair(painter, self.mouse_pos)
        
        # Информация о координатах
        self._draw_coordinates(painter)
        
        # Сетка (опционально)
        # self._draw_grid(painter)
    
    def _draw_crosshair(self, painter: QPainter, pos: QPoint):
        """Нарисовать прицел"""
        pen = QPen(QColor(255, 0, 0))
        pen.setWidth(2)
        painter.setPen(pen)
        
        size = 20
        
        # Горизонтальная линия
        painter.drawLine(pos.x() - size, pos.y(), pos.x() + size, pos.y())
        
        # Вертикальная линия
        painter.drawLine(pos.x(), pos.y() - size, pos.x(), pos.y() + size)
        
        # Круг вокруг курсора
        painter.setBrush(QBrush(QColor(255, 0, 0, 50)))
        painter.drawEllipse(pos, size, size)
    
    def _draw_coordinates(self, painter: QPainter):
        """Нарисовать координаты"""
        # Панель с координатами
        panel_x = 20
        panel_y = 20
        panel_width = 200
        panel_height = 80
        
        # Фон панели
        painter.setBrush(QBrush(QColor(0, 0, 0, 200)))
        painter.setPen(QPen(QColor(100, 100, 100)))
        painter.drawRoundedRect(panel_x, panel_y, panel_width, panel_height, 10, 10)
        
        # Текст
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Consolas", 14)
        painter.setFont(font)
        
        text_y = panel_y + 30
        painter.drawText(panel_x + 15, text_y, f"X: {self.mouse_pos.x()}")
        painter.drawText(panel_x + 15, text_y + 25, f"Y: {self.mouse_pos.y()}")
        
        # Инструкция
        small_font = QFont("Consolas", 10)
        painter.setFont(small_font)
        painter.setPen(QColor(150, 150, 150))
        painter.drawText(panel_x + 15, text_y + 50, "Нажмите ESC для выхода")
    
    def _draw_grid(self, painter: QPainter):
        """Нарисовать сетку"""
        pen = QPen(QColor(255, 255, 255, 30))
        pen.setWidth(1)
        painter.setPen(pen)
        
        grid_size = 100
        
        # Вертикальные линии
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        
        # Горизонтальные линии
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)
    
    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        if not self.interactive:
            return
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_Space:
            # Зафиксировать координаты
            self._capture_coordinates()
    
    def mousePressEvent(self, event):
        """Обработка кликов мыши"""
        if not self.interactive:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._capture_coordinates()
            self.close()
    
    def _capture_coordinates(self):
        """Захватить координаты"""
        try:
            pos = self.backend.mouse.get_position()
            print(f"Захвачены координаты: {pos.x}, {pos.y}")
        except Exception as e:
            logger.exception("Ошибка захвата координат")
    
    def showEvent(self, event):
        """При показе окна"""
        if self.interactive:
            self.activateWindow()
            self.setFocus()
    
    def closeEvent(self, event):
        """При закрытии"""
        try:
            self.update_timer.stop()
        except Exception as e:
            logger.exception("Ошибка при закрытии оверлея")
        finally:
            event.accept()
