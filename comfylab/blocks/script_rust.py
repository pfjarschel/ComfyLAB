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
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from comfylab.engine.registry import register_block
from comfylab.blocks.base import ExecutionContext, ExecIn, ExecOut, DataIn, DataOut
from comfylab.blocks.base_script import BaseSubprocessScriptBlock, parse_decorators
from backend.workspace import get_temp_dir, get_workspace_path

DECORATOR_PATTERN = re.compile(
    r'^//\s*@(input|output)\s+(.*)',
    re.MULTILINE
)

DEFAULT_RUST_CODE = """// @input name="value" type="number" default=1.0
// @output name="result" type="number"

result = value * 2.0;
"""


def parse_rust_decorators(code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parses Rust-style decorator comments."""
    return parse_decorators(code, DECORATOR_PATTERN)


@register_block("script/rust")
class RustScriptBlock(BaseSubprocessScriptBlock):
    icon = "🦀"
    display_name = "Rust Script"
    description = "User-defined Rust code block with decorated inputs and outputs."
    comment_pattern = DECORATOR_PATTERN
    default_code = DEFAULT_RUST_CODE
    file_extension = ".rs"
    executable_name = "cargo"

    async def _run_subprocess(self, code: str, inputs: Dict[str, Any], timeout: float):
        persist_cache = self.properties.get("persist_cache", True)
        if persist_cache:
            project_dir = get_workspace_path() / "rust_blocks" / self.id
        else:
            project_dir = get_temp_dir() / f"rust_project_{self.id}"
        src_dir = project_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        cargo_toml_file = project_dir / "Cargo.toml"
        main_rs_file = src_dir / "main.rs"
        input_file = project_dir / "inputs.json"
        output_file = project_dir / "outputs.json"

        # Write inputs JSON file
        input_file.write_text(json.dumps(inputs), encoding="utf-8")

        # Map Python types to Rust types
        def get_rust_type(type_str: str) -> str:
            if type_str == 'number': return 'f64'
            if type_str == 'boolean': return 'bool'
            if type_str in ('text', 'string'): return 'String'
            if type_str == 'list': return 'Vec<serde_json::Value>'
            return 'serde_json::Value'

        # Map dynamic struct fields for inputs
        input_struct_fields = []
        for inp in self._parsed_inputs:
            name = inp['name']
            type_str = inp.get('type', 'any')
            rust_type = get_rust_type(type_str)
            input_struct_fields.append(f"    {name}: {rust_type},")

        # Map dynamic struct fields for outputs
        output_struct_fields = []
        for out in self._parsed_outputs:
            name = out['name']
            type_str = out.get('type', 'any')
            rust_type = get_rust_type(type_str)
            output_struct_fields.append(f"    {name}: {rust_type},")

        # Generate variable bindings for inputs
        input_bindings = []
        for inp in self._parsed_inputs:
            name = inp['name']
            input_bindings.append(f"    let {name} = inputs.{name};")

        # Generate mutable variable definitions and defaults for outputs
        output_declarations = []
        for out in self._parsed_outputs:
            name = out['name']
            type_str = out.get('type', 'any')
            rust_type = get_rust_type(type_str)
            
            # Default values
            default_val = "0.0"
            if rust_type == 'bool': default_val = "false"
            elif rust_type == 'String': default_val = 'String::new()'
            elif rust_type == 'Vec<serde_json::Value>': default_val = "Vec::new()"
            elif rust_type == 'serde_json::Value': default_val = "serde_json::Value::Null"
            
            # Check if this output is also an input (read-write pin)
            matching_input = next((i for i in self._parsed_inputs if i['name'] == name), None)
            if matching_input:
                output_declarations.append(f"    let mut {name} = inputs.{name};")
            else:
                output_declarations.append(f"    let mut {name} = {default_val};")

        # Populate output struct instantiation
        output_instantiations = []
        for out in self._parsed_outputs:
            name = out['name']
            output_instantiations.append(f"        {name},")

        # Write Cargo.toml
        cargo_toml_content = f"""[package]
name = "rust_project_{self.id}"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"
"""
        cargo_toml_file.write_text(cargo_toml_content, encoding="utf-8")

        # Assemble Rust main.rs code
        rust_main_code = f"""use serde::{{Serialize, Deserialize}};
use std::fs::File;
use std::io::Write;

#[derive(Deserialize, Debug)]
struct Inputs {{
{chr(10).join(input_struct_fields)}
}}

#[derive(Serialize, Debug)]
struct Outputs {{
{chr(10).join(output_struct_fields)}
}}

fn main() -> Result<(), Box<dyn std::error::Error>> {{
    // Read inputs file
    let inputs_file = File::open("{input_file.as_posix()}")?;
    let inputs: Inputs = serde_json::from_reader(inputs_file)?;

    // Bind inputs to variables
{chr(10).join(input_bindings)}

    // Declare mutable outputs
{chr(10).join(output_declarations)}

    // --- USER CODE ---
{code}
    // -----------------

    // Write outputs file
    let outputs = Outputs {{
{chr(10).join(output_instantiations)}
    }};
    let mut outputs_file = File::create("{output_file.as_posix()}")?;
    let json_str = serde_json::to_string(&outputs)?;
    outputs_file.write_all(json_str.as_bytes())?;

    Ok(())
}}
"""
        main_rs_file.write_text(rust_main_code, encoding="utf-8")

        try:
            # Run cargo project compilation & execution
            process = await asyncio.create_subprocess_exec(
                "cargo", "run", "--manifest-path", str(cargo_toml_file), "--quiet",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                raise TimeoutError(f"Rust subprocess exceeded compilation/execution timeout of {timeout}s.")

            if process.returncode != 0:
                err_msg = stderr.decode().strip() or stdout.decode().strip()
                raise RuntimeError(f"Rust Cargo execution failed with exit code {process.returncode}: {err_msg}")

            # Read output
            if output_file.exists():
                outputs_data = json.loads(output_file.read_text(encoding="utf-8"))
                self._computed_outputs = outputs_data
            else:
                self._computed_outputs = {}

        finally:
            if input_file.exists():
                input_file.unlink()
            if output_file.exists():
                output_file.unlink()


from comfylab.engine.config import get_config
if get_config().get("enable_rust_scripting", False):
    register_block("script/rust")(RustScriptBlock)
