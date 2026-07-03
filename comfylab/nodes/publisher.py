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

import datetime
import re
import json
import asyncio
from pathlib import Path
from comfylab.nodes.base import ExecIn, ExecOut, DataIn, DataOut
from backend.workspace import get_workspace_path

def _build_pin_code(inputs: list, outputs: list) -> dict:
    """Build common pin definition and pull code shared by all language templates."""
    inputs_code = ["ExecIn(\"In\")"]
    for pin in inputs:
        name = pin.get("name")
        type_hint = pin.get("type", "any")
        default = pin.get("default")
        widget = pin.get("widget")
        min_val = pin.get("min")
        max_val = pin.get("max")
        step = pin.get("step")
        options = pin.get("options")
        
        hint_str = "Any"
        if type_hint == "number": hint_str = "float"
        elif type_hint == "boolean": hint_str = "bool"
        elif type_hint == "text" or type_hint == "string": hint_str = "str"
        elif type_hint == "list": hint_str = "list"
        
        args = [f'"{name}"', f'type_hint={hint_str}']
        if default is not None:
            if isinstance(default, str):
                args.append(f'default="{default}"')
            else:
                args.append(f'default={default}')
        if widget:
            args.append(f'widget="{widget}"')
        if min_val is not None:
            args.append(f'min_val={min_val}')
        if max_val is not None:
            args.append(f'max_val={max_val}')
        if step is not None:
            args.append(f'step={step}')
        if options is not None:
            args.append(f'options={json.dumps(options)}')
            
        inputs_code.append(f"DataIn({', '.join(args)})")

    outputs_code = ["ExecOut(\"Out\")"]
    for pin in outputs:
        name = pin.get("name")
        type_hint = pin.get("type", "any")
        
        hint_str = "Any"
        if type_hint == "number": hint_str = "float"
        elif type_hint == "boolean": hint_str = "bool"
        elif type_hint == "text" or type_hint == "string": hint_str = "str"
        elif type_hint == "list": hint_str = "list"
        
        outputs_code.append(f'DataOut("{name}", type_hint={hint_str})')

    pulls_code = []
    for pin in inputs:
        name = pin.get("name")
        pulls_code.append(f'        {name} = await context.pull(self.id, "{name}")')
    
    output_names = [p.get("name") for p in outputs]
    
    return {
        "inputs_joined": ",\n        ".join(inputs_code),
        "outputs_joined": ",\n        ".join(outputs_code),
        "pulls_joined": "\n".join(pulls_code),
        "input_names": [p.get("name") for p in inputs],
        "output_names": output_names,
        "output_names_repr": repr(output_names),
    }


def generate_node_class_code(
    display_name: str,
    class_name: str,
    type_name: str,
    category: str,
    icon: str,
    description: str,
    inputs: list,
    outputs: list,
    original_code: str,
    language: str = "python",
    destination: str = "global",
    clean_name: str = ""
) -> str:
    if language == "python":
        return _build_python_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code)
    elif language == "lua":
        return _build_lua_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code)
    elif language in ("javascript", "typescript"):
        return _build_js_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code, language)
    elif language == "julia":
        return _build_julia_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code)
    elif language == "r":
        return _build_r_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code)
    elif language in ("octave", "matlab"):
        return _build_octave_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code)
    elif language == "wolfram":
        return _build_wolfram_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code)
    elif language == "rust":
        return _build_rust_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code, destination, clean_name)
    else:
        raise ValueError(f"Unsupported language for publishing: {language}")


# ── Template builders ──────────────────────────────────────────────────

