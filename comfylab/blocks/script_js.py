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
import json
import shutil
from typing import Any, Dict, List, Optional, Tuple

from comfylab.engine.registry import register_block
from comfylab.blocks.base import ExecutionContext, ExecIn, ExecOut, DataIn, DataOut
from comfylab.blocks.base_script import BaseSubprocessScriptBlock, parse_decorators

DECORATOR_PATTERN = re.compile(
    r'^//\s*@(input|output)\s+(.*)',
    re.MULTILINE
)

DEFAULT_JS_CODE = """// @input name="value" type="number" default=1.0
// @output name="result" type="number"

result = value * 2;
"""

DEFAULT_TS_CODE = """// @input name="value" type="number" default=1.0
// @output name="result" type="number"

const val: number = value;
result = val * 2;
"""


def parse_js_decorators(code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parses JavaScript/TypeScript-style decorator comments."""
    return parse_decorators(code, DECORATOR_PATTERN)


class BaseJavaScriptBlock(BaseSubprocessScriptBlock):
    comment_pattern = DECORATOR_PATTERN
    default_code = DEFAULT_JS_CODE
    file_extension = ".js"
    executable_name = "block"
    is_ts = False

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        is_typescript = self.properties.get("language") == "typescript" or self.id.endswith("typescript") or "typescript" in self.category.lower() or getattr(self, "is_ts", False)
        self.file_extension = ".ts" if is_typescript else ".js"
        return await super().execute(context, trigger_pin)

    def _get_subprocess_args(self, script_file_path: str) -> List[str]:
        is_typescript = self.properties.get("language") == "typescript" or self.id.endswith("typescript") or "typescript" in self.category.lower() or getattr(self, "is_ts", False)
        cmd = ["block"]
        if is_typescript:
            if shutil.which("tsx"):
                cmd = ["tsx"]
            elif shutil.which("ts-block"):
                cmd = ["ts-block"]
            else:
                cmd = ["block", "--experimental-strip-types"]
        cmd.append(script_file_path)
        return cmd

    def _generate_script(self, code: str, inputs: Dict[str, Any], output_file_path: str) -> str:
        # Generate inputs injection code in JavaScript/TypeScript syntax
        injection_lines = []
        for name, val in inputs.items():
            injection_lines.append(f"const {name} = {json.dumps(val)};")
        injection_code = "\n".join(injection_lines) + "\n\n"

        # Generate mutable output variable declarations
        output_declarations = []
        for out in self._parsed_outputs:
            name = out['name']
            output_declarations.append(f"let {name} = null;")
        output_code = "\n".join(output_declarations) + "\n\n"

        # Output serialization code
        out_obj_fields = ", ".join(f"{out['name']}: {out['name']}" for out in self._parsed_outputs)
        output_script = f"""
const fs = require('fs');
fs.writeFileSync('{output_file_path}', JSON.stringify({{ {out_obj_fields} }}));
"""

        # Split ES6 imports from the rest of the code to place variables after imports
        import_regex = re.compile(r'^\s*import\s+(?:[\s\S]*?from\s+)?[\'"][^\'"]+[\'"]\s*;?', re.MULTILINE)
        import_matches = list(import_regex.finditer(code))
        if import_matches:
            insert_pos = import_matches[-1].end()
            imports_part = code[:insert_pos]
            body_part = code[insert_pos:]
        else:
            imports_part = ""
            body_part = code

        return f"""{imports_part}
{injection_code}
{output_code}
{body_part}
{output_script}"""


class JavaScriptScriptBlock(BaseJavaScriptBlock):
    icon = "☕"
    display_name = "JavaScript Script"
    description = "User-defined JavaScript code block with decorated inputs and outputs."
    default_code = DEFAULT_JS_CODE
    is_ts = False


class TypeScriptScriptBlock(BaseJavaScriptBlock):
    icon = "🟦"
    display_name = "TypeScript Script"
    description = "User-defined TypeScript code block with decorated inputs and outputs."
    default_code = DEFAULT_TS_CODE
    is_ts = True


async def validate_code(code: str, language: str = "javascript") -> dict:
    """Validates JavaScript/TypeScript script syntax using block compilation check."""
    if language == "typescript":
        return {"valid": True}
    import shutil
    import tempfile
    import os
    import asyncio
    if shutil.which("block"):
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w", encoding="utf-8") as f:
            f.write(code)
            temp_name = f.name
        try:
            process = await asyncio.create_subprocess_exec(
                "block", "-c", temp_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                return {"valid": True}
            return {"valid": False, "error": stderr.decode().strip() or stdout.decode().strip()}
        except Exception as e:
            return {"valid": False, "error": str(e)}
        finally:
            try:
                os.unlink(temp_name)
            except:
                pass
    return {"valid": True}


from comfylab.engine.config import get_config
if get_config().get("enable_js_scripting", False):
    register_block("script/javascript")(JavaScriptScriptBlock)
    register_block("script/typescript")(TypeScriptScriptBlock)

