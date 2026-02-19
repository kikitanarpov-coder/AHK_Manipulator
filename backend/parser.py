"""
Модуль импорта действий из различных форматов
"""

import re
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from backend.core import TaskBoard, TaskRow, Action, ActionType, Coordinates


class ActionImporter:
    """Импорт действий из различных форматов"""
    
    # Паттерны для парсинга AHK v2
    AHK_PATTERNS = {
        ActionType.MOUSE_CLICK: r'Click,\s*(\w+)?,?\s*(\d+)?,?\s*(\d+)?',
        ActionType.MOUSE_MOVE: r'MouseMove,\s*(\d+),\s*(\d+)',
        ActionType.KEY_PRESS: r'Send,\s*\{([^}]+)\}',
        ActionType.WAIT_TIME: r'Sleep,\s*(\d+)',
        ActionType.LOOP: r'Loop,\s*(\d+)',
    }
    
    # Маппинг AHK клавиш на внутренние
    AHK_KEY_MAP = {
        "LButton": "left",
        "RButton": "right",
        "MButton": "middle",
        "Enter": "enter",
        "Tab": "tab",
        "Space": "space",
        "BackSpace": "backspace",
        "Delete": "delete",
        "Home": "home",
        "End": "end",
        "PgUp": "pageup",
        "PgDn": "pagedown",
        "Up": "up",
        "Down": "down",
        "Left": "left",
        "Right": "right",
        "F1": "f1",
        "F2": "f2",
        "F3": "f3",
        "F4": "f4",
        "F5": "f5",
        "F6": "f6",
        "F7": "f7",
        "F8": "f8",
        "F9": "f9",
        "F10": "f10",
        "F11": "f11",
        "F12": "f12",
        "^": "ctrl",
        "+": "shift",
        "!": "alt",
        "#": "win",
    }
    
    def __init__(self):
        self.current_row_id = 0
    
    def import_from_ahk(self, ahk_text: str, board_name: str = "Imported Board") -> TaskBoard:
        """
        Импорт из AHK скрипта
        
        Args:
            ahk_text: Текст AHK скрипта
            board_name: Имя доски
        
        Returns:
            TaskBoard с импортированными действиями
        """
        board = TaskBoard(
            id=f"imported_{datetime.now().timestamp()}",
            name=board_name
        )
        
        row = TaskRow(
            id=f"row_{self.current_row_id}",
            name="Imported Row"
        )
        board.add_row(row)
        self.current_row_id += 1
        
        # Парсим по строкам
        for line in ahk_text.split('\n'):
            line = line.strip()
            
            # Пропускаем комментарии и пустые строки
            if not line or line.startswith(';') or line.startswith('#'):
                continue
            
            # Пытаемся распознать команду
            action = self._parse_ahk_line(line)
            if action:
                row.add_action(action)
        
        return board
    
    def _parse_ahk_line(self, line: str) -> Optional[Action]:
        """Распарсить одну строку AHK"""
        import uuid
        
        for action_type, pattern in self.AHK_PATTERNS.items():
            match = re.match(pattern, line, re.IGNORECASE)
            
            if match:
                groups = match.groups()
                
                if action_type == ActionType.MOUSE_CLICK:
                    return Action(
                        id=str(uuid.uuid4()),
                        action_type=action_type,
                        name="AHK Click",
                        mouse_button=groups[0] or "left",
                        coordinates=Coordinates(
                            x=int(groups[1]) if groups[1] else 0,
                            y=int(groups[2]) if groups[2] else 0
                        )
                    )
                
                elif action_type == ActionType.MOUSE_MOVE:
                    return Action(
                        id=str(uuid.uuid4()),
                        action_type=action_type,
                        name="AHK Move",
                        coordinates=Coordinates(
                            x=int(groups[0]),
                            y=int(groups[1])
                        )
                    )
                
                elif action_type == ActionType.KEY_PRESS:
                    key = self._map_ahk_key(groups[0])
                    return Action(
                        id=str(uuid.uuid4()),
                        action_type=action_type,
                        name=f"AHK Key: {key}",
                        key=key
                    )
                
                elif action_type == ActionType.WAIT_TIME:
                    return Action(
                        id=str(uuid.uuid4()),
                        action_type=action_type,
                        name="AHK Wait",
                        delay_before_ms=int(groups[0])
                    )
                
                elif action_type == ActionType.LOOP:
                    return Action(
                        id=str(uuid.uuid4()),
                        action_type=action_type,
                        name="AHK Loop",
                        metadata={"iterations": int(groups[0])}
                    )
        
        return None
    
    def _map_ahk_key(self, ahk_key: str) -> str:
        """Преобразовать AHK клавишу во внутреннее представление"""
        # Проверяем маппинг
        if ahk_key in self.AHK_KEY_MAP:
            return self.AHK_KEY_MAP[ahk_key]
        
        # Модификаторы
        result = ""
        for char in ahk_key:
            if char in self.AHK_KEY_MAP:
                result += self.AHK_KEY_MAP[char] + "+"
            else:
                result += char.lower()
        
        return result.rstrip('+')
    
    def import_from_json(self, json_data: Dict[str, Any]) -> TaskBoard:
        """
        Импорт из JSON
        
        Args:
            json_data: Словарь с данными
        
        Returns:
            TaskBoard
        """
        board = TaskBoard(
            id=json_data.get("id", f"imported_{datetime.now().timestamp()}"),
            name=json_data.get("name", "Imported Board")
        )
        
        for row_data in json_data.get("rows", []):
            row = TaskRow(
                id=row_data.get("id", f"row_{self.current_row_id}"),
                name=row_data.get("name", "Row"),
                enabled=row_data.get("enabled", True)
            )
            
            for action_data in row_data.get("actions", []):
                action = Action.from_dict(action_data)
                row.add_action(action)
            
            board.add_row(row)
        
        return board
    
    def import_from_file(self, filepath: str) -> TaskBoard:
        """
        Импорт из файла (AHK или JSON)
        
        Args:
            filepath: Путь к файлу
        
        Returns:
            TaskBoard
        """
        path = Path(filepath).expanduser()
        with path.open('r', encoding='utf-8') as f:
            content = f.read()
        
        # Определяем формат по расширению
        suffix = path.suffix.lower()
        if suffix == '.ahk':
            return self.import_from_ahk(content)
        elif suffix == '.json':
            return self.import_from_json(json.loads(content))
        else:
            # Пытаемся определить по содержимому
            if content.strip().startswith('{'):
                return self.import_from_json(json.loads(content))
            else:
                return self.import_from_ahk(content)
