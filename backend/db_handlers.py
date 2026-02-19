"""
Обработчики действий для работы с базами данных
"""

from typing import Dict, Any, Optional
from backend.core import (
    BaseActionHandler, Action, ExecutionResult, ActionType,
    IDatabaseService
)


class DBSearchHandler(BaseActionHandler):
    """Обработчик поиска в БД"""

    async def execute(self, action: Action) -> ExecutionResult:
        try:
            if not self.database:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error="Сервис баз данных не инициализирован"
                )

            db_name = action.metadata.get('database', '')
            search_column = action.metadata.get('search_column', '')
            search_value = action.metadata.get('search_value', '')
            result_column = action.metadata.get('result_column', '')
            result_variable = action.metadata.get('result_variable', 'db_result')

            # Поиск
            result = self.database.search(db_name, search_column, search_value)

            if result:
                # Сохраняем результат в переменную
                if result_column and result_column in result:
                    self.variables[result_variable] = result[result_column]
                else:
                    self.variables[result_variable] = result

                return ExecutionResult(
                    success=True, action_id=action.id, action_name=action.name,
                    message=f"Найдено в {db_name}: {result_variable}={self.variables.get(result_variable)}"
                )
            else:
                self.variables[result_variable] = None
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    message="Не найдено"
                )

        except Exception as e:
            return ExecutionResult(
                success=False, action_id=action.id, action_name=action.name,
                error=f"Ошибка поиска в БД: {str(e)}"
            )


class DBGetValueHandler(BaseActionHandler):
    """Обработчик получения значения из БД"""

    async def execute(self, action: Action) -> ExecutionResult:
        try:
            variable = action.metadata.get('variable', '')
            column = action.metadata.get('column', '')
            result_variable = action.metadata.get('result_variable', 'db_value')

            # Получаем данные из переменной
            record_data = self.variables.get(variable, {})

            if isinstance(record_data, dict) and column in record_data:
                self.variables[result_variable] = record_data[column]
                return ExecutionResult(
                    success=True, action_id=action.id, action_name=action.name,
                    message=f"Получено: {column}={self.variables.get(result_variable)}"
                )
            else:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error=f"Переменная {variable} не найдена или не содержит {column}"
                )

        except Exception as e:
            return ExecutionResult(
                success=False, action_id=action.id, action_name=action.name,
                error=f"Ошибка получения значения: {str(e)}"
            )


class DBIterateHandler(BaseActionHandler):
    """Обработчик итерации по БД"""

    async def execute(self, action: Action) -> ExecutionResult:
        try:
            if not self.database:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error="Сервис баз данных не инициализирован"
                )

            db_name = action.metadata.get('database', '')
            value_column = action.metadata.get('value_column', '')
            row_variable = action.metadata.get('row_variable', 'current_row')
            value_variable = action.metadata.get('value_variable', 'current_value')

            # Получаем данные
            databases = getattr(self.database, "databases", {})
            db = databases.get(db_name)
            if not db:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error=f"База данных {db_name} не найдена"
                )

            data = db.get('data', [])
            columns = db.get('columns', [])

            count = 0
            for i, record in enumerate(data[:100]):  # Макс 100 строк
                if not self.variables.get('_running', True):
                    break

                self.variables[row_variable] = i + 1
                if value_column and value_column in record:
                    self.variables[value_variable] = record[value_column]
                    count += 1

            return ExecutionResult(
                success=True, action_id=action.id, action_name=action.name,
                message=f"Обработано {count} строк из {db_name}"
            )

        except Exception as e:
            return ExecutionResult(
                success=False, action_id=action.id, action_name=action.name,
                error=f"Ошибка итерации: {str(e)}"
            )


