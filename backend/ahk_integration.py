"""
Интеграция с AutoHotkey v2:
- парсинг и валидация скриптов
- безопасный запуск (Windows native / cross-platform emulation)
"""

from __future__ import annotations

import asyncio
import os
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core import Action, ActionType, BackendApplication, Coordinates, TaskBoard, TaskRow


@dataclass
class AhkCommand:
    name: str
    args: List[str]
    raw: str
    line_no: int


@dataclass
class AhkFunction:
    name: str
    params: List[str]
    body: List[AhkCommand] = field(default_factory=list)


@dataclass
class AhkScript:
    requires: Optional[str] = None
    globals: Dict[str, str] = field(default_factory=dict)
    top_level: List[AhkCommand] = field(default_factory=list)
    hotkeys: Dict[str, List[AhkCommand]] = field(default_factory=dict)
    functions: Dict[str, AhkFunction] = field(default_factory=dict)


@dataclass
class AhkDiagnostic:
    level: str  # info|warning|error
    message: str
    line_no: int = 0


@dataclass
class AhkValidationResult:
    is_valid: bool
    diagnostics: List[AhkDiagnostic] = field(default_factory=list)


@dataclass
class AhkExecutionResult:
    success: bool
    mode: str  # native|emulated|none
    return_code: int = 0
    stdout: str = ""
    stderr: str = ""
    diagnostics: List[AhkDiagnostic] = field(default_factory=list)
    board: Optional[TaskBoard] = None


class AhkV2Parser:
    _requires_re = re.compile(r"^#Requires\s+AutoHotkey\s+v(?P<ver>[\d\.]+)", re.IGNORECASE)
    _assign_re = re.compile(r"^(?P<name>[A-Za-z_]\w*)\s*:?=\s*(?P<value>.+)$")
    _global_re = re.compile(r"^global\s+(?P<body>.+)$", re.IGNORECASE)
    _func_re = re.compile(r"^(?P<name>[A-Za-z_]\w*)\((?P<params>.*)\)\s*\{$")
    _hotkey_re = re.compile(r"^(?P<key>.+?)::\s*(?P<body>.*)$")
    _call_re = re.compile(r"^(?P<name>[A-Za-z_]\w*)\((?P<args>.*)\)$")

    def parse_text(self, text: str) -> AhkScript:
        script = AhkScript()
        lines = text.splitlines()
        i = 0

        while i < len(lines):
            raw = lines[i]
            line = self._strip_comment(raw).strip()
            i += 1
            if not line:
                continue

            m_req = self._requires_re.match(line)
            if m_req:
                script.requires = m_req.group("ver")
                continue

            m_global = self._global_re.match(line)
            if m_global:
                self._parse_global_declaration(m_global.group("body"), script.globals)
                continue

            # Функция
            m_func = self._func_re.match(line)
            if m_func:
                name = m_func.group("name")
                params = [p.strip() for p in m_func.group("params").split(",") if p.strip()]
                body_lines, i = self._collect_block(lines, i)
                body_cmds = self._parse_commands(body_lines, i - len(body_lines))
                script.functions[name] = AhkFunction(name=name, params=params, body=body_cmds)
                continue

            # Hotkey
            m_hot = self._hotkey_re.match(line)
            if m_hot:
                hk = m_hot.group("key").strip()
                inline_body = m_hot.group("body").strip()
                if inline_body and inline_body != "{":
                    script.hotkeys[hk] = [self._parse_command(inline_body, i)]
                else:
                    body_lines, i = self._collect_block(lines, i)
                    script.hotkeys[hk] = self._parse_commands(body_lines, i - len(body_lines))
                continue

            # Глобальная переменная (только top-level)
            m_assign = self._assign_re.match(line)
            if m_assign:
                script.globals[m_assign.group("name")] = m_assign.group("value").strip()
                continue

            script.top_level.append(self._parse_command(line, i))

        return script

    def parse_file(self, filepath: str | Path) -> AhkScript:
        path = Path(filepath).expanduser()
        text = path.read_text(encoding="utf-8-sig")
        return self.parse_text(text)

    def _collect_block(self, lines: List[str], start_index: int) -> tuple[List[str], int]:
        body: List[str] = []
        depth = 1
        i = start_index
        while i < len(lines):
            raw = lines[i]
            line = self._strip_comment(raw).strip()
            i += 1
            if not line:
                continue
            depth += line.count("{")
            depth -= line.count("}")
            if depth <= 0:
                break
            body.append(line)
        return body, i

    def _parse_commands(self, lines: List[str], start_line: int) -> List[AhkCommand]:
        out = []
        for idx, line in enumerate(lines, start=start_line):
            clean = line.strip()
            if not clean or clean == "}":
                continue
            out.append(self._parse_command(clean, idx))
        return out

    def _parse_command(self, line: str, line_no: int) -> AhkCommand:
        m_call = self._call_re.match(line)
        if m_call:
            name = m_call.group("name")
            args = self._split_args(m_call.group("args"))
            return AhkCommand(name=name, args=args, raw=line, line_no=line_no)

        # v1-style and label-style commands: "Click 100, 200", "Send {Enter}"
        parts = line.split(maxsplit=1)
        name = parts[0]
        args = self._split_args(parts[1]) if len(parts) > 1 else []
        return AhkCommand(name=name, args=args, raw=line, line_no=line_no)

    def _strip_comment(self, line: str) -> str:
        in_string = False
        out = []
        for ch in line:
            if ch == '"':
                in_string = not in_string
            if ch == ';' and not in_string:
                break
            out.append(ch)
        return "".join(out)

    def _split_args(self, args_str: str) -> List[str]:
        args = []
        buf = []
        depth = 0
        in_string = False
        for ch in args_str:
            if ch == '"':
                in_string = not in_string
            elif ch == "(" and not in_string:
                depth += 1
            elif ch == ")" and not in_string and depth > 0:
                depth -= 1

            if ch == "," and not in_string and depth == 0:
                args.append("".join(buf).strip())
                buf = []
            else:
                buf.append(ch)
        if buf:
            args.append("".join(buf).strip())
        return [a for a in args if a != ""]

    def _parse_global_declaration(self, body: str, target: Dict[str, str]) -> None:
        # Пример: global a := 1, b := "x"
        for chunk in self._split_args(body):
            m_assign = self._assign_re.match(chunk)
            if m_assign:
                target[m_assign.group("name")] = m_assign.group("value").strip()
            else:
                name = chunk.strip()
                if name:
                    target[name] = ""


