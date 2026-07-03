import pytest
import comfylab.nodes
from comfylab.nodes.script import parse_script_decorators, PythonScriptNode
from comfylab.engine.executor import ExecutionEngine


class TestParseScriptDecorators:

    def test_parse_basic_input_output(self):
        code = '# @input name="voltage" type="number" default=1.0\n# @output name="result" type="number"\n\nresult = voltage * 2\n'
        inputs, outputs = parse_script_decorators(code)
        assert len(inputs) == 1
        assert len(outputs) == 1
        assert inputs[0]['name'] == 'voltage'
        assert inputs[0]['type'] == 'number'
        assert inputs[0]['default'] == 1.0
        assert outputs[0]['name'] == 'result'
        assert outputs[0]['type'] == 'number'

    def test_parse_multiple_inputs(self):
        code = (
            '# @input name="a" type="number" default=0.0\n'
            '# @input name="b" type="number" default=0.0\n'
            '# @input name="label" type="text" default="hello"\n'
            '# @output name="sum" type="number"\n'
        )
        inputs, outputs = parse_script_decorators(code)
        assert len(inputs) == 3
        assert inputs[0]['name'] == 'a'
        assert inputs[1]['name'] == 'b'
        assert inputs[2]['name'] == 'label'
        assert inputs[2]['type'] == 'text'
        assert inputs[2]['default'] == 'hello'
        assert len(outputs) == 1

    def test_parse_boolean_input(self):
        code = '# @input name="enable" type="boolean" default=true\n# @output name="result" type="number"\n'
        inputs, outputs = parse_script_decorators(code)
        assert inputs[0]['default'] is True

    def test_parse_boolean_false(self):
        code = '# @input name="flag" type="boolean" default=false\n'
        inputs, _ = parse_script_decorators(code)
        assert inputs[0]['default'] is False

    def test_parse_widget_and_range(self):
        code = '# @input name="power" type="number" default=0.0 widget="slider" min=-10.0 max=10.0 step=0.1\n'
        inputs, _ = parse_script_decorators(code)
        assert inputs[0]['widget'] == 'slider'
        assert inputs[0]['min'] == -10.0
        assert inputs[0]['max'] == 10.0
        assert inputs[0]['step'] == 0.1

    def test_parse_options_array(self):
        code = '# @input name="wave" type="text" default="sine" options=["sine","square","triangle"]\n'
        inputs, _ = parse_script_decorators(code)
        assert inputs[0]['options'] == ['sine', 'square', 'triangle']

    def test_parse_no_decorators(self):
        code = 'result = 42\n'
        inputs, outputs = parse_script_decorators(code)
        assert len(inputs) == 0
        assert len(outputs) == 0

    def test_parse_missing_name_skipped(self):
        code = '# @input type="number" default=1.0\n# @output name="result" type="number"\n'
        inputs, outputs = parse_script_decorators(code)
        assert len(inputs) == 0
        assert len(outputs) == 1

    def test_parse_integer_default(self):
        code = '# @input name="count" type="number" default=10\n'
        inputs, _ = parse_script_decorators(code)
        assert inputs[0]['default'] == 10
        assert isinstance(inputs[0]['default'], int)

    def test_parse_list_type_no_widget(self):
        code = '# @input name="data" type="list"\n# @output name="processed" type="list"\n'
        inputs, outputs = parse_script_decorators(code)
        assert inputs[0]['type'] == 'list'
        assert outputs[0]['type'] == 'list'


