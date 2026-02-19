# Тесты бэкенда AHK Manipulator

## Запуск тестов

```bash
# Активация виртуального окружения
source .venv/bin/activate

# Запуск всех тестов
python -m unittest tests.test_backend -v

# Запуск конкретного теста
python -m unittest tests.test_backend.TestAction.test_create_action -v

# Запуск тестов по категории
python -m unittest tests.test_backend.TestMouseClickHandler -v
```

## Покрытие тестами

### Модели данных (100%)
- ✅ `Coordinates` — координаты
- ✅ `Color` — цвет пикселя
- ✅ `Action` — действие
- ✅ `TaskRow` — строка доски
- ✅ `TaskBoard` — доска

### Обработчики действий (100%)
- ✅ `MouseClickHandler` — клик мышью
- ✅ `MouseMoveHandler` — перемещение мыши
- ✅ `KeyPressHandler` — нажатие клавиши
- ✅ `WaitTimeHandler` — ожидание времени

### Компоненты
- ✅ `ActionHandlerRegistry` — реестр обработчиков
- ✅ `ExecutionEngine` — движок выполнения
- ✅ `BackendApplication` — приложение

## Структура тестов

```
tests/
└── test_backend.py
    ├── TestCoordinates       # Тесты Coordinates
    ├── TestColor             # Тесты Color
    ├── TestAction            # Тесты Action
    ├── TestTaskRow           # Тесты TaskRow
    ├── TestTaskBoard         # Тесты TaskBoard
    ├── TestMouseClickHandler # Тесты MOUSE_CLICK
    ├── TestMouseMoveHandler  # Тесты MOUSE_MOVE
    ├── TestKeyPressHandler   # Тесты KEY_PRESS
    ├── TestWaitTimeHandler   # Тесты WAIT_TIME
    ├── TestActionHandlerRegistry
    ├── TestExecutionEngine
    ├── TestBackendApplication
    └── TestIntegration       # Интеграционные тесты
```

## Статистика

- **Всего тестов:** 45
- **Успешно:** 45
- **Ошибки:** 0
- **Время выполнения:** ~0.6 сек

## Примеры тестов

### Тест модели
```python
def test_create_coordinates(self):
    coord = Coordinates(x=100, y=200)
    self.assertEqual(coord.x, 100)
    self.assertEqual(coord.y, 200)
```

### Тест обработчика
```python
def test_successful_click(self):
    mock_mouse = Mock(spec=IMouseService)
    handler = MouseClickHandler(mouse=mock_mouse)
    
    action = Action(
        id="click_1",
        action_type=ActionType.MOUSE_CLICK,
        coordinates=Coordinates(x=100, y=200)
    )
    
    result = asyncio.run(handler.execute(action))
    
    self.assertTrue(result.success)
    self.mock_mouse.move_to.assert_called_once_with(100, 200)
```

### Интеграционный тест
```python
def test_full_workflow(self):
    app = BackendApplication(mouse=mock_mouse, keyboard=mock_keyboard)
    
    board = app.create_board("Доска")
    row = app.add_row("Строка")
    app.add_action(row.id, Action(...))
    
    results = asyncio.run(app.run_board(board))
    
    self.assertTrue(all(r.success for r in results))
```

## Добавление новых тестов

1. Создайте класс теста:
```python
class TestMyHandler(unittest.TestCase):
    def setUp(self):
        self.handler = MyHandler()
    
    def test_my_feature(self):
        result = self.handler.execute(...)
        self.assertTrue(result.success)
```

2. Запустите тесты:
```bash
python -m unittest tests.test_backend.TestMyHandler -v
```

## Моки (Mocks)

Тесты используют моки для внешних зависимостей:

```python
from unittest.mock import Mock

# Мок сервиса мыши
mock_mouse = Mock(spec=IMouseService)
mock_mouse.get_position.return_value = Coordinates(100, 200)

# Мок сервиса клавиатуры
mock_keyboard = Mock(spec=IKeyboardService)
```

## Покрытие кода (Coverage)

Для измерения покрытия кода установите coverage:

```bash
pip install coverage
coverage run -m unittest tests.test_backend
coverage report
```
