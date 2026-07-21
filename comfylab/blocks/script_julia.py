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

from typing import Any, Dict, Optional

from comfylab.engine.registry import register_block
from comfylab.blocks.base_script import BaseSubprocessScriptBlock
from comfylab.blocks.script import DECORATOR_PATTERN

DEFAULT_JULIA_CODE = """# @input name="value" type="number" default=1.0
# @output name="result" type="number"

result = value * 2
"""


@register_block("script/julia")
class JuliaScriptBlock(BaseSubprocessScriptBlock):
    icon = "👩‍🏫"
    display_name = "Julia Script"
    description = "User-defined Julia code block with decorated inputs and outputs."
    comment_pattern = DECORATOR_PATTERN
    default_code = DEFAULT_JULIA_CODE
    file_extension = ".jl"
    executable_name = "julia"

    def _generate_script(self, code: str, inputs: Dict[str, Any], output_file_path: str) -> str:
        # Generate inputs injection code in Julia syntax
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
                def to_julia_vector(lst):
                    parts = []
                    for item in lst:
                        if isinstance(item, bool): parts.append(str(item).lower())
                        elif isinstance(item, (int, float)): parts.append(str(item))
                        elif isinstance(item, str): parts.append('"' + item.replace('"', '\\"') + '"')
                        elif isinstance(item, list): parts.append(to_julia_vector(item))
                        else: parts.append("nothing")
                    return "[" + ",".join(parts) + "]"
                injection_lines.append(f"{name} = {to_julia_vector(val)}")
            else:
                injection_lines.append(f"{name} = nothing")

        injection_code = "\n".join(injection_lines) + "\n\n"

        # Pure Julia JSON serializer (no external package dependency)
        julia_json_serializer = r"""
function serialize_to_json(val)
    if val === nothing
        return "null"
    elseif isa(val, Bool)
        return val ? "true" : "false"
    elseif isa(val, Number)
        return string(val)
    elseif isa(val, AbstractString)
        return string('"', replace(val, '"' => "\\\""), '"')
    elseif isa(val, AbstractVector) || isa(val, Tuple)
        parts = [serialize_to_json(v) for v in val]
        return string("[", join(parts, ","), "]")
    elseif isa(val, AbstractDict)
        parts = [string('"', replace(string(k), '"' => "\\\""), "\":", serialize_to_json(v)) for (k, v) in val]
        return string("{", join(parts, ","), "}")
    else
        return string('"', replace(string(val), '"' => "\\\""), '"')
    end
end
"""

        # Append execution extraction script
        out_pairs = []
        for out in self._parsed_outputs:
            name = out['name']
            out_pairs.append(f'string("\\"{name}\\\":", serialize_to_json(isdefined(Main, :{name}) ? {name} : nothing))')

        output_script = f"""
{julia_json_serializer}

out_str = string("{{", join([{", ".join(out_pairs)}], ","), "}}")

open("{output_file_path}", "w") do f
    write(f, out_str)
end
"""
        return injection_code + code + "\n" + output_script


async def validate_code(code: str) -> dict:
    """Validates Julia script syntax using julia parser check."""
    import shutil
    import tempfile
    import os
    import asyncio
    if shutil.which("julia"):
        with tempfile.NamedTemporaryFile(suffix=".jl", delete=False, mode="w", encoding="utf-8") as f:
            f.write(code)
            temp_name = f.name
        try:
            process = await asyncio.create_subprocess_exec(
                "julia", "-e", f"Meta.parse(read(\"{temp_name}\", String))",
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
if get_config().get("enable_julia_scripting", False):
    register_block("script/julia")(JuliaScriptBlock)

