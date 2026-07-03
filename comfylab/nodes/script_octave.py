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

import re
import os
from typing import Any, Dict, List, Optional, Tuple

from comfylab.engine.registry import register_node
from comfylab.nodes.base_script import BaseSubprocessScriptNode, parse_decorators

DECORATOR_PATTERN = re.compile(
    r'^%\s*@(input|output)\s+(.*)',
    re.MULTILINE
)

DEFAULT_OCTAVE_CODE = """% @input name="value" type="number" default=1.0
% @output name="result" type="number"

result = value * 2;
"""


def parse_octave_decorators(code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parses Octave-style decorator comments."""
    return parse_decorators(code, DECORATOR_PATTERN)


@register_node("script/octave")
class OctaveScriptNode(BaseSubprocessScriptNode):
    icon = "📐"
    display_name = "Octave Script"
    description = "User-defined GNU Octave code block with decorated inputs and outputs."
    comment_pattern = DECORATOR_PATTERN
    default_code = DEFAULT_OCTAVE_CODE
    file_extension = ".m"
    executable_name = "octave"

    def _get_subprocess_args(self, script_file_path: str) -> List[str]:
        return ["octave", "--no-gui", "--no-window-system", "--silent", "--no-history", script_file_path]

    def _get_subprocess_env(self) -> Optional[Dict[str, str]]:
        env = os.environ.copy()
        env["QT_QPA_PLATFORM"] = "offscreen"
        return env

    def _generate_script(self, code: str, inputs: Dict[str, Any], output_file_path: str) -> str:
        # Map Python values to Octave literals
        def to_octave_literal(val):
            if val is None:
                return "[]"
            elif isinstance(val, bool):
                return "true" if val else "false"
            elif isinstance(val, (int, float)):
                return str(val)
            elif isinstance(val, str):
                escaped = val.replace("'", "''")
                return f"'{escaped}'"
            elif isinstance(val, list):
                parts = [to_octave_literal(v) for v in val]
                return f"{{{', '.join(parts)}}}"
            elif isinstance(val, dict):
                parts = []
                for k, v in val.items():
                    parts.append(f"'{k}'")
                    parts.append(to_octave_literal(v))
                return f"struct({', '.join(parts)})"
            return "[]"

        # Generate inputs injection code in Octave syntax
        injection_lines = []
        for name, val in inputs.items():
            injection_lines.append(f"{name} = {to_octave_literal(val)};")

        injection_code = "\n".join(injection_lines) + "\n\n"

        # Pure-Octave JSON serialization function fallback (no dependencies)
        octave_json_serializer = r"""
function json_str = serialize_to_json(val)
    if isempty(val)
        json_str = 'null';
    elseif islogical(val)
        if val
            json_str = 'true';
        else
            json_str = 'false';
        end
    elseif isnumeric(val)
        if length(val) > 1
            parts = {};
            for i = 1:length(val)
                parts{end+1} = num2str(val(i));
            end
            json_str = ['[', strjoin(parts, ','), ']'];
        else
            json_str = num2str(val);
        end
    elseif ischar(val)
        json_str = ['"', strrep(val, '"', '\"'), '"'];
    elseif iscell(val)
        parts = {};
        for i = 1:length(val)
            parts{end+1} = serialize_to_json(val{i});
        end
        json_str = ['[', strjoin(parts, ','), ']'];
    elseif isstruct(val)
        fields = fieldnames(val);
        parts = {};
        for i = 1:length(fields)
            f = fields{i};
            parts{end+1} = ['"', f, '":', serialize_to_json(val.(f))];
        end
        json_str = ['{', strjoin(parts, ','), '}'];
    else
        json_str = 'null';
    end
end
"""

        # Append execution extraction script
        out_struct_fields = ", ".join(f"'{out['name']}', {out['name']}" for out in self._parsed_outputs)
        output_script = f"""
{octave_json_serializer}

if exist('jsonencode', 'builtin')
    out_str = jsonencode(struct({out_struct_fields}));
else
    out_str = serialize_to_json(struct({out_struct_fields}));
end

fid = fopen('{output_file_path}', 'w');
if fid ~= -1
    fprintf(fid, '%s', out_str);
    fclose(fid);
end
"""
        return injection_code + code + "\n" + output_script


from comfylab.engine.config import get_config
if get_config().get("enable_octave_scripting", False):
    register_node("script/octave")(OctaveScriptNode)
