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
import shutil
from typing import Any, Dict, List, Optional, Tuple

from comfylab.engine.registry import register_block
from comfylab.blocks.base import ExecutionContext
from comfylab.blocks.base_script import BaseSubprocessScriptBlock, parse_decorators

# Lupa import fallback
try:
    import lupa
    LUPA_AVAILABLE = True
except ImportError:
    LUPA_AVAILABLE = False

DECORATOR_PATTERN = re.compile(
    r'^--\s*@(input|output)\s+(.*)',
    re.MULTILINE
)

DEFAULT_LUA_CODE = """-- @input name="value" type="number" default=1.0
-- @output name="result" type="number"

result = value * 2
"""


def parse_lua_decorators(code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parses Lua-style decorator comments."""
    return parse_decorators(code, DECORATOR_PATTERN)


@register_block("script/lua")
class LuaScriptBlock(BaseSubprocessScriptBlock):
    icon = "🌙"
    display_name = "Lua Script"
    description = "User-defined Lua code block with decorated inputs and outputs."
    comment_pattern = DECORATOR_PATTERN
    default_code = DEFAULT_LUA_CODE
    file_extension = ".lua"
    executable_name = "lua"

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        if LUPA_AVAILABLE:
            code = self.properties.get("code", "")
            if not code.strip():
                raise ValueError("Script block has no code to execute.")

            self._parsed_inputs, self._parsed_outputs = parse_lua_decorators(code)
            inputs = {}
            for inp in self._parsed_inputs:
                name = inp['name']
                inputs[name] = await context.pull(self.id, name)

            timeout = float(self.properties.get("timeout", 30.0))
            await self._run_in_process_lupa(code, inputs, timeout)
            return "Out"
        else:
            return await super().execute(context, trigger_pin)

    async def _run_in_process_lupa(self, code: str, inputs: Dict[str, Any], timeout: float):
        from lupa import LuaRuntime
        lua = LuaRuntime(unpack_returned_tuples=True)

        # Helper to convert lua table to python dict/list recursively
        def lua_to_py(obj):
            if type(obj).__name__ == 'LuaTable':
                d = dict(obj)
                if all(isinstance(k, int) for k in d.keys()):
                    lst = [None] * len(d)
                    for k, v in d.items():
                        if 1 <= k <= len(d):
                            lst[k-1] = lua_to_py(v)
                    return lst
                else:
                    return {k: lua_to_py(v) for k, v in d.items()}
            return obj

        # Helper to convert python dict/list to lua table
        def py_to_lua(obj):
            if isinstance(obj, dict):
                return lua.table(**{k: py_to_lua(v) for k, v in obj.items()})
            elif isinstance(obj, list):
                return lua.table(*[py_to_lua(v) for v in obj])
            return obj

        for name, val in inputs.items():
            lua.globals()[name] = py_to_lua(val)

        def run():
            lua.execute(code)

        try:
            await asyncio.wait_for(
                asyncio.to_thread(run),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Lua script exceeded timeout of {timeout}s.")

        self._computed_outputs = {}
        for out in self._parsed_outputs:
            name = out['name']
            val = lua.globals()[name]
            self._computed_outputs[name] = lua_to_py(val)

    def _generate_script(self, code: str, inputs: Dict[str, Any], output_file_path: str) -> str:
        # Generate inputs injection code
        injection_lines = []
        for name, val in inputs.items():
            if isinstance(val, bool):
                injection_lines.append(f"{name} = {str(val).lower()}")
            elif isinstance(val, (int, float)):
                injection_lines.append(f"{name} = {val}")
            elif isinstance(val, str):
                escaped = val.replace('"', '\\"').replace('\n', '\\n')
                injection_lines.append(f'{name} = "{escaped}"')
            elif isinstance(val, list):
                def to_lua_table(lst):
                    parts = []
                    for item in lst:
                        if isinstance(item, bool): parts.append(str(item).lower())
                        elif isinstance(item, (int, float)): parts.append(str(item))
                        elif isinstance(item, str): parts.append('"' + item.replace('"', '\\"') + '"')
                        elif isinstance(item, list): parts.append(to_lua_table(item))
                        else: parts.append("nil")
                    return "{" + ",".join(parts) + "}"
                injection_lines.append(f"{name} = {to_lua_table(val)}")
            else:
                injection_lines.append(f"{name} = nil")

        injection_code = "\n".join(injection_lines) + "\n\n"

        # Pure-Lua JSON serialization function to output variables back
        lua_json_serializer = """
function serialize_to_json(val)
    if type(val) == "table" then
        local parts = {}
        local is_array = true
        local max_idx = 0
        local count = 0
        for k, _ in pairs(val) do
            if type(k) ~= "number" then
                is_array = false
                break
            end
            if k > max_idx then max_idx = k end
            count = count + 1
        end
        if is_array and count == max_idx then
            for _, v in ipairs(val) do
                table.insert(parts, serialize_to_json(v))
            end
            return "[" .. table.concat(parts, ",") .. "]"
        else
            for k, v in pairs(val) do
                table.insert(parts, '"' .. tostring(k) .. '":' .. serialize_to_json(v))
            end
            return "{" .. table.concat(parts, ",") .. "}"
        end
    elseif type(val) == "string" then
        return '"' .. val:gsub('"', '\\"'):gsub('\\n', '\\\\n') .. '"'
    elseif type(val) == "boolean" then
        return tostring(val)
    elseif type(val) == "number" then
        return tostring(val)
    else
        return "null"
    end
end
"""

        # Append execution extraction script
        out_names_list = ", ".join(f'["{out["name"]}"] = serialize_to_json({out["name"]})' for out in self._parsed_outputs)
        output_script = f"""
{lua_json_serializer}

local out_table = {{ {out_names_list} }}
local out_str = "{{"
local first = true
for k, v in pairs(out_table) do
    if not first then out_str = out_str .. "," end
    out_str = out_str .. '"' .. k .. '":' .. v
    first = false
end
out_str = out_str .. "}}"

local f = io.open("{output_file_path}", "w")
if f then
    f:write(out_str)
    f:close()
end
"""
        return injection_code + code + "\n" + output_script


async def validate_code(code: str) -> dict:
    """Validates Lua script syntax using Lupa or fallback command line assert(load())."""
    try:
        from lupa import LuaRuntime
        lua = LuaRuntime()
        lua.compile(code)
        return {"valid": True}
    except ImportError:
        pass
    except Exception as e:
        return {"valid": False, "error": str(e)}

    if shutil.which("lua"):
        try:
            process = await asyncio.create_subprocess_exec(
                "lua", "-e", "assert(load([[" + code.replace("]]", "\\]\\]") + "]]))",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                return {"valid": True}
            return {"valid": False, "error": stderr.decode().strip() or stdout.decode().strip()}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    return {"valid": True}
