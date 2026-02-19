"""
Бэкенд ядро приложения AHK Manipulator
Чистая логика без зависимостей от UI
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
import asyncio
import json
import os
import uuid
from pathlib import Path


# =============================================================================
# КОНФИГУРАЦИЯ
# =============================================================================

CONFIG = {
    "app_name": "AHK Manipulator",
    "version": "0.3.0",
    "default_delay_ms": 1000,
    "pixel_check_interval_ms": 100,
    "mouse_poll_interval_ms": 50,
}


# =============================================================================
# ТИПЫ ДЕЙСТВИЙ
# =============================================================================

class ActionType(Enum):
    """Типы действий"""
    MOUSE_CLICK = auto()
    MOUSE_MOVE = auto()
    KEY_PRESS = auto()
    WAIT_TIME = auto()
    WAIT_PIXEL_COLOR = auto()
    WAIT_PIXEL_CHANGE = auto()
    WAIT_IMAGE = auto()
    WAIT_TEXT = auto()
    CONDITIONAL = auto()
    LOOP = auto()
    SCREENSHOT = auto()
    LOG = auto()
    DB_SEARCH = auto()
    DB_GET_VALUE = auto()
    DB_ITERATE = auto()
    DB_SAVE = auto()
    CHECK_VALUE = auto()
    RUN_ROW = auto()


# =============================================================================
# МОДЕЛИ ДАННЫХ
# =============================================================================

@dataclass
class Coordinates:
    """Координаты на экране"""
    x: int
    y: int

    def to_tuple(self) -> tuple[int, int]:
        return (self.x, self.y)

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: dict) -> 'Coordinates':
        return cls(x=data.get("x", 0), y=data.get("y", 0))


@dataclass
class Color:
    """Цвет пикселя"""
    r: int
    g: int
    b: int
    tolerance: int = 10

    def matches(self, other: 'Color') -> bool:
        return (abs(self.r - other.r) <= self.tolerance and
                abs(self.g - other.g) <= self.tolerance and
                abs(self.b - other.b) <= self.tolerance)

    def to_dict(self) -> dict:
        return {"r": self.r, "g": self.g, "b": self.b, "tolerance": self.tolerance}


@dataclass
class Action:
    """Действие"""
    id: str
    action_type: ActionType
    name: str
    enabled: bool = True
    delay_before_ms: int = 0
    delay_after_ms: int = 0
    repeat_count: int = 1
    coordinates: Optional[Coordinates] = None
    color: Optional[Color] = None
    key: Optional[str] = None
    mouse_button: str = "left"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action_type": self.action_type.name,
            "name": self.name,
            "enabled": self.enabled,
            "delay_before_ms": self.delay_before_ms,
            "delay_after_ms": self.delay_after_ms,
            "repeat_count": self.repeat_count,
            "coordinates": self.coordinates.to_dict() if self.coordinates else None,
            "color": self.color.to_dict() if self.color else None,
            "mouse_button": self.mouse_button,
            "key": self.key,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Action':
        action_type_name = data.get("action_type", "MOUSE_CLICK")
        try:
            action_type = ActionType[action_type_name]
        except KeyError:
            action_type = ActionType.MOUSE_CLICK

        return cls(
            id=data.get("id", ""),
            action_type=action_type,
            name=data.get("name", ""),
            enabled=data.get("enabled", True),
            delay_before_ms=data.get("delay_before_ms", 0),
            delay_after_ms=data.get("delay_after_ms", 0),
            repeat_count=data.get("repeat_count", 1),
            coordinates=Coordinates.from_dict(data["coordinates"]) if data.get("coordinates") else None,
            color=Color(**data["color"]) if data.get("color") else None,
            mouse_button=data.get("mouse_button", "left"),
            key=data.get("key"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TaskRow:
    """Строка task-доски"""
    id: str
    name: str
    actions: List[Action] = field(default_factory=list)
    enabled: bool = True

    def add_action(self, action: Action) -> None:
        self.actions.append(action)

    def remove_action(self, action_id: str) -> bool:
        for i, action in enumerate(self.actions):
            if action.id == action_id:
                self.actions.pop(i)
                return True
        return False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "actions": [a.to_dict() for a in self.actions]
        }


@dataclass
class TaskBoard:
    """Task-доска"""
    id: str
    name: str
    rows: List[TaskRow] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)

    def add_row(self, row: TaskRow) -> None:
        self.rows.append(row)

    def remove_row(self, row_id: str) -> bool:
        for i, row in enumerate(self.rows):
            if row.id == row_id:
                self.rows.pop(i)
                return True
        return False

    def get_all_actions(self) -> List[Action]:
        actions = []
        for row in self.rows:
            if row.enabled:
                actions.extend([a for a in row.actions if a.enabled])
        return actions

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "rows": [row.to_dict() for row in self.rows]
        }


# =============================================================================
# РЕЗУЛЬТАТЫ ВЫПОЛНЕНИЯ
# =============================================================================

@dataclass
class ExecutionResult:
    """Результат выполнения действия"""
    success: bool
    action_id: str
    action_name: str
    message: str = ""
    error: Optional[str] = None

    def __str__(self) -> str:
        status = "✓" if self.success else "✗"
        return f"{status} {self.action_name}: {self.message or self.error}"


# =============================================================================
# АБСТРАКТНЫЕ ИНТЕРФЕЙСЫ (Ports)
# =============================================================================

class IMouseService(ABC):
    """Интерфейс сервиса мыши"""

    @abstractmethod
    def get_position(self) -> Coordinates:
        pass

    @abstractmethod
    def move_to(self, x: int, y: int, duration_ms: int = 0) -> None:
        pass

    @abstractmethod
    def click(self, button: str = "left") -> None:
        pass


class IKeyboardService(ABC):
    """Интерфейс сервиса клавиатуры"""

    @abstractmethod
    def press(self, key: str) -> None:
        pass

    @abstractmethod
    def press_hotkey(self, keys: List[str]) -> None:
        pass


class IScreenService(ABC):
    """Интерфейс сервиса экрана"""

    @abstractmethod
    def get_pixel_color(self, x: int, y: int) -> Optional[Color]:
        pass

    @abstractmethod
    def take_screenshot(self, region: Optional[tuple] = None) -> Optional[str]:
        pass

    @abstractmethod
    def find_image(self, image_path: str, confidence: float = 0.9) -> Optional[Coordinates]:
        pass


class IDatabaseService(ABC):
    """Интерфейс сервиса баз данных"""

    @abstractmethod
    def search(self, db_name: str, column: str, value: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_columns(self, db_name: str) -> List[str]:
        pass


# =============================================================================
# ОБРАБОТЧИКИ ДЕЙСТВИЙ (Action Handlers)
# =============================================================================

class BaseActionHandler(ABC):
    """Базовый класс обработчика действий"""

    def __init__(self, mouse: IMouseService = None,
                 keyboard: IKeyboardService = None,
                 screen: IScreenService = None,
                 database: IDatabaseService = None):
        self.mouse = mouse
        self.keyboard = keyboard
        self.screen = screen
        self.database = database
        self.variables: Dict[str, Any] = {}
        self.registry: Optional['ActionHandlerRegistry'] = None

    @abstractmethod
    async def execute(self, action: Action) -> ExecutionResult:
        """Выполнить действие"""
        pass

    def _substitute_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """Подставить переменные в текст"""
        if not text:
            return text
        result = text
        for var_name, var_value in variables.items():
            result = result.replace(f'{{{var_name}}}', str(var_value))
        return result


class MouseClickHandler(BaseActionHandler):
    """Обработчик MOUSE_CLICK"""

    async def execute(self, action: Action) -> ExecutionResult:
        try:
            if not self.mouse:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error="Сервис мыши не инициализирован"
                )

            if not action.coordinates:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error="Не указаны координаты"
                )

            # Перемещение и клик
            self.mouse.move_to(action.coordinates.x, action.coordinates.y)
            self.mouse.click(action.mouse_button)

            return ExecutionResult(
                success=True, action_id=action.id, action_name=action.name,
                message=f"Клик {action.mouse_button} в ({action.coordinates.x}, {action.coordinates.y})"
            )
        except Exception as e:
            return ExecutionResult(
                success=False, action_id=action.id, action_name=action.name,
                error=f"Ошибка: {str(e)}"
            )


class MouseMoveHandler(BaseActionHandler):
    """Обработчик MOUSE_MOVE"""

    async def execute(self, action: Action) -> ExecutionResult:
        try:
            if not self.mouse:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error="Сервис мыши не инициализирован"
                )

            if not action.coordinates:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error="Не указаны координаты"
                )

            duration = action.metadata.get('move_duration_ms', 0)
            self.mouse.move_to(action.coordinates.x, action.coordinates.y, duration)

            return ExecutionResult(
                success=True, action_id=action.id, action_name=action.name,
                message=f"Перемещение в ({action.coordinates.x}, {action.coordinates.y})"
            )
        except Exception as e:
            return ExecutionResult(
                success=False, action_id=action.id, action_name=action.name,
                error=f"Ошибка: {str(e)}"
            )


class KeyPressHandler(BaseActionHandler):
    """Обработчик KEY_PRESS"""

    async def execute(self, action: Action) -> ExecutionResult:
        try:
            if not self.keyboard:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error="Сервис клавиатуры не инициализирован"
                )

            if not action.key:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error="Не указана клавиша"
                )

            self.keyboard.press(action.key)

            return ExecutionResult(
                success=True, action_id=action.id, action_name=action.name,
                message=f"Нажатие клавиши: {action.key}"
            )
        except Exception as e:
            return ExecutionResult(
                success=False, action_id=action.id, action_name=action.name,
                error=f"Ошибка: {str(e)}"
            )


class WaitTimeHandler(BaseActionHandler):
    """Обработчик WAIT_TIME"""

    async def execute(self, action: Action) -> ExecutionResult:
        try:
            delay = action.delay_before_ms or action.metadata.get('wait_ms', CONFIG["default_delay_ms"])
            await asyncio.sleep(delay / 1000)

            return ExecutionResult(
                success=True, action_id=action.id, action_name=action.name,
                message=f"Ожидание {delay}мс"
            )
        except Exception as e:
            return ExecutionResult(
                success=False, action_id=action.id, action_name=action.name,
                error=f"Ошибка: {str(e)}"
            )


class WaitPixelColorHandler(BaseActionHandler):
    """Обработчик WAIT_PIXEL_COLOR"""

    async def execute(self, action: Action) -> ExecutionResult:
        if not self.screen:
            return ExecutionResult(False, action.id, action.name, error="Сервис экрана не инициализирован")
        if not action.coordinates:
            return ExecutionResult(False, action.id, action.name, error="Не указаны координаты")

        timeout_ms = int(action.metadata.get("timeout_ms", 5000))
        interval_ms = int(action.metadata.get("check_interval_ms", CONFIG["pixel_check_interval_ms"]))
        any_change = bool(action.metadata.get("any_change", False))

        if any_change:
            initial = self.screen.get_pixel_color(action.coordinates.x, action.coordinates.y)
            if not initial:
                return ExecutionResult(False, action.id, action.name, error="Не удалось прочитать стартовый цвет")
            target_color = None
        else:
            target_color = action.color or Color(
                r=int(action.metadata.get("color_r", 0)),
                g=int(action.metadata.get("color_g", 0)),
                b=int(action.metadata.get("color_b", 0)),
                tolerance=int(action.metadata.get("tolerance", 10)),
            )
            initial = None

        loop = asyncio.get_running_loop()
        start = loop.time()
        while (loop.time() - start) * 1000 <= timeout_ms:
            current = self.screen.get_pixel_color(action.coordinates.x, action.coordinates.y)
            if current:
                if any_change and initial and not initial.matches(current):
                    return ExecutionResult(True, action.id, action.name, message="Обнаружено изменение пикселя")
                if target_color and target_color.matches(current):
                    return ExecutionResult(True, action.id, action.name, message="Целевой цвет обнаружен")
            await asyncio.sleep(max(interval_ms, 1) / 1000)

        return ExecutionResult(False, action.id, action.name, message="Таймаут ожидания цвета")


class WaitPixelChangeHandler(BaseActionHandler):
    """Обработчик WAIT_PIXEL_CHANGE"""

    async def execute(self, action: Action) -> ExecutionResult:
        if not self.screen:
            return ExecutionResult(False, action.id, action.name, error="Сервис экрана не инициализирован")
        if not action.coordinates:
            return ExecutionResult(False, action.id, action.name, error="Не указаны координаты")

        timeout_ms = int(action.metadata.get("timeout_ms", 5000))
        interval_ms = int(action.metadata.get("check_interval_ms", CONFIG["pixel_check_interval_ms"]))
        initial = self.screen.get_pixel_color(action.coordinates.x, action.coordinates.y)
        if not initial:
            return ExecutionResult(False, action.id, action.name, error="Не удалось прочитать стартовый цвет")

        loop = asyncio.get_running_loop()
        start = loop.time()
        while (loop.time() - start) * 1000 <= timeout_ms:
            current = self.screen.get_pixel_color(action.coordinates.x, action.coordinates.y)
            if current and not initial.matches(current):
                return ExecutionResult(True, action.id, action.name, message="Пиксель изменился")
            await asyncio.sleep(max(interval_ms, 1) / 1000)

        return ExecutionResult(False, action.id, action.name, message="Таймаут ожидания изменения пикселя")


class WaitImageHandler(BaseActionHandler):
    """Обработчик WAIT_IMAGE"""

    async def execute(self, action: Action) -> ExecutionResult:
        if not self.screen:
            return ExecutionResult(False, action.id, action.name, error="Сервис экрана не инициализирован")

        image_path = str(action.metadata.get("image_path", "")).strip()
        if not image_path:
            return ExecutionResult(False, action.id, action.name, error="Не указан путь к изображению")

        confidence = float(action.metadata.get("confidence", 0.9))
        timeout_ms = int(action.metadata.get("timeout_ms", 5000))
        interval_ms = int(action.metadata.get("check_interval_ms", CONFIG["pixel_check_interval_ms"]))

        loop = asyncio.get_running_loop()
        start = loop.time()
        while (loop.time() - start) * 1000 <= timeout_ms:
            found = self.screen.find_image(image_path, confidence)
            if found:
                self.variables["last_image_x"] = found.x
                self.variables["last_image_y"] = found.y
                return ExecutionResult(
                    True, action.id, action.name,
                    message=f"Изображение найдено в ({found.x}, {found.y})"
                )
            await asyncio.sleep(max(interval_ms, 1) / 1000)

        return ExecutionResult(False, action.id, action.name, message="Таймаут ожидания изображения")


class WaitTextHandler(BaseActionHandler):
    """Обработчик WAIT_TEXT (OCR заглушка с явным контрактом)"""

    async def execute(self, action: Action) -> ExecutionResult:
        expected = str(action.metadata.get("search_text", "")).strip()
        text_source = str(self.variables.get("ocr_text", ""))
        if expected and expected in text_source:
            return ExecutionResult(True, action.id, action.name, message="Текст найден в ocr_text")
        return ExecutionResult(
            False, action.id, action.name,
            message="WAIT_TEXT требует OCR-провайдер (не подключен)"
        )


class ConditionalHandler(BaseActionHandler):
    """Обработчик CONDITIONAL"""

    async def execute(self, action: Action) -> ExecutionResult:
        condition_type = action.metadata.get("condition_type", "variable_equals")
        condition_value = action.metadata.get("condition_value", "")
        if_true = action.metadata.get("if_true", "execute_next")
        if_false = action.metadata.get("if_false", "skip_next")

        result = False
        if condition_type == "variable_equals":
            var_name = action.metadata.get("variable_name", "")
            result = str(self.variables.get(var_name, "")) == str(condition_value)
        elif condition_type == "image_exists" and self.screen:
            image_path = action.metadata.get("image_path", "")
            confidence = float(action.metadata.get("confidence", 0.9))
            result = bool(self.screen.find_image(image_path, confidence))
        elif condition_type == "pixel_color" and self.screen and action.coordinates:
            current = self.screen.get_pixel_color(action.coordinates.x, action.coordinates.y)
            target = action.color
            result = bool(current and target and target.matches(current))

        decision = if_true if result else if_false
        if decision == "skip_next":
            self.variables["_skip_next_count"] = int(self.variables.get("_skip_next_count", 0)) + 1
        elif decision == "break":
            self.variables["_break_execution"] = True

        return ExecutionResult(
            True, action.id, action.name,
            message=f"Условие={result}; решение={decision}"
        )


class LoopHandler(BaseActionHandler):
    """Обработчик LOOP"""

    async def execute(self, action: Action) -> ExecutionResult:
        iterations = int(action.metadata.get("iterations", action.repeat_count or 1))
        if iterations < 1:
            iterations = 1
        delay_ms = int(action.metadata.get("delay_ms", 0))

        # LOOP действует как контролируемая пауза N итераций.
        for i in range(iterations):
            self.variables["_loop_index"] = i + 1
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000)

        self.variables["_loop_iterations"] = iterations
        return ExecutionResult(True, action.id, action.name, message=f"Цикл выполнен: {iterations} итераций")


class ScreenshotHandler(BaseActionHandler):
    """Обработчик SCREENSHOT"""

    async def execute(self, action: Action) -> ExecutionResult:
        if not self.screen:
            return ExecutionResult(False, action.id, action.name, error="Сервис экрана не инициализирован")

        rx = int(action.metadata.get("region_x", 0))
        ry = int(action.metadata.get("region_y", 0))
        rw = int(action.metadata.get("region_width", 0))
        rh = int(action.metadata.get("region_height", 0))
        region = None if rw <= 0 or rh <= 0 else (rx, ry, rw, rh)
        path = self.screen.take_screenshot(region)
        if not path:
            return ExecutionResult(False, action.id, action.name, message="Не удалось сделать скриншот")

        self.variables["last_screenshot"] = path
        return ExecutionResult(True, action.id, action.name, message=f"Скриншот сохранён: {path}")


class LogHandler(BaseActionHandler):
    """Обработчик LOG"""

    async def execute(self, action: Action) -> ExecutionResult:
        message = action.metadata.get("message", action.name)
        level = str(action.metadata.get("log_level", "INFO")).upper()
        self.variables["last_log_message"] = message
        self.variables["last_log_level"] = level
        return ExecutionResult(True, action.id, action.name, message=f"[{level}] {message}")


# =============================================================================
# РЕЕСТР ОБРАБОТЧИКОВ
# =============================================================================

class ActionHandlerRegistry:
    """Реестр обработчиков действий"""

    def __init__(self, mouse: IMouseService = None,
                 keyboard: IKeyboardService = None,
                 screen: IScreenService = None,
                 database: IDatabaseService = None):
        self._handlers: Dict[ActionType, BaseActionHandler] = {}
        self._register_default_handlers(mouse, keyboard, screen, database)

    def _register_default_handlers(self, mouse, keyboard, screen, database):
        """Регистрация стандартных обработчиков"""
        self._handlers[ActionType.MOUSE_CLICK] = MouseClickHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.MOUSE_MOVE] = MouseMoveHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.KEY_PRESS] = KeyPressHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.WAIT_TIME] = WaitTimeHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.WAIT_PIXEL_COLOR] = WaitPixelColorHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.WAIT_PIXEL_CHANGE] = WaitPixelChangeHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.WAIT_IMAGE] = WaitImageHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.WAIT_TEXT] = WaitTextHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.CONDITIONAL] = ConditionalHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.LOOP] = LoopHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.SCREENSHOT] = ScreenshotHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.LOG] = LogHandler(mouse, keyboard, screen, database)
        
        # Обработчики баз данных
        from backend.db_handlers import (
            DBSearchHandler, DBGetValueHandler, DBIterateHandler,
            DBSaveHandler, CheckValueHandler, RunRowHandler
        )
        
        self._handlers[ActionType.DB_SEARCH] = DBSearchHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.DB_GET_VALUE] = DBGetValueHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.DB_ITERATE] = DBIterateHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.DB_SAVE] = DBSaveHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.CHECK_VALUE] = CheckValueHandler(mouse, keyboard, screen, database)
        self._handlers[ActionType.RUN_ROW] = RunRowHandler(mouse, keyboard, screen, database)

    def get_handler(self, action_type: ActionType) -> Optional[BaseActionHandler]:
        """Получить обработчик для типа действия"""
        return self._handlers.get(action_type)

    def register_handler(self, action_type: ActionType, handler: BaseActionHandler):
        """Зарегистрировать обработчик"""
        self._handlers[action_type] = handler


# =============================================================================
# ИСПОЛНИТЕЛЬ (Execution Engine)
# =============================================================================

class ExecutionEngine:
    """Движок выполнения действий"""

    def __init__(self, registry: ActionHandlerRegistry):
        self.registry = registry
        self.is_running = False
        self.is_paused = False
        self.variables: Dict[str, Any] = {}
        self.results: List[ExecutionResult] = []

    async def execute_action(self, action: Action) -> ExecutionResult:
        """Выполнить одно действие"""
        import time
        
        if not action.enabled:
            return ExecutionResult(
                success=False, action_id=action.id, action_name=action.name,
                message="Действие отключено"
            )

        # Точная задержка перед выполнением
        if action.delay_before_ms > 0:
            await self._precise_sleep(action.delay_before_ms)

        # Получение обработчика
        handler = self.registry.get_handler(action.action_type)
        if not handler:
            return ExecutionResult(
                success=False, action_id=action.id, action_name=action.name,
                error=f"Обработчик для {action.action_type} не найден"
            )

        # Передаём runtime-контекст движка в обработчики.
        handler.variables = self.variables
        handler.registry = self.registry

        # Выполнение и замер времени
        start_time = time.perf_counter()
        result = await handler.execute(action)
        execution_time = (time.perf_counter() - start_time) * 1000
        
        self.results.append(result)

        # Точная задержка после выполнения с компенсацией
        if action.delay_after_ms > 0:
            remaining = action.delay_after_ms - execution_time
            if remaining > 0:
                await self._precise_sleep(remaining)

        return result
    
    async def _precise_sleep(self, ms: float):
        """
        Точный сон с компенсацией
        
        Args:
            ms: Миллисекунды для ожидания
        """
        if ms <= 0:
            return
        # Не блокируем event loop через time.sleep.
        await asyncio.sleep(ms / 1000)

    async def execute_board(self, board: TaskBoard) -> List[ExecutionResult]:
        """Выполнить всю доску"""
        self.is_running = True
        self.results.clear()
        self.variables.clear()
        self.variables['_board'] = board  # Передаём доску для RunRowHandler
        self.variables['_running'] = True

        actions = board.get_all_actions()

        for i, action in enumerate(actions):
            if not self.is_running:
                break

            if self.variables.get("_break_execution"):
                break

            skip_count = int(self.variables.get("_skip_next_count", 0))
            if skip_count > 0:
                self.variables["_skip_next_count"] = skip_count - 1
                continue

            while self.is_paused:
                await asyncio.sleep(0.1)

            result = await self.execute_action(action)

        self.is_running = False
        self.variables['_running'] = False
        return self.results

    def stop(self) -> None:
        """Остановить выполнение"""
        self.is_running = False

    def pause(self) -> None:
        """Пауза"""
        self.is_paused = True

    def resume(self) -> None:
        """Продолжить"""
        self.is_paused = False

    def get_variable(self, name: str) -> Any:
        """Получить переменную"""
        return self.variables.get(name)

    def set_variable(self, name: str, value: Any) -> None:
        """Установить переменную"""
        self.variables[name] = value


# =============================================================================
# ПРИЛОЖЕНИЕ (Application Service)
# =============================================================================

class BackendApplication:
    """Основной сервис приложения (бэкенд)"""
    
    # Импортируем экспорт/импорт здесь чтобы избежать циклического импорта
    from backend.export import ActionExporter as _exporter_class
    from backend.parser import ActionImporter as _importer_class

    def __init__(self, mouse: IMouseService = None,
                 keyboard: IKeyboardService = None,
                 screen: IScreenService = None,
                 database: IDatabaseService = None):
        # Сервисы
        self.mouse = mouse
        self.keyboard = keyboard
        self.screen = screen
        self.database = database

        # Состояние
        self.current_board: Optional[TaskBoard] = None
        self.boards: List[TaskBoard] = []

        # Реестр и движок
        self.registry = ActionHandlerRegistry(mouse, keyboard, screen, database)
        self.engine = ExecutionEngine(self.registry)

        # Базы данных
        self.databases: List[str] = []
        
        # Экспорт/Импорт
        self.exporter = self._exporter_class()
        self.importer = self._importer_class()
        self._ahk_runner = None

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex}"

    def create_board(self, name: str) -> TaskBoard:
        """Создать доску"""
        board = TaskBoard(id=self._new_id("board"), name=name)
        self.boards.append(board)
        self.current_board = board
        return board

    def add_row(self, name: str = "Новая строка") -> TaskRow:
        """Добавить строку"""
        if not self.current_board:
            self.create_board("Без названия")

        row = TaskRow(id=self._new_id("row"), name=name)
        self.current_board.add_row(row)
        return row

    def add_action(self, row_id: str, action: Action) -> None:
        """Добавить действие"""
        if not self.current_board:
            raise ValueError("Нет активной доски")

        for row in self.current_board.rows:
            if row.id == row_id:
                row.add_action(action)
                self.current_board.modified_at = datetime.now()
                return

        raise ValueError(f"Строка {row_id} не найдена")

    async def run_board(self, board: TaskBoard = None) -> List[ExecutionResult]:
        """Запустить доску"""
        board = board or self.current_board
        if not board:
            raise ValueError("Нет активной доски")

        return await self.engine.execute_board(board)

    def stop_execution(self) -> None:
        """Остановить выполнение"""
        self.engine.stop()

    def save_board(self, board: TaskBoard, filepath: str) -> None:
        """Сохранить доску в JSON"""
        path = Path(filepath).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)

        data = board.to_dict()
        data['version'] = CONFIG['version']
        data['app'] = CONFIG['app_name']

        with path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_board(self, filepath: str) -> TaskBoard:
        """Загрузить доску из JSON"""
        path = Path(filepath).expanduser()
        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)

        board = TaskBoard(
            id=data.get('id', 'board_1'),
            name=data.get('name', 'Загруженная доска'),
        )

        for row_data in data.get('rows', []):
            row = TaskRow(
                id=row_data.get('id'),
                name=row_data.get('name'),
                enabled=row_data.get('enabled', True),
            )

            for action_data in row_data.get('actions', []):
                action = Action.from_dict(action_data)
                row.add_action(action)

            board.add_row(row)

        return board

    def export_to_ahk(self, board: TaskBoard, include_comments: bool = True) -> str:
        """Экспорт в AHK скрипт"""
        return self.exporter.export_to_ahk(board, include_comments)
    
    def export_to_python(self, board: TaskBoard, include_imports: bool = True) -> str:
        """Экспорт в Python скрипт"""
        return self.exporter.export_to_python(board, include_imports)
    
    def import_from_ahk(self, ahk_text: str, board_name: str = "Imported Board") -> TaskBoard:
        """Импорт из AHK скрипта"""
        return self.importer.import_from_ahk(ahk_text, board_name)
    
    def import_from_file(self, filepath: str) -> TaskBoard:
        """Импорт из файла (AHK или JSON)"""
        path = Path(filepath).expanduser()
        board = self.importer.import_from_file(filepath)

        # Fallback на расширенный AHK v2 импорт, если legacy-парсер не извлёк действий.
        if path.suffix.lower() == ".ahk" and len(board.get_all_actions()) == 0:
            try:
                runner = self._get_ahk_runner()
                script = runner.parse_file(path)
                translated_board, _ = runner.translator.to_board(script, board_name=path.stem)
                if translated_board and translated_board.get_all_actions():
                    return translated_board
            except Exception:
                pass

        return board

    # ===== AHK v2 Integration =====

    def _get_ahk_runner(self):
        if self._ahk_runner is None:
            from backend.ahk_integration import AhkRunner
            self._ahk_runner = AhkRunner(self)
        return self._ahk_runner

    def parse_ahk_file(self, filepath: str):
        """Распарсить AHK v2 скрипт в структурную модель."""
        return self._get_ahk_runner().parse_file(filepath)

    def validate_ahk_file(self, filepath: str):
        """Валидация AHK v2 скрипта."""
        return self._get_ahk_runner().validate_file(filepath)

    def execute_ahk_file(
        self,
        filepath: str,
        mode: str = "auto",
        timeout_sec: int = 30,
        allowed_root: str | None = None,
    ):
        """Выполнить AHK v2 скрипт (native/emulated)."""
        return self._get_ahk_runner().execute_file(
            filepath=filepath,
            mode=mode,
            timeout_sec=timeout_sec,
            allowed_root=allowed_root,
        )

    def shutdown(self) -> None:
        """Корректно завершить сервисы и выполнение."""
        self.stop_execution()
        for service in (self.mouse, self.keyboard, self.screen, self.database):
            close = getattr(service, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass
