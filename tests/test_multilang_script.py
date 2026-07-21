import pytest
import shutil
from comfylab.engine.executor import ExecutionEngine
from comfylab.blocks.script_lua import parse_lua_decorators, LuaScriptBlock
from comfylab.blocks.script_js import parse_js_decorators, JavaScriptScriptBlock, TypeScriptScriptBlock
from comfylab.blocks.script_rust import parse_rust_decorators, RustScriptBlock
from comfylab.blocks.script_julia import JuliaScriptBlock
from comfylab.blocks.script_r import RScriptBlock
from comfylab.blocks.script_octave import parse_octave_decorators, OctaveScriptBlock
from comfylab.blocks.script_wolfram import parse_wolfram_decorators, WolframScriptBlock


class TestParseMultilangDecorators:

    def test_parse_lua_decorators(self):
        code = '-- @input name="voltage" type="number" default=1.0\n-- @output name="result" type="number"\n'
        inputs, outputs = parse_lua_decorators(code)
        assert len(inputs) == 1
        assert len(outputs) == 1
        assert inputs[0]['name'] == 'voltage'
        assert inputs[0]['type'] == 'number'
        assert inputs[0]['default'] == 1.0
        assert outputs[0]['name'] == 'result'
        assert outputs[0]['type'] == 'number'

    def test_parse_js_decorators(self):
        code = '// @input name="x" type="number" default=5.0\n// @output name="doubled" type="number"\n'
        inputs, outputs = parse_js_decorators(code)
        assert len(inputs) == 1
        assert len(outputs) == 1
        assert inputs[0]['name'] == 'x'
        assert inputs[0]['default'] == 5.0
        assert outputs[0]['name'] == 'doubled'

    def test_parse_rust_decorators(self):
        code = '// @input name="val" type="boolean" default=true\n// @output name="out" type="boolean"\n'
        inputs, outputs = parse_rust_decorators(code)
        assert len(inputs) == 1
        assert len(outputs) == 1
        assert inputs[0]['name'] == 'val'
        assert inputs[0]['default'] is True
        assert outputs[0]['name'] == 'out'

    def test_parse_octave_decorators(self):
        code = '% @input name="amp" type="number" default=2.5\n% @output name="out" type="number"\n'
        inputs, outputs = parse_octave_decorators(code)
        assert len(inputs) == 1
        assert len(outputs) == 1
        assert inputs[0]['name'] == 'amp'
        assert inputs[0]['default'] == 2.5
        assert outputs[0]['name'] == 'out'

    def test_parse_wolfram_decorators(self):
        code = '(* @input name="param" type="number" default=3.14 *)\n(* @output name="res" type="number" *)\n'
        inputs, outputs = parse_wolfram_decorators(code)
        assert len(inputs) == 1
        assert len(outputs) == 1
        assert inputs[0]['name'] == 'param'
        assert inputs[0]['default'] == 3.14
        assert outputs[0]['name'] == 'res'