def _build_python_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code):
    pc = _build_pin_code(inputs, outputs)
    safe = original_code.replace('"""', '\\\\"\\\\"\\\\"')
    return f"""# Auto-generated by ComfyLAB Node Publisher
# Date: {datetime.date.today().isoformat()}

import sys
import asyncio
from typing import Any
from comfylab.nodes.base import BaseNode, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.engine.registry import register_node
from backend.workspace import get_workspace_path
from comfylab.engine.config import get_config

@register_node("{type_name}")
class {class_name}(BaseNode):
    category = "{category}"
    icon = "{icon}"
    display_name = "{display_name}"
    description = "{description}"
    original_code = \"\"\"{safe}\"\"\"

    inputs_def = [
        {pc["inputs_joined"]}
    ]
    outputs_def = [
        {pc["outputs_joined"]}
    ]

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> str:
{pc["pulls_joined"]}

        namespace = {{
            "context": context,
            "run_id": context.run_id,
            "__builtins__": __builtins__,
        }}
        for pin_name in [p.name for p in self.inputs_def if isinstance(p, DataIn)]:
            namespace[pin_name] = locals().get(pin_name)
        workspace_path = get_workspace_path()
        namespace['workspace'] = str(workspace_path)
        namespace['__file__'] = str(workspace_path / f"node_execute_{{self.id}}.py")
        try:
            import numpy as np
            namespace["np"] = np
            namespace["numpy"] = np
        except ImportError:
            pass
        import math
        namespace["math"] = math
        code = self.properties.get("code", self.original_code)
        try:
            compiled = compile(code, f'<user_node:{{self.id}}>', 'exec')
        except SyntaxError as e:
            raise SyntaxError(f"Script syntax error: {{e}}")
        config = get_config()
        timeout = config.get("script_timeout", 30.0)
        def run_script():
            exec(compiled, namespace)
        workspace_str = str(workspace_path)
        sys.path.insert(0, workspace_str)
        try:
            await asyncio.wait_for(asyncio.to_thread(run_script), timeout=float(timeout))
        except asyncio.TimeoutError:
            raise TimeoutError(f"Node '{{self.id}}' exceeded timeout of {{timeout}}s.")
        finally:
            if workspace_str in sys.path:
                sys.path.remove(workspace_str)
        self._outputs = {{}}
        for pin_name in [p.name for p in self.outputs_def if isinstance(p, DataOut)]:
            if pin_name in namespace:
                self._outputs[pin_name] = namespace[pin_name]
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
        return getattr(self, "_outputs", {{}}).get(pin_name)
"""


def _build_inheritance_template(display_name, class_name, type_name, category, icon, description, original_code,
                                  parent_module, parent_class, parse_func, language, extra_code_lines=""):
    """Generic template: inherit from the language's script node class."""
    safe = original_code.replace('"""', '\\\\"\\\\"\\\\"')
    return f"""# Auto-generated by ComfyLAB Node Publisher
# Date: {datetime.date.today().isoformat()}

from comfylab.nodes.base import ExecIn, ExecOut, DataIn, DataOut
from comfylab.engine.registry import register_node
from {parent_module} import {parent_class}, {parse_func}

EMBEDDED_CODE = \"\"\"{safe}\"\"\"

_parsed_inputs, _parsed_outputs = {parse_func}(EMBEDDED_CODE)

_type_map = {{"number": float, "boolean": bool, "text": str, "string": str, "list": list}}
_STATIC_INPUTS = [ExecIn("In")]
for _inp in _parsed_inputs:
    _kw = {{"type_hint": _type_map.get(_inp.get("type", "any"))}}
    if _inp.get("default") is not None:
        _kw["default"] = _inp["default"]
    if _inp.get("widget"): _kw["widget"] = _inp["widget"]
    if _inp.get("min") is not None: _kw["min_val"] = _inp["min"]
    if _inp.get("max") is not None: _kw["max_val"] = _inp["max"]
    if _inp.get("step") is not None: _kw["step"] = _inp["step"]
    if _inp.get("options") is not None: _kw["options"] = _inp["options"]
    _STATIC_INPUTS.append(DataIn(_inp["name"], **_kw))

_STATIC_OUTPUTS = [ExecOut("Out")]
for _out in _parsed_outputs:
    _STATIC_OUTPUTS.append(DataOut(_out["name"], type_hint=_type_map.get(_out.get("type", "any"))))
{extra_code_lines}

@register_node("{type_name}")
class {class_name}({parent_class}):
    category = "{category}"
    icon = "{icon}"
    display_name = "{display_name}"
    description = "{description}"
    script_language = \"{language}\"
    original_code = EMBEDDED_CODE
    inputs_def = _STATIC_INPUTS
    outputs_def = _STATIC_OUTPUTS

    def __init__(self, node_id, properties=None):
        props = dict(properties or {{}})
        props.setdefault("code", EMBEDDED_CODE)
        super().__init__(node_id, props)
"""


def _build_lua_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code):
    return _build_inheritance_template(display_name, class_name, type_name, category, icon, description, original_code,
        "comfylab.nodes.script_lua", "LuaScriptNode", "parse_lua_decorators", "lua")

def _build_js_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code, language):
    is_ts = language == "typescript"
    parent = "TypeScriptScriptNode" if is_ts else "BaseJavaScriptNode"
    lang_key = "typescript" if is_ts else "javascript"
    return _build_inheritance_template(display_name, class_name, type_name, category, icon, description, original_code,
        "comfylab.nodes.script_js", parent, "parse_js_decorators", lang_key)

def _build_julia_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code):
    return _build_inheritance_template(display_name, class_name, type_name, category, icon, description, original_code,
        "comfylab.nodes.script_julia", "JuliaScriptNode", "parse_script_decorators", "julia",
        "from comfylab.nodes.script import parse_script_decorators")

