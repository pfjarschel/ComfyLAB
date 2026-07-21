# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import asyncio
import re
from typing import Any, Dict, List, Optional, Tuple

from comfylab.engine.registry import register_block
from comfylab.blocks.base import ExecutionContext, ExecIn, ExecOut, DataIn, DataOut
from comfylab.blocks.base_script import BaseScriptBlock, parse_decorators
from backend.workspace import get_workspace_path, get_temp_dir

DECORATOR_PATTERN = re.compile(
    r'^#\s*@(input|output)\s+(.*)',
    re.MULTILINE
)

DEFAULT_SCRIPT_CODE = """# @input name="value" type="number" default=1.0
# @output name="result" type="number"

result = value * 2
"""


def parse_script_decorators(code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parses Python-style decorator comments."""
    return parse_decorators(code, DECORATOR_PATTERN)


@register_block("script/python")
class PythonScriptBlock(BaseScriptBlock):
    icon = "🐍"
    display_name = "Python Script"
    description = "User-defined Python code block with decorated inputs and outputs."
    comment_pattern = DECORATOR_PATTERN
    default_code = DEFAULT_SCRIPT_CODE

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        code = self.properties.get("code", "")
        if not code.strip():
            raise ValueError("Script block has no code to execute.")

        self._parsed_inputs, self._parsed_outputs = parse_script_decorators(code)

        namespace: Dict[str, Any] = {}

        for inp in self._parsed_inputs:
            name = inp['name']
            val = await context.pull(self.id, name)
            namespace[name] = val

        namespace['context'] = context
        namespace['run_id'] = context.run_id

        workspace_path = get_workspace_path()
        namespace['workspace'] = str(workspace_path)
        namespace['__file__'] = str(get_temp_dir() / f"script_{self.id}.py")

        try:
            import numpy as np
            namespace['np'] = np
            namespace['numpy'] = np
        except ImportError:
            pass

        import math
        namespace['math'] = math

        try:
            compiled = compile(code, f'<script:{self.id}>', 'exec')
        except SyntaxError as e:
            raise SyntaxError(f"Script syntax error: {e}")

        timeout = self.properties.get("timeout", 30.0)

        def run_script():
            exec(compiled, namespace)

        import sys
        workspace_str = str(workspace_path)
        sys.path.insert(0, workspace_str)

        try:
            await asyncio.wait_for(
                asyncio.to_thread(run_script),
                timeout=float(timeout)
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Script block '{self.id}' exceeded timeout of {timeout}s.")
        finally:
            if workspace_str in sys.path:
                sys.path.remove(workspace_str)

        self._computed_outputs = {}
        for out in self._parsed_outputs:
            name = out['name']
            if name in namespace:
                self._computed_outputs[name] = namespace[name]

        return "Out"


def validate_code(code: str) -> dict:
    """Validates Python script syntax using compile()."""
    try:
        compile(code, '<script>', 'exec')
        return {"valid": True}
    except SyntaxError as e:
        return {"valid": False, "error": str(e), "line": e.lineno, "offset": e.offset}