class AhkValidator:
    WINDOWS_ONLY_COMMANDS = {"ComObject", "WinExist", "WinActivate", "ControlSend", "ControlClick"}
    POTENTIALLY_DANGEROUS = {"Run", "RunWait", "DllCall", "RegWrite", "RegDelete"}

    def validate(self, script: AhkScript) -> AhkValidationResult:
        diagnostics: List[AhkDiagnostic] = []

        if not script.requires:
            diagnostics.append(AhkDiagnostic("warning", "Missing #Requires AutoHotkey v2.0 directive"))
        elif not script.requires.startswith("2"):
            diagnostics.append(AhkDiagnostic("error", f"Unsupported AHK version: {script.requires}"))

        all_cmds: List[AhkCommand] = []
        all_cmds.extend(script.top_level)
        for body in script.hotkeys.values():
            all_cmds.extend(body)
        for fn in script.functions.values():
            all_cmds.extend(fn.body)

        for cmd in all_cmds:
            name = cmd.name
            if name in self.POTENTIALLY_DANGEROUS:
                diagnostics.append(AhkDiagnostic("warning", f"Potentially dangerous command: {name}", cmd.line_no))
            if name in self.WINDOWS_ONLY_COMMANDS and platform.system() != "Windows":
                diagnostics.append(AhkDiagnostic("info", f"Windows-specific command: {name}", cmd.line_no))

        has_error = any(d.level == "error" for d in diagnostics)
        return AhkValidationResult(is_valid=not has_error, diagnostics=diagnostics)


