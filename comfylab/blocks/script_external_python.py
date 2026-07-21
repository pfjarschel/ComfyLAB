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

import sys
import json
from typing import Any, Dict, List, Optional

from comfylab.engine.registry import register_block
from comfylab.blocks.script import parse_script_decorators
from comfylab.blocks.base_script import BaseSubprocessScriptBlock
from comfylab.engine.config import get_config

DEFAULT_EXTERNAL_PYTHON_CODE = """# @input name="value" type="number" default=1.0
# @output name="result" type="number"

result = value * 2
"""


@register_block("script/python_external")
class ExternalPythonScriptBlock(BaseSubprocessScriptBlock):
    icon = "🔀"
    display_name = "External Python"
    description = "Runs Python code in an isolated subprocess with custom Python environments."
    comment_pattern = None
    default_code = DEFAULT_EXTERNAL_PYTHON_CODE
    file_extension = ".py"

    def __init__(self, block_id: str, properties: Optional[Dict[str, Any]] = None):
        # We need the Python comment pattern from script.py
        from comfylab.blocks.script import DECORATOR_PATTERN
        self.comment_pattern = DECORATOR_PATTERN
        super().__init__(block_id, properties)

    def _get_subprocess_args(self, script_file_path: str) -> List[str]:
        block_exec = self.properties.get("executable_path", "").strip()
        config = get_config()
        config_exec = config.get("external_python_path", "").strip()
        python_exe = block_exec or config_exec or sys.executable
        return [python_exe, script_file_path]

    def _generate_script(self, code: str, inputs: Dict[str, Any], output_file_path: str) -> str:
        # Inputs injection via JSON load in script prefix
        injection_code = f"""import json
import sys

# Load inputs from injected JSON
__inputs = json.loads({json.dumps(json.dumps(inputs))})
for __k, __v in __inputs.items():
    globals()[__k] = __v
"""

        # Outputs extraction at script suffix
        output_names = [out["name"] for out in self._parsed_outputs]
        extraction_code = f"""
# Extract outputs
__outputs = {{}}
for __name in {repr(output_names)}:
    if __name in globals():
        __outputs[__name] = globals()[__name]
with open({repr(output_file_path)}, "w", encoding="utf-8") as __f:
    json.dump(__outputs, __f)
"""
        return injection_code + "\n# --- User Script --- \n" + code + "\n# --- Extraction --- \n" + extraction_code