class TestPythonScriptNodeExecution:

    @pytest.mark.asyncio
    async def test_basic_script_multiply(self):
        blueprint = {
            "nodes": [
                {"id": "num", "type": "constants/number", "properties": {"value": 5.0}},
                {
                    "id": "script",
                    "type": "script/python",
                    "properties": {
                        "code": '# @input name="value" type="number" default=1.0\n# @output name="result" type="number"\n\nresult = value * 3\n'
                    }
                },
                {"id": "display", "type": "outputs/basic/display", "properties": {}}
            ],
            "links": [
                {"id": "l1", "type": "data", "source_node": "num", "source_pin": "Value", "target_node": "script", "target_pin": "value"},
                {"id": "l2", "type": "exec", "source_node": "script", "source_pin": "Out", "target_node": "display", "target_pin": "In"},
                {"id": "l3", "type": "data", "source_node": "script", "source_pin": "result", "target_node": "display", "target_pin": "Value"}
            ]
        }

        telemetry = {}
        async def cb(run_id, msg):
            if isinstance(msg, dict) and msg.get("type") == "telemetry":
                telemetry[msg["node_id"]] = msg["data"]

        engine = ExecutionEngine()
        engine.telemetry_callback = cb
        engine.load_blueprint(blueprint)
        await engine.run(start_node_id="script", start_pin_name="In")

        assert telemetry["display"] == {"value": 15.0}

    @pytest.mark.asyncio
    async def test_script_multiple_outputs(self):
        blueprint = {
            "nodes": [
                {
                    "id": "script",
                    "type": "script/python",
                    "properties": {
                        "code": '# @input name="x" type="number" default=10.0\n# @output name="doubled" type="number"\n# @output name="tripled" type="number"\n\ndoubled = x * 2\ntripled = x * 3\n'
                    }
                },
                {"id": "print1", "type": "outputs/basic/print", "properties": {}},
                {"id": "print2", "type": "outputs/basic/print", "properties": {}}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_node": "script", "source_pin": "Out", "target_node": "print1", "target_pin": "In"},
                {"id": "l2", "type": "exec", "source_node": "print1", "source_pin": "Out", "target_node": "print2", "target_pin": "In"},
                {"id": "l3", "type": "data", "source_node": "script", "source_pin": "doubled", "target_node": "print1", "target_pin": "Value"},
                {"id": "l4", "type": "data", "source_node": "script", "source_pin": "tripled", "target_node": "print2", "target_pin": "Value"}
            ]
        }

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)
        await engine.run(start_node_id="script", start_pin_name="In")

        assert engine.nodes["print1"].last_printed == 20.0
        assert engine.nodes["print2"].last_printed == 30.0

    @pytest.mark.asyncio
    async def test_script_with_default_input(self):
        blueprint = {
            "nodes": [
                {
                    "id": "script",
                    "type": "script/python",
                    "properties": {
                        "code": '# @input name="value" type="number" default=7.0\n# @output name="result" type="number"\n\nresult = value + 3\n'
                    }
                },
                {"id": "print", "type": "outputs/basic/print", "properties": {}}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_node": "script", "source_pin": "Out", "target_node": "print", "target_pin": "In"},
                {"id": "l2", "type": "data", "source_node": "script", "source_pin": "result", "target_node": "print", "target_pin": "Value"}
            ]
        }

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)
        await engine.run(start_node_id="script", start_pin_name="In")

        assert engine.nodes["print"].last_printed == 10.0

    @pytest.mark.asyncio
    async def test_script_syntax_error(self):
        blueprint = {
            "nodes": [
                {
                    "id": "script",
                    "type": "script/python",
                    "properties": {
                        "code": '# @output name="result" type="number"\n\nresult = 1 +\n'
                    }
                }
            ],
            "links": []
        }

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)

        with pytest.raises(SyntaxError):
            await engine.run(start_node_id="script", start_pin_name="In")

        assert engine.state == "ABORTED"

    @pytest.mark.asyncio
    async def test_script_runtime_error(self):
        blueprint = {
            "nodes": [
                {
                    "id": "script",
                    "type": "script/python",
                    "properties": {
                        "code": '# @output name="result" type="number"\n\nresult = 1 / 0\n'
                    }
                }
            ],
            "links": []
        }

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)

        with pytest.raises(ZeroDivisionError):
            await engine.run(start_node_id="script", start_pin_name="In")

        assert engine.state == "ABORTED"

    @pytest.mark.asyncio
    async def test_script_timeout(self):
        blueprint = {
            "nodes": [
                {
                    "id": "script",
                    "type": "script/python",
                    "properties": {
                        "code": '# @output name="result" type="number"\n\nimport time\ntime.sleep(10)\nresult = 1\n',
                        "timeout": 0.1
                    }
                }
            ],
            "links": []
        }

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)

        with pytest.raises(TimeoutError):
            await engine.run(start_node_id="script", start_pin_name="In")

        assert engine.state == "ABORTED"

    @pytest.mark.asyncio
    async def test_script_empty_code(self):
        blueprint = {
            "nodes": [
                {
                    "id": "script",
                    "type": "script/python",
                    "properties": {"code": ""}
                }
            ],
            "links": []
        }

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)

        with pytest.raises(ValueError, match="no code"):
            await engine.run(start_node_id="script", start_pin_name="In")

    @pytest.mark.asyncio
    async def test_script_with_math_import(self):
        blueprint = {
            "nodes": [
                {
                    "id": "script",
                    "type": "script/python",
                    "properties": {
                        "code": '# @output name="result" type="number"\n\nresult = math.pi\n'
                    }
                },
                {"id": "print", "type": "outputs/basic/print", "properties": {}}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_node": "script", "source_pin": "Out", "target_node": "print", "target_pin": "In"},
                {"id": "l2", "type": "data", "source_node": "script", "source_pin": "result", "target_node": "print", "target_pin": "Value"}
            ]
        }

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)
        await engine.run(start_node_id="script", start_pin_name="In")

        import math
        assert abs(engine.nodes["print"].last_printed - math.pi) < 0.0001

    @pytest.mark.asyncio
    async def test_script_in_for_loop(self):
        blueprint = {
            "nodes": [
                {"id": "loop", "type": "control_flow/loops/for_loop", "properties": {"Count": 3}},
                {
                    "id": "script",
                    "type": "script/python",
                    "properties": {
                        "code": '# @input name="idx" type="number" default=0\n# @output name="result" type="number"\n\nresult = idx * 10\n'
                    }
                },
                {"id": "print", "type": "outputs/basic/print", "properties": {}}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_node": "loop", "source_pin": "LoopBody", "target_node": "script", "target_pin": "In"},
                {"id": "l2", "type": "exec", "source_node": "script", "source_pin": "Out", "target_node": "print", "target_pin": "In"},
                {"id": "l3", "type": "data", "source_node": "loop", "source_pin": "Index", "target_node": "script", "target_pin": "idx"},
                {"id": "l4", "type": "data", "source_node": "script", "source_pin": "result", "target_node": "print", "target_pin": "Value"}
            ]
        }

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)
        await engine.run(start_node_id="loop", start_pin_name="Start")

        assert engine.nodes["print"].last_printed == 20