class AhkToBoardTranslator:
    def to_board(self, script: AhkScript, board_name: str = "Imported AHK v2") -> tuple[TaskBoard, List[AhkDiagnostic]]:
        board = TaskBoard(id=f"ahk_{os.getpid()}", name=board_name)
        diagnostics: List[AhkDiagnostic] = []
        function_row_ids: Dict[str, str] = {}

        main_row = TaskRow(id="row_main", name="AHK Main")
        board.add_row(main_row)

        # Создаём отдельные строки для функций, чтобы сохранить структуру сценария.
        for fn_name in script.functions.keys():
            row_id = f"row_fn_{fn_name.lower()}"
            function_row_ids[fn_name] = row_id
            board.add_row(TaskRow(id=row_id, name=f"Fn: {fn_name}"))

        commands = list(script.top_level)
        if not commands and script.hotkeys:
            # По умолчанию берём первый hotkey block для эмуляции.
            first_hk = next(iter(script.hotkeys.keys()))
            commands = list(script.hotkeys[first_hk])
        if not commands and "Main" in script.functions:
            commands = [AhkCommand(name="Main", args=[], raw="Main()", line_no=0)]

        for cmd in commands:
            action = self._command_to_action(cmd, diagnostics, function_row_ids)
            if action:
                main_row.add_action(action)

        # Наполняем строки функций.
        for fn_name, fn in script.functions.items():
            row = next((r for r in board.rows if r.id == function_row_ids[fn_name]), None)
            if row is None:
                continue
            for cmd in fn.body:
                action = self._command_to_action(cmd, diagnostics, function_row_ids)
                if action:
                    row.add_action(action)

        return board, diagnostics

    def _command_to_action(
        self,
        cmd: AhkCommand,
        diagnostics: List[AhkDiagnostic],
        function_row_ids: Dict[str, str],
    ) -> Optional[Action]:
        name = cmd.name.lower()
        action_id = f"ahk_line_{cmd.line_no}_{name}"

        # Вызовы пользовательских функций превращаем в RUN_ROW.
        if cmd.name in function_row_ids:
            return Action(
                id=action_id,
                action_type=ActionType.RUN_ROW,
                name=f"Call {cmd.name}",
                metadata={"row_id": function_row_ids[cmd.name], "wait_complete": True},
            )

        if name == "click":
            x, y = self._extract_xy(cmd.args)
            return Action(
                id=action_id,
                action_type=ActionType.MOUSE_CLICK,
                name="AHK Click",
                coordinates=Coordinates(x=x, y=y),
                mouse_button="left",
            )
        if name == "send":
            key = cmd.args[0] if cmd.args else ""
            key = str(key).strip().strip('"').strip("{}")
            return Action(
                id=action_id,
                action_type=ActionType.KEY_PRESS,
                name="AHK Send",
                key=key.lower(),
            )
        if name == "sleep":
            delay = int(self._safe_int(cmd.args[0], 0)) if cmd.args else 0
            return Action(
                id=action_id,
                action_type=ActionType.WAIT_TIME,
                name="AHK Sleep",
                delay_before_ms=max(delay, 0),
            )
        if name == "pixelwaitchange":
            x, y = self._extract_xy(cmd.args)
            timeout = int(self._safe_int(cmd.args[2], 5000)) if len(cmd.args) >= 3 else 5000
            interval = int(self._safe_int(cmd.args[3], 100)) if len(cmd.args) >= 4 else 100
            return Action(
                id=action_id,
                action_type=ActionType.WAIT_PIXEL_CHANGE,
                name="AHK PixelWaitChange",
                coordinates=Coordinates(x=x, y=y),
                metadata={"timeout_ms": timeout, "check_interval_ms": interval},
            )
        if name == "clipwait":
            sec = float(cmd.args[0]) if cmd.args else 1.0
            return Action(
                id=action_id,
                action_type=ActionType.WAIT_TIME,
                name="AHK ClipWait",
                delay_before_ms=max(0, int(sec * 1000)),
            )
        if name in {"pixelgetcolor", "pixelsearch"}:
            x, y = self._extract_xy(cmd.args)
            return Action(
                id=action_id,
                action_type=ActionType.WAIT_PIXEL_CHANGE,
                name=f"AHK {cmd.name}",
                coordinates=Coordinates(x=x, y=y),
                metadata={"timeout_ms": 5000, "check_interval_ms": 100},
            )
        if ":=" in cmd.raw:
            return Action(
                id=action_id,
                action_type=ActionType.LOG,
                name="AHK Assign",
                metadata={"message": cmd.raw, "log_level": "DEBUG"},
            )

        if name in {
            "if", "for", "loop", "switch", "try", "catch", "throw", "return",
            "continue", "break", "else", "finally",
        }:
            return Action(
                id=action_id,
                action_type=ActionType.LOG,
                name=f"AHK {cmd.name}",
                metadata={"message": cmd.raw, "log_level": "DEBUG"},
            )

        if name in {
            "winexist", "winactivate", "winwaitactive",
            "clipboard", "fileread", "fileappend", "filedelete", "fileexist",
            "msgbox", "comobject", "clipwait",
            "map", "array", "instr", "strsplit", "subStr".lower(), "trim",
        }:
            return Action(
                id=action_id,
                action_type=ActionType.LOG,
                name=f"AHK {cmd.name}",
                metadata={"message": cmd.raw, "log_level": "INFO"},
            )

        diagnostics.append(AhkDiagnostic("info", f"Unsupported command in emulation: {cmd.name}", cmd.line_no))
        return Action(
            id=action_id,
            action_type=ActionType.LOG,
            name=f"AHK Unsupported: {cmd.name}",
            metadata={"message": cmd.raw, "log_level": "WARNING"},
        )

    def _extract_xy(self, args: List[str]) -> tuple[int, int]:
        if len(args) >= 2:
            return self._safe_int(args[-2], 0), self._safe_int(args[-1], 0)
        return 0, 0

    def _safe_int(self, value: Any, default: int) -> int:
        try:
            return int(str(value).strip().strip('"'))
        except Exception:
            return default


