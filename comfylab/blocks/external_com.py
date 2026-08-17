import sys
import uuid
import json
import shutil
import asyncio
import logging
from typing import Any, Dict, List, Optional
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.engine.registry import register_block

logger = logging.getLogger("comfylab.blocks.external_com")

# In-memory COM session registry for active graph runs
_ACTIVE_COM_SESSIONS: Dict[str, Dict[str, Any]] = {}


def _get_powershell_for_bitness(bitness: str) -> str:
    """Returns the path to the appropriate PowerShell executable based on bitness."""
    if sys.platform != "win32":
        return shutil.which("pwsh") or shutil.which("powershell") or "powershell"

    if bitness == "32-bit (SysWOW64)":
        syswow64_ps = r"C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe"
        if shutil.which(syswow64_ps):
            return syswow64_ps
        return "powershell.exe"

    if bitness == "64-bit":
        sys32_ps = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        if shutil.which(sys32_ps):
            return sys32_ps
        return "powershell.exe"

    # Auto: prefer pwsh if available, else standard powershell
    return shutil.which("pwsh") or shutil.which("powershell.exe") or "powershell"


async def _run_com_command(ps_exe: str, ps_script: str, timeout: float = 30.0) -> Any:
    """Executes a PowerShell script in an STA environment and parses JSON result."""
    if sys.platform != "win32" and not (shutil.which("pwsh") or shutil.which("powershell")):
        raise RuntimeError("ActiveX/COM Automation is only supported on Windows operating systems.")

    process = await asyncio.create_subprocess_exec(
        ps_exe,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy", "Bypass",
        "-STA",
        "-Command",
        ps_script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        raise TimeoutError(f"COM operation timed out after {timeout}s.")

    if process.returncode != 0:
        err_msg = stderr.decode().strip() or stdout.decode().strip()
        raise RuntimeError(f"COM execution failed: {err_msg}")

    out_text = stdout.decode().strip()
    if not out_text:
        return None

    try:
        return json.loads(out_text)
    except json.JSONDecodeError:
        return out_text


# ---------------------------------------------------------------------------
# Block 1 — Open COM Session
# ---------------------------------------------------------------------------

@register_block("external_libraries/com/open")
class COMOpenSessionBlock(BaseBlock):
    category = "External Libraries/COM"
    icon = "🔌"
    display_name = "Open COM Session"
    description = (
        "Initializes an ActiveX/COM object by ProgID (e.g. 'Excel.Application', 'Thorlabs.APTMotor') "
        "and outputs a Session Handle."
    )

    inputs_def = [
        ExecIn("In"),
        DataIn("ProgID", type_hint=str, default="Excel.Application", widget="text"),
        DataIn("Bitness", type_hint=str, default="Auto", widget="dropdown",
               options=["Auto", "32-bit (SysWOW64)", "64-bit"]),
        DataIn("Visible", type_hint=bool, default=False, widget="toggle"),
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Session", type_hint=str),
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Abrir Sessão COM",
            "description": "Inicializa um objeto ActiveX/COM por ProgID (ex: 'Excel.Application') e emite uma referência de sessão.",
            "category": "Bibliotecas Externas/COM",
            "pins": {
                "In": "Entrada",
                "ProgID": "ProgID",
                "Bitness": "Arquitetura",
                "Visible": "Visível",
                "Out": "Saída",
                "Session": "Sessão"
            }
        },
        "es": {
            "display_name": "Abrir Sesión COM",
            "description": "Inicializa un objeto ActiveX/COM por ProgID (ej: 'Excel.Application') y emite una referencia de sesión.",
            "category": "Bibliotecas Externas/COM",
            "pins": {
                "In": "Entrada",
                "ProgID": "ProgID",
                "Bitness": "Arquitectura",
                "Visible": "Visible",
                "Out": "Salida",
                "Session": "Sesión"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._session_id: Optional[str] = None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        prog_id = await context.pull(self.id, "ProgID") or "Excel.Application"
        bitness = await context.pull(self.id, "Bitness") or "Auto"
        visible = await context.pull(self.id, "Visible") or False

        session_id = f"COM_{uuid.uuid4().hex[:8]}"
        ps_exe = _get_powershell_for_bitness(bitness)

        # Test creating object
        vis_cmd = f"$obj.Visible = ${str(visible).lower()}; " if visible else ""
        test_script = (
            f"try {{ "
            f"$obj = New-Object -ComObject '{prog_id}'; "
            f"{vis_cmd}"
            f"[System.Runtime.InteropServices.Marshal]::ReleaseComObject($obj) | Out-Null; "
            f"@{{ status = 'ok'; session = '{session_id}' }} | ConvertTo-Json -Compress "
            f"}} catch {{ "
            f"[Console]::Error.WriteLine($_.Exception.Message); exit 1 "
            f"}}"
        )

        res = await _run_com_command(ps_exe, test_script)
        _ACTIVE_COM_SESSIONS[session_id] = {
            "prog_id": prog_id,
            "bitness": bitness,
            "ps_exe": ps_exe,
            "visible": visible
        }

        self._session_id = session_id
        context.cache_value(self.id, "Session", session_id)
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Session":
            return self._session_id
        return None

    async def clear_data(self) -> None:
        self._session_id = None


# ---------------------------------------------------------------------------
# Block 2 — Invoke COM Member (Method / Property)
# ---------------------------------------------------------------------------

@register_block("external_libraries/com/call")
class COMInvokeMemberBlock(BaseBlock):
    category = "External Libraries/COM"
    icon = "⚙️"
    display_name = "Invoke COM Member"
    description = (
        "Invokes a method or gets/sets a property on an active ActiveX/COM session."
    )

    inputs_def = [
        ExecIn("In"),
        DataIn("Session", type_hint=str, default=""),
        DataIn("MemberName", type_hint=str, default="Quit", widget="text"),
        DataIn("ActionType", type_hint=str, default="Invoke Method", widget="dropdown",
               options=["Invoke Method", "Get Property", "Set Property"]),
        DataIn("Argument1", type_hint=Any, default="", widget="text"),
        DataIn("Argument2", type_hint=Any, default="", widget="text"),
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Result", type_hint=Any),
        DataOut("Session", type_hint=str),
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Invocar Membro COM",
            "description": "Invoca um método ou obtém/define uma propriedade em uma sessão ActiveX/COM ativa.",
            "category": "Bibliotecas Externas/COM",
            "pins": {
                "In": "Entrada",
                "Session": "Sessão",
                "MemberName": "Nome do Membro",
                "ActionType": "Tipo de Ação",
                "Argument1": "Argumento 1",
                "Argument2": "Argumento 2",
                "Out": "Saída",
                "Result": "Resultado"
            }
        },
        "es": {
            "display_name": "Invocar Miembro COM",
            "description": "Invoca un método u obtiene/establece una propiedad en una sesión ActiveX/COM activa.",
            "category": "Bibliotecas Externas/COM",
            "pins": {
                "In": "Entrada",
                "Session": "Sesión",
                "MemberName": "Nombre del Miembro",
                "ActionType": "Tipo de Acción",
                "Argument1": "Argumento 1",
                "Argument2": "Argumento 2",
                "Out": "Salida",
                "Result": "Resultado"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._result: Any = None
        self._session_id: Optional[str] = None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        session_id = await context.pull(self.id, "Session")
        member_name = await context.pull(self.id, "MemberName") or "Quit"
        action_type = await context.pull(self.id, "ActionType") or "Invoke Method"
        arg1 = await context.pull(self.id, "Argument1")
        arg2 = await context.pull(self.id, "Argument2")

        session_info = _ACTIVE_COM_SESSIONS.get(session_id, {})
        prog_id = session_info.get("prog_id")
        ps_exe = session_info.get("ps_exe") or _get_powershell_for_bitness("Auto")

        if not prog_id:
            prog_id = session_id  # Allow direct ProgID fallback if not opened via Open session block

        args_str = ""
        if arg1 not in (None, ""):
            args_str += f", {json.dumps(arg1)}"
            if arg2 not in (None, ""):
                args_str += f", {json.dumps(arg2)}"

        if action_type == "Get Property":
            cmd = f"$res = $obj.{member_name}"
        elif action_type == "Set Property":
            cmd = f"$obj.{member_name} = {json.dumps(arg1)}; $res = $true"
        else:
            cmd = f"$res = $obj.{member_name}({args_str.lstrip(', ')})"

        script = (
            f"try {{ "
            f"$obj = New-Object -ComObject '{prog_id}'; "
            f"{cmd}; "
            f"@{{ result = $res }} | ConvertTo-Json -Depth 5 -Compress "
            f"}} catch {{ "
            f"[Console]::Error.WriteLine($_.Exception.Message); exit 1 "
            f"}}"
        )

        res = await _run_com_command(ps_exe, script)
        result_val = res.get("result") if isinstance(res, dict) else res

        self._result = result_val
        self._session_id = session_id
        context.cache_value(self.id, "Result", result_val)
        context.cache_value(self.id, "Session", session_id)
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            return self._result
        elif pin_name == "Session":
            return self._session_id
        return None

    async def clear_data(self) -> None:
        self._result = None
        self._session_id = None


# ---------------------------------------------------------------------------
# Block 3 — Close COM Session
# ---------------------------------------------------------------------------

@register_block("external_libraries/com/close")
class COMCloseSessionBlock(BaseBlock):
    category = "External Libraries/COM"
    icon = "🔌"
    display_name = "Close COM Session"
    description = "Releases an ActiveX/COM object session and cleans up resources."

    inputs_def = [
        ExecIn("In"),
        DataIn("Session", type_hint=str, default=""),
    ]
    outputs_def = [
        ExecOut("Out"),
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Fechar Sessão COM",
            "description": "Libera uma sessão de objeto ActiveX/COM e limpa os recursos.",
            "category": "Bibliotecas Externas/COM",
            "pins": {
                "In": "Entrada",
                "Session": "Sessão",
                "Out": "Saída"
            }
        },
        "es": {
            "display_name": "Cerrar Sesión COM",
            "description": "Libera una sesión de objeto ActiveX/COM y limpia los recursos.",
            "category": "Bibliotecas Externas/COM",
            "pins": {
                "In": "Entrada",
                "Session": "Sesión",
                "Out": "Salida"
            }
        }
    }

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        session_id = await context.pull(self.id, "Session")
        if session_id in _ACTIVE_COM_SESSIONS:
            del _ACTIVE_COM_SESSIONS[session_id]
        return "Out"


# ---------------------------------------------------------------------------
# Block 4 — Standalone ActiveX / COM Controller
# ---------------------------------------------------------------------------

@register_block("external_libraries/com/controller")
class COMControllerBlock(BaseBlock):
    category = "External Libraries/COM"
    icon = "🎛️"
    display_name = "ActiveX / COM Controller"
    description = (
        "Standalone single-block controller for quick ActiveX/COM automation commands "
        "with selectable 32-bit/64-bit architecture."
    )

    inputs_def = [
        ExecIn("In"),
        DataIn("ProgID", type_hint=str, default="Excel.Application", widget="text"),
        DataIn("MemberName", type_hint=str, default="Version", widget="text"),
        DataIn("ActionType", type_hint=str, default="Get Property", widget="dropdown",
               options=["Invoke Method", "Get Property", "Set Property"]),
        DataIn("Bitness", type_hint=str, default="Auto", widget="dropdown",
               options=["Auto", "32-bit (SysWOW64)", "64-bit"]),
        DataIn("Argument", type_hint=Any, default="", widget="text"),
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Result", type_hint=Any),
    ]

    i18n = {
        "pt-BR": {
            "display_name": "Controlador ActiveX / COM",
            "description": "Controlador em bloco único para comandos rápidos de automação ActiveX/COM com seleção de arquitetura 32/64-bit.",
            "category": "Bibliotecas Externas/COM",
            "pins": {
                "In": "Entrada",
                "ProgID": "ProgID",
                "MemberName": "Nome do Membro",
                "ActionType": "Tipo de Ação",
                "Bitness": "Arquitetura",
                "Argument": "Argumento",
                "Out": "Saída",
                "Result": "Resultado"
            }
        },
        "es": {
            "display_name": "Controlador ActiveX / COM",
            "description": "Controlador en bloque único para comandos rápidos de automatización ActiveX/COM con selección de arquitectura 32/64-bit.",
            "category": "Bibliotecas Externas/COM",
            "pins": {
                "In": "Entrada",
                "ProgID": "ProgID",
                "MemberName": "Nombre del Miembro",
                "ActionType": "Tipo de Acción",
                "Bitness": "Arquitectura",
                "Argument": "Argumento",
                "Out": "Salida",
                "Result": "Resultado"
            }
        }
    }

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        super().__init__(block_id, properties)
        self._result: Any = None

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        prog_id = await context.pull(self.id, "ProgID") or "Excel.Application"
        member_name = await context.pull(self.id, "MemberName") or "Version"
        action_type = await context.pull(self.id, "ActionType") or "Get Property"
        bitness = await context.pull(self.id, "Bitness") or "Auto"
        arg = await context.pull(self.id, "Argument")

        ps_exe = _get_powershell_for_bitness(bitness)

        if action_type == "Get Property":
            cmd = f"$res = $obj.{member_name}"
        elif action_type == "Set Property":
            cmd = f"$obj.{member_name} = {json.dumps(arg)}; $res = $true"
        else:
            args_str = json.dumps(arg) if arg not in (None, "") else ""
            cmd = f"$res = $obj.{member_name}({args_str})"

        script = (
            f"try {{ "
            f"$obj = New-Object -ComObject '{prog_id}'; "
            f"{cmd}; "
            f"[System.Runtime.InteropServices.Marshal]::ReleaseComObject($obj) | Out-Null; "
            f"@{{ result = $res }} | ConvertTo-Json -Depth 5 -Compress "
            f"}} catch {{ "
            f"[Console]::Error.WriteLine($_.Exception.Message); exit 1 "
            f"}}"
        )

        res = await _run_com_command(ps_exe, script)
        result_val = res.get("result") if isinstance(res, dict) else res

        self._result = result_val
        context.cache_value(self.id, "Result", result_val)
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        if pin_name == "Result":
            return self._result
        return None

    async def clear_data(self) -> None:
        self._result = None