class TestMultilangExecution:

    @pytest.mark.asyncio
    async def test_lua_execution(self):
        # Lua can run either via Lupa or system lua subprocess. We skip only if both are missing.
        try:
            import lupa
            lupa_available = True
        except ImportError:
            lupa_available = False

        if not lupa_available and not shutil.which("lua"):
            pytest.skip("Neither lupa nor lua executable is available in PATH.")

        blueprint = {
            "blocks": [
                {
                    "id": "lua_script",
                    "type": "script/lua",
                    "properties": {
                        "code": '-- @input name="value" type="number" default=5.0\n-- @output name="result" type="number"\n\nresult = value * 3\n'
                    }
                },
                {"id": "print", "type": "outputs/basic/print", "properties": {}}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_block": "lua_script", "source_pin": "Out", "target_block": "print", "target_pin": "In"},
                {"id": "l2", "type": "data", "source_block": "lua_script", "source_pin": "result", "target_block": "print", "target_pin": "Value"}
            ]
        }

        from comfylab.engine.config import update_config
        # Enable it in config so loader registers it
        update_config({"enable_lua_scripting": True})

        # Dynamically import/register block if loader skipped it initially
        from comfylab.engine.registry import register_block
        register_block("script/lua")(LuaScriptBlock)

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)
        await engine.run(start_block_id="lua_script", start_pin_name="In")

        assert engine.blocks["print"].last_printed == 15.0

    @pytest.mark.asyncio
    async def test_js_execution(self):
        if not shutil.which("block"):
            pytest.skip("block executable is not available in PATH.")

        blueprint = {
            "blocks": [
                {
                    "id": "js_script",
                    "type": "script/javascript",
                    "properties": {
                        "code": '// @input name="value" type="number" default=4.0\n// @output name="result" type="number"\n\nresult = value * 2;\n'
                    }
                },
                {"id": "print", "type": "outputs/basic/print", "properties": {}}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_block": "js_script", "source_pin": "Out", "target_block": "print", "target_pin": "In"},
                {"id": "l2", "type": "data", "source_block": "js_script", "source_pin": "result", "target_block": "print", "target_pin": "Value"}
            ]
        }

        from comfylab.engine.registry import register_block
        register_block("script/javascript")(JavaScriptScriptBlock)

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)
        await engine.run(start_block_id="js_script", start_pin_name="In")

        assert engine.blocks["print"].last_printed == 8.0

    @pytest.mark.asyncio
    async def test_julia_execution(self):
        if not shutil.which("julia"):
            pytest.skip("julia executable is not available in PATH.")

        blueprint = {
            "blocks": [
                {
                    "id": "julia_script",
                    "type": "script/julia",
                    "properties": {
                        "code": '# @input name="value" type="number" default=3.0\n# @output name="result" type="number"\n\nresult = value * 4\n'
                    }
                },
                {"id": "print", "type": "outputs/basic/print", "properties": {}}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_block": "julia_script", "source_pin": "Out", "target_block": "print", "target_pin": "In"},
                {"id": "l2", "type": "data", "source_block": "julia_script", "source_pin": "result", "target_block": "print", "target_pin": "Value"}
            ]
        }

        from comfylab.engine.registry import register_block
        register_block("script/julia")(JuliaScriptBlock)

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)
        await engine.run(start_block_id="julia_script", start_pin_name="In")

        assert engine.blocks["print"].last_printed == 12.0

    @pytest.mark.asyncio
    async def test_rust_execution(self):
        if not shutil.which("cargo") or not shutil.which("rustc"):
            pytest.skip("cargo or rustc executables are not available in PATH.")

        blueprint = {
            "blocks": [
                {
                    "id": "rust_script",
                    "type": "script/rust",
                    "properties": {
                        "code": '// @input name="value" type="number" default=2.0\n// @output name="result" type="number"\n\nresult = value * 5.0;\n'
                    }
                },
                {"id": "print", "type": "outputs/basic/print", "properties": {}}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_block": "rust_script", "source_pin": "Out", "target_block": "print", "target_pin": "In"},
                {"id": "l2", "type": "data", "source_block": "rust_script", "source_pin": "result", "target_block": "print", "target_pin": "Value"}
            ]
        }

        from comfylab.engine.registry import register_block
        register_block("script/rust")(RustScriptBlock)

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)
        await engine.run(start_block_id="rust_script", start_pin_name="In")

        assert engine.blocks["print"].last_printed == 10.0

    @pytest.mark.asyncio
    async def test_r_execution(self):
        if not shutil.which("Rscript"):
            pytest.skip("Rscript is not available in PATH.")

        blueprint = {
            "blocks": [
                {
                    "id": "r_script",
                    "type": "script/r",
                    "properties": {
                        "code": '# @input name="value" type="number" default=6.0\n# @output name="result" type="number"\n\nresult <- value * 3\n'
                    }
                },
                {"id": "print", "type": "outputs/basic/print", "properties": {}}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_block": "r_script", "source_pin": "Out", "target_block": "print", "target_pin": "In"},
                {"id": "l2", "type": "data", "source_block": "r_script", "source_pin": "result", "target_block": "print", "target_pin": "Value"}
            ]
        }

        from comfylab.engine.registry import register_block
        register_block("script/r")(RScriptBlock)

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)
        await engine.run(start_block_id="r_script", start_pin_name="In")

        assert engine.blocks["print"].last_printed == 18.0

    @pytest.mark.asyncio
    async def test_octave_execution(self):
        if not shutil.which("octave"):
            pytest.skip("octave is not available in PATH.")

        blueprint = {
            "blocks": [
                {
                    "id": "octave_script",
                    "type": "script/octave",
                    "properties": {
                        "code": '% @input name="value" type="number" default=7.0\n% @output name="result" type="number"\n\nresult = value * 4;\n'
                    }
                },
                {"id": "print", "type": "outputs/basic/print", "properties": {}}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_block": "octave_script", "source_pin": "Out", "target_block": "print", "target_pin": "In"},
                {"id": "l2", "type": "data", "source_block": "octave_script", "source_pin": "result", "target_block": "print", "target_pin": "Value"}
            ]
        }

        from comfylab.engine.registry import register_block
        register_block("script/octave")(OctaveScriptBlock)

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)
        await engine.run(start_block_id="octave_script", start_pin_name="In")

        assert engine.blocks["print"].last_printed == 28.0

    @pytest.mark.asyncio
    async def test_wolfram_execution(self):
        if not shutil.which("wolframscript"):
            pytest.skip("wolframscript is not available in PATH.")

        blueprint = {
            "blocks": [
                {
                    "id": "wolfram_script",
                    "type": "script/wolfram",
                    "properties": {
                        "code": '(* @input name="value" type="number" default=8.0 *)\n(* @output name="result" type="number" *)\n\nresult = value * 5;\n'
                    }
                },
                {"id": "print", "type": "outputs/basic/print", "properties": {}}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_block": "wolfram_script", "source_pin": "Out", "target_block": "print", "target_pin": "In"},
                {"id": "l2", "type": "data", "source_block": "wolfram_script", "source_pin": "result", "target_block": "print", "target_pin": "Value"}
            ]
        }

        from comfylab.engine.registry import register_block
        register_block("script/wolfram")(WolframScriptBlock)

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)
        await engine.run(start_block_id="wolfram_script", start_pin_name="In")

        assert engine.blocks["print"].last_printed == 40.0