class TestExternalPythonScriptNodeExecution:

    @pytest.mark.asyncio
    async def test_basic_external_script_multiply(self):
        blueprint = {
            "nodes": [
                {"id": "num", "type": "constants/number", "properties": {"value": 6.0}},
                {
                    "id": "script",
                    "type": "script/python_external",
                    "properties": {
                        "code": '# @input name="value" type="number" default=1.0\n# @output name="result" type="number"\n\nresult = value * 4\n'
                    }
                },
                {"id": "display", "type": "outputs/basic/display", "properties": {}}
            ],
            "links": [
                {"id": "l1", "type": "data", "source_node": "num", "source_pin": "Value", "target_node": "script", "target_pin": "value"},
                {"id": "l2", "type": "exec", "source_node": "script", "source_pin": "Out", "target_node": "display", "target_pin": "In"},
                {"id": "l3", "type": "data", "source_node": "script", "source_pin": "result", "target_node": "display", "target_pin": "Value"}
            ]
        }

        # Dynamically load the node to registry (since loader might have skipped it or run already)
        from comfylab.engine.registry import register_node
        from comfylab.nodes.script_external_python import ExternalPythonScriptNode
        register_node("script/python_external")(ExternalPythonScriptNode)

        telemetry = {}
        async def cb(run_id, msg):
            if isinstance(msg, dict) and msg.get("type") == "telemetry":
                telemetry[msg["node_id"]] = msg["data"]

        engine = ExecutionEngine()
        engine.telemetry_callback = cb
        engine.load_blueprint(blueprint)
        await engine.run(start_node_id="script", start_pin_name="In")

        assert telemetry["display"] == {"value": 24.0}