class AhkRunner:
    def __init__(self, backend: BackendApplication):
        self.backend = backend
        self.parser = AhkV2Parser()
        self.validator = AhkValidator()
        self.translator = AhkToBoardTranslator()

    def parse_file(self, filepath: str | Path) -> AhkScript:
        return self.parser.parse_file(filepath)

    def validate_file(self, filepath: str | Path) -> AhkValidationResult:
        script = self.parser.parse_file(filepath)
        return self.validator.validate(script)

    def find_ahk_executable(self) -> Optional[str]:
        if platform.system() != "Windows":
            return None
        env_path = os.environ.get("AUTOHOTKEY_EXE")
        if env_path and Path(env_path).exists():
            return env_path

        for candidate in (
            r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe",
            r"C:\Program Files\AutoHotkey\AutoHotkey.exe",
            "AutoHotkey64.exe",
            "AutoHotkey.exe",
        ):
            resolved = shutil.which(candidate) if os.path.basename(candidate) == candidate else candidate
            if resolved and Path(resolved).exists():
                return str(resolved)
        return None

    def execute_file(
        self,
        filepath: str | Path,
        mode: str = "auto",
        timeout_sec: int = 30,
        allowed_root: Optional[str | Path] = None,
    ) -> AhkExecutionResult:
        path = Path(filepath).expanduser().resolve()
        if allowed_root is not None:
            root = Path(allowed_root).expanduser().resolve()
            if root not in path.parents and path != root:
                return AhkExecutionResult(
                    success=False,
                    mode="none",
                    diagnostics=[AhkDiagnostic("error", f"Path outside allowed root: {path}")],
                )

        script = self.parser.parse_file(path)
        validation = self.validator.validate(script)
        if not validation.is_valid:
            return AhkExecutionResult(False, "none", diagnostics=validation.diagnostics)

        selected_mode = mode
        if mode == "auto":
            selected_mode = "native" if self.find_ahk_executable() else "emulated"

        if selected_mode == "native":
            exe = self.find_ahk_executable()
            if not exe:
                return AhkExecutionResult(
                    success=False,
                    mode="native",
                    diagnostics=[AhkDiagnostic("error", "AutoHotkey executable not found")],
                )
            return self._execute_native(exe, path, timeout_sec, validation.diagnostics)

        if selected_mode == "emulated":
            return self._execute_emulated(script, validation.diagnostics)

        return AhkExecutionResult(False, "none", diagnostics=[AhkDiagnostic("error", f"Unknown mode: {mode}")])

    def _execute_native(
        self,
        ahk_exe: str,
        script_path: Path,
        timeout_sec: int,
        diagnostics: List[AhkDiagnostic],
    ) -> AhkExecutionResult:
        try:
            proc = subprocess.run(
                [ahk_exe, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            return AhkExecutionResult(
                success=proc.returncode == 0,
                mode="native",
                return_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                diagnostics=diagnostics,
            )
        except subprocess.TimeoutExpired as exc:
            return AhkExecutionResult(
                success=False,
                mode="native",
                return_code=-1,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "Timeout",
                diagnostics=diagnostics + [AhkDiagnostic("error", "Native AHK execution timeout")],
            )
        except Exception as exc:
            return AhkExecutionResult(
                success=False,
                mode="native",
                return_code=-1,
                stderr=str(exc),
                diagnostics=diagnostics + [AhkDiagnostic("error", f"Native run failed: {exc}")],
            )

    def _execute_emulated(self, script: AhkScript, diagnostics: List[AhkDiagnostic]) -> AhkExecutionResult:
        board, translate_diags = self.translator.to_board(script)

        async def _run():
            return await self.backend.run_board(board)

        try:
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    # Эмуляцию из активного loop запускаем в отдельном потоке.
                    results = asyncio.run(asyncio.to_thread(lambda: asyncio.run(_run())))
                else:
                    results = loop.run_until_complete(_run())
            except RuntimeError:
                results = asyncio.run(_run())

            success = all(r.success for r in results) if results else True
            return AhkExecutionResult(
                success=success,
                mode="emulated",
                diagnostics=diagnostics + translate_diags,
                board=board,
            )
        except Exception as exc:
            return AhkExecutionResult(
                success=False,
                mode="emulated",
                diagnostics=diagnostics + translate_diags + [AhkDiagnostic("error", f"Emulation failed: {exc}")],
                board=board,
            )