def _build_r_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code):
    return _build_inheritance_template(display_name, class_name, type_name, category, icon, description, original_code,
        "comfylab.nodes.script_r", "RScriptNode", "parse_script_decorators", "r",
        "from comfylab.nodes.script import parse_script_decorators")

def _build_octave_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code):
    return _build_inheritance_template(display_name, class_name, type_name, category, icon, description, original_code,
        "comfylab.nodes.script_octave", "OctaveScriptNode", "parse_octave_decorators", "octave")

def _build_wolfram_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code):
    return _build_inheritance_template(display_name, class_name, type_name, category, icon, description, original_code,
        "comfylab.nodes.script_wolfram", "WolframScriptNode", "parse_wolfram_decorators", "wolfram")


def _build_rust_template(display_name, class_name, type_name, category, icon, description, inputs, outputs, original_code, destination, clean_name):
    safe = original_code.replace('"""', '\\\\"\\\\"\\\\"')
    
    from comfylab.engine.config import get_comfylab_base_dir
    if destination == "global":
        base = get_comfylab_base_dir() / "rust_nodes"
    else:
        base = get_workspace_path() / "rust_nodes"
    base.mkdir(parents=True, exist_ok=True)
    proj_dir = base / clean_name
    if proj_dir.exists():
        i = 2
        while (base / f"{clean_name}_{i}").exists():
            i += 1
        proj_dir = base / f"{clean_name}_{i}"
    proj_dir_str = str(proj_dir)
    
    return f"""# Auto-generated by ComfyLAB Node Publisher
# Date: {datetime.date.today().isoformat()}

import json
import asyncio
from pathlib import Path
from comfylab.nodes.base import ExecIn, ExecOut, DataIn, DataOut
from comfylab.engine.registry import register_node
from comfylab.nodes.script_rust import RustScriptNode, parse_rust_decorators

EMBEDDED_CODE = \"\"\"{safe}\"\"\"

_parsed_inputs, _parsed_outputs = parse_rust_decorators(EMBEDDED_CODE)

_type_map = {{"number": float, "boolean": bool, "text": str, "string": str, "list": list}}
_STATIC_INPUTS = [ExecIn("In")]
for _inp in _parsed_inputs:
    _kw = {{"type_hint": _type_map.get(_inp.get("type", "any"))}}
    if _inp.get("default") is not None:
        _kw["default"] = _inp["default"]
    if _inp.get("widget"): _kw["widget"] = _inp["widget"]
    if _inp.get("min") is not None: _kw["min_val"] = _inp["min"]
    if _inp.get("max") is not None: _kw["max_val"] = _inp["max"]
    if _inp.get("step") is not None: _kw["step"] = _inp["step"]
    if _inp.get("options") is not None: _kw["options"] = _inp["options"]
    _STATIC_INPUTS.append(DataIn(_inp["name"], **_kw))

_STATIC_OUTPUTS = [ExecOut("Out")]
for _out in _parsed_outputs:
    _STATIC_OUTPUTS.append(DataOut(_out["name"], type_hint=_type_map.get(_out.get("type", "any"))))

_PROJECT_DIR = Path(r"{proj_dir_str}")

@register_node("{type_name}")
class {class_name}(RustScriptNode):
    category = "{category}"
    icon = "{icon}"
    display_name = "{display_name}"
    description = "{description}"
    script_language = "rust"
    original_code = EMBEDDED_CODE
    inputs_def = _STATIC_INPUTS
    outputs_def = _STATIC_OUTPUTS

    def __init__(self, node_id, properties=None):
        props = dict(properties or {{}})
        props.setdefault("code", EMBEDDED_CODE)
        props["persist_cache"] = True
        super().__init__(node_id, props)

    async def _run_cargo_script(self, code, inputs, timeout):
        project_dir = _PROJECT_DIR
        src_dir = project_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        cargo_toml_file = project_dir / "Cargo.toml"
        main_rs_file = src_dir / "main.rs"
        input_file = project_dir / "inputs.json"
        output_file = project_dir / "outputs.json"

        input_file.write_text(json.dumps(inputs), encoding="utf-8")

        def get_rust_type(type_str: str) -> str:
            if type_str == 'number': return 'f64'
            if type_str == 'boolean': return 'bool'
            if type_str in ('text', 'string'): return 'String'
            if type_str == 'list': return 'Vec<serde_json::Value>'
            return 'serde_json::Value'

        input_struct_fields = []
        for inp in self._parsed_inputs:
            name = inp['name']; rust_type = get_rust_type(inp.get('type', 'any'))
            input_struct_fields.append(f\"    {{name}}: {{rust_type}},\")
        output_struct_fields = []
        for out in self._parsed_outputs:
            name = out['name']; rust_type = get_rust_type(out.get('type', 'any'))
            output_struct_fields.append(f\"    {{name}}: {{rust_type}},\")
        input_bindings = []
        for inp in self._parsed_inputs:
            name = inp['name']
            input_bindings.append(f\"    let {{name}} = inputs.{{name}};\")
        output_declarations = []
        for out in self._parsed_outputs:
            name = out['name']; rust_type = get_rust_type(out.get('type', 'any'))
            default_val = {{\"f64\":\"0.0\",\"bool\":\"false\",\"String\":\"String::new()\",\"Vec<serde_json::Value>\":\"Vec::new()\",\"serde_json::Value\":\"serde_json::Value::Null\"}}.get(rust_type, \"serde_json::Value::Null\")
            matching_input = next((i for i in self._parsed_inputs if i['name'] == name), None)
            if matching_input: output_declarations.append(f\"    let mut {{name}} = inputs.{{name}};\")
            else: output_declarations.append(f\"    let mut {{name}} = {{default_val}};\")
        output_instantiations = []
        for out in self._parsed_outputs:
            name = out['name']
            output_instantiations.append(f\"        {{name}},\")

        cargo_toml_file.write_text(\"\"\"[package]
name = \\\"{clean_name}\\\"
version = \\\"0.1.0\\\"
edition = \\\"2021\\\"

[dependencies]
serde = {{ version = \\\"1.0\\\", features = [\\\"derive\\\"] }}
serde_json = \\\"1.0\\\"
\"\"\", encoding=\"utf-8\")

        rust_main_code = \"use serde::{{Serialize, Deserialize}};\\n\"
        rust_main_code += \"use std::fs::File;\\n\"
        rust_main_code += \"use std::io::Write;\\n\"
        rust_main_code += \"\\n\"
        rust_main_code += \"#[derive(Deserialize, Debug)]\\n\"
        rust_main_code += \"struct Inputs {{\\n\"
        rust_main_code += chr(10).join(input_struct_fields) + \"\\n\"
        rust_main_code += \"}}\\n\"
        rust_main_code += \"\\n\"
        rust_main_code += \"#[derive(Serialize, Debug)]\\n\"
        rust_main_code += \"struct Outputs {{\\n\"
        rust_main_code += chr(10).join(output_struct_fields) + \"\\n\"
        rust_main_code += \"}}\\n\"
        rust_main_code += \"\\n\"
        rust_main_code += \"fn main() -> Result<(), Box<dyn std::error::Error>> {{\\n\"
        rust_main_code += f'    let inputs_file = File::open(\"{{input_file.as_posix()}}\")?;\\n'
        rust_main_code += \"    let inputs: Inputs = serde_json::from_reader(inputs_file)?;\\n\"
        rust_main_code += chr(10).join(input_bindings) + \"\\n\"
        rust_main_code += chr(10).join(output_declarations) + \"\\n\"
        rust_main_code += \"    // --- USER CODE ---\\n\"
        rust_main_code += code + \"\\n\"
        rust_main_code += \"    // -----------------\\n\"
        rust_main_code += \"    let outputs = Outputs {{\\n\"
        rust_main_code += chr(10).join(output_instantiations) + \"\\n\"
        rust_main_code += \"    }};\\n\"
        rust_main_code += f'    let mut outputs_file = File::create(\"{{output_file.as_posix()}}\")?;\\n'
        rust_main_code += \"    let json_str = serde_json::to_string(&outputs)?;\\n\"
        rust_main_code += \"    outputs_file.write_all(json_str.as_bytes())?;\\n\"
        rust_main_code += \"    Ok(())\\n\"
        rust_main_code += \"}}\\n\"
        main_rs_file.write_text(rust_main_code, encoding="utf-8")

        try:
            process = await asyncio.create_subprocess_exec(
                "cargo", "run", "--manifest-path", str(cargo_toml_file), "--quiet",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                raise TimeoutError(f"Rust subprocess exceeded timeout of {{timeout}}s.")
            if process.returncode != 0:
                err_msg = stderr.decode().strip() or stdout.decode().strip()
                raise RuntimeError(f"Rust Cargo execution failed with exit code {{process.returncode}}: {{err_msg}}")
            if output_file.exists():
                self._computed_outputs = json.loads(output_file.read_text(encoding="utf-8"))
            else:
                self._computed_outputs = {{}}
        finally:
            if input_file.exists(): input_file.unlink()
            if output_file.exists(): output_file.unlink()
"""
