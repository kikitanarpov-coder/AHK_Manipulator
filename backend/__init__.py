"""
Бэкенд пакет AHK Manipulator
"""

from backend.core import (
    # Конфигурация
    CONFIG,
    
    # Типы
    ActionType,
    
    # Модели
    Coordinates,
    Color,
    Action,
    TaskRow,
    TaskBoard,
    
    # Результаты
    ExecutionResult,
    
    # Интерфейсы
    IMouseService,
    IKeyboardService,
    IScreenService,
    IDatabaseService,
    
    # Обработчики
    BaseActionHandler,
    MouseClickHandler,
    MouseMoveHandler,
    KeyPressHandler,
    WaitTimeHandler,
    WaitPixelColorHandler,
    WaitPixelChangeHandler,
    WaitImageHandler,
    WaitTextHandler,
    ConditionalHandler,
    LoopHandler,
    ScreenshotHandler,
    LogHandler,
    
    # Реестр и движок
    ActionHandlerRegistry,
    ExecutionEngine,
    
    # Приложение
    BackendApplication,
)

from backend.services import (
    MouseService,
    KeyboardService,
    ScreenService,
    DatabaseService,
)

from backend.export import ActionExporter

from backend.parser import ActionImporter
from backend.ahk_integration import (
    AhkCommand,
    AhkFunction,
    AhkScript,
    AhkDiagnostic,
    AhkValidationResult,
    AhkExecutionResult,
    AhkV2Parser,
    AhkValidator,
    AhkToBoardTranslator,
    AhkRunner,
)

__all__ = [
    # Конфигурация
    'CONFIG',
    
    # Типы
    'ActionType',
    
    # Модели
    'Coordinates',
    'Color',
    'Action',
    'TaskRow',
    'TaskBoard',
    
    # Результаты
    'ExecutionResult',
    
    # Интерфейсы
    'IMouseService',
    'IKeyboardService',
    'IScreenService',
    'IDatabaseService',
    
    # Обработчики
    'BaseActionHandler',
    'MouseClickHandler',
    'MouseMoveHandler',
    'KeyPressHandler',
    'WaitTimeHandler',
    'WaitPixelColorHandler',
    'WaitPixelChangeHandler',
    'WaitImageHandler',
    'WaitTextHandler',
    'ConditionalHandler',
    'LoopHandler',
    'ScreenshotHandler',
    'LogHandler',
    
    # Реестр и движок
    'ActionHandlerRegistry',
    'ExecutionEngine',
    
    # Приложение
    'BackendApplication',
    
    # Сервисы
    'MouseService',
    'KeyboardService',
    'ScreenService',
    'DatabaseService',
    
    # Экспорт/Импорт
    'ActionExporter',
    'ActionImporter',

    # AHK v2 integration
    'AhkCommand',
    'AhkFunction',
    'AhkScript',
    'AhkDiagnostic',
    'AhkValidationResult',
    'AhkExecutionResult',
    'AhkV2Parser',
    'AhkValidator',
    'AhkToBoardTranslator',
    'AhkRunner',
]