class DBSaveHandler(BaseActionHandler):
    """Обработчик сохранения в БД"""

    async def execute(self, action: Action) -> ExecutionResult:
        try:
            if not self.database:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error="Сервис баз данных не инициализирован"
                )

            db_name = action.metadata.get('database', '')
            search_column = action.metadata.get('search_column', '')
            raw_search_value = str(action.metadata.get('search_value', ''))
            update_column = action.metadata.get('update_column', '')
            raw_save_value = str(action.metadata.get('save_value', ''))

            search_value = self._substitute_variables(raw_search_value, self.variables)
            save_value = self._substitute_variables(raw_save_value, self.variables)

            databases = getattr(self.database, "databases", {})
            db = databases.get(db_name)
            if not db:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error=f"База данных {db_name} не найдена"
                )

            updated = False
            for record in db.get("data", []):
                if str(record.get(search_column, "")).strip() == str(search_value).strip():
                    record[update_column] = save_value
                    updated = True
                    break

            if not updated:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    message="Запись для обновления не найдена"
                )

            self.variables["db_last_saved_value"] = save_value
            return ExecutionResult(
                success=True, action_id=action.id, action_name=action.name,
                message=f"Обновлено {update_column}={save_value}"
            )
        except Exception as e:
            return ExecutionResult(
                success=False, action_id=action.id, action_name=action.name,
                error=f"Ошибка сохранения в БД: {str(e)}"
            )


class CheckValueHandler(BaseActionHandler):
    """Обработчик проверки значения (замена)"""

    async def execute(self, action: Action) -> ExecutionResult:
        try:
            if not self.database:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error="Сервис баз данных не инициализирован"
                )

            db_name = action.metadata.get('database', '')
            from_column = action.metadata.get('from_column', '')
            to_column = action.metadata.get('to_column', '')
            check_variable = action.metadata.get('check_variable', '')
            result_variable = action.metadata.get('result_variable', 'new_value')

            # Получаем текущее значение
            current_value = self.variables.get(check_variable, '')

            # Ищем в БД замен
            databases = getattr(self.database, "databases", {})
            db = databases.get(db_name)
            if not db:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error=f"База данных {db_name} не найдена"
                )

            # Простой поиск соответствия
            for record in db.get('data', []):
                if record.get(from_column) == current_value:
                    self.variables[result_variable] = record.get(to_column, '')
                    return ExecutionResult(
                        success=True, action_id=action.id, action_name=action.name,
                        message=f"Замена: {current_value} → {self.variables[result_variable]}"
                    )

            # Замена не найдена
            self.variables[result_variable] = current_value
            return ExecutionResult(
                success=False, action_id=action.id, action_name=action.name,
                message=f"Замена не найдена для: {current_value}"
            )

        except Exception as e:
            return ExecutionResult(
                success=False, action_id=action.id, action_name=action.name,
                error=f"Ошибка проверки значения: {str(e)}"
            )


class RunRowHandler(BaseActionHandler):
    """Обработчик запуска строки (подпрограммы)"""

    async def execute(self, action: Action) -> ExecutionResult:
        try:
            row_id = action.metadata.get('row_id', '')
            wait_complete = action.metadata.get('wait_complete', True)

            # Находим строку в текущей доске
            # Это требует доступа к доске, который передаётся через variables
            board = self.variables.get('_board')
            if not board:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error="Доска не доступна для запуска строки"
                )

            target_row = None
            for row in board.rows:
                if row.id == row_id:
                    target_row = row
                    break

            if not target_row:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    error=f"Строка {row_id} не найдена"
                )

            if not target_row.enabled:
                return ExecutionResult(
                    success=False, action_id=action.id, action_name=action.name,
                    message=f"Строка {target_row.name} отключена"
                )

            # Выполняем действия строки
            for row_action in target_row.actions:
                if not row_action.enabled:
                    continue

                handler = self.registry.get_handler(row_action.action_type)
                if handler:
                    handler.variables = self.variables
                    handler.registry = self.registry
                    await handler.execute(row_action)

            return ExecutionResult(
                success=True, action_id=action.id, action_name=action.name,
                message=f"Строка {target_row.name} выполнена"
            )

        except Exception as e:
            return ExecutionResult(
                success=False, action_id=action.id, action_name=action.name,
                error=f"Ошибка запуска строки: {str(e)}"
            )
