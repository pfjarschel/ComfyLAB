import os
import tempfile
import shutil
import pytest
import comfylab.nodes
from comfylab.engine.executor import ExecutionEngine
from backend.workspace import (
    get_workspace_path,
    set_workspace_path,
    get_default_workspace_path,
    _workspace_path,
)


@pytest.fixture(autouse=True)
def reset_workspace_path():
    """Reset the global workspace path state between tests."""
    import backend.workspace as ws_module
    ws_module._workspace_path = None
    yield
    ws_module._workspace_path = None


class TestWorkspaceConfig:

    def test_default_workspace_path(self):
        default = get_default_workspace_path()
        assert default.name == "workspace"
        assert ".comfylab" in str(default)

    def test_get_workspace_creates_directory(self):
        ws = get_workspace_path()
        assert ws.exists()
        assert ws.is_dir()

    def test_set_workspace_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            custom = os.path.join(tmpdir, "my_workspace")
            result = set_workspace_path(custom)
            assert str(result) == os.path.realpath(custom)
            assert os.path.exists(custom)
            assert get_workspace_path() == result

    def test_set_workspace_creates_nested_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "a", "b", "c", "workspace")
            set_workspace_path(nested)
            assert os.path.exists(nested)


class TestScriptNodeWorkspaceIntegration:

    @pytest.mark.asyncio
    async def test_script_runs_in_workspace_cwd(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            set_workspace_path(tmpdir)
            blueprint = {
                "nodes": [
                    {
                        "id": "script",
                        "type": "script/python",
                        "properties": {
                            "code": '# @output name="cwd" type="text"\n\nimport os\ncwd = os.getcwd()\n'
                        }
                    },
                    {"id": "print", "type": "outputs/basic/print", "properties": {}}
                ],
                "links": [
                    {"id": "l1", "type": "exec", "source_node": "script", "source_pin": "Out", "target_node": "print", "target_pin": "In"},
                    {"id": "l2", "type": "data", "source_node": "script", "source_pin": "cwd", "target_node": "print", "target_pin": "Value"}
                ]
            }

            engine = ExecutionEngine()
            engine.load_blueprint(blueprint)
            await engine.run(start_node_id="script", start_pin_name="In")

            assert engine.nodes["print"].last_printed == os.path.realpath(tmpdir)

    @pytest.mark.asyncio
    async def test_script_can_write_file_to_workspace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            set_workspace_path(tmpdir)
            blueprint = {
                "nodes": [
                    {
                        "id": "script",
                        "type": "script/python",
                        "properties": {
                            "code": '# @output name="path" type="text"\n\nwith open("test_output.txt", "w") as f:\n    f.write("hello workspace")\npath = "test_output.txt"\n'
                        }
                    }
                ],
                "links": []
            }

            engine = ExecutionEngine()
            engine.load_blueprint(blueprint)
            await engine.run(start_node_id="script", start_pin_name="In")

            output_file = os.path.join(tmpdir, "test_output.txt")
            assert os.path.exists(output_file)
            with open(output_file) as f:
                assert f.read() == "hello workspace"

    @pytest.mark.asyncio
    async def test_workspace_variable_injected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            set_workspace_path(tmpdir)
            blueprint = {
                "nodes": [
                    {
                        "id": "script",
                        "type": "script/python",
                        "properties": {
                            "code": '# @output name="ws_path" type="text"\n\nws_path = str(workspace)\n'
                        }
                    },
                    {"id": "print", "type": "outputs/basic/print", "properties": {}}
                ],
                "links": [
                    {"id": "l1", "type": "exec", "source_node": "script", "source_pin": "Out", "target_node": "print", "target_pin": "In"},
                    {"id": "l2", "type": "data", "source_node": "script", "source_pin": "ws_path", "target_node": "print", "target_pin": "Value"}
                ]
            }

            engine = ExecutionEngine()
            engine.load_blueprint(blueprint)
            await engine.run(start_node_id="script", start_pin_name="In")

            assert engine.nodes["print"].last_printed == os.path.realpath(tmpdir)

    @pytest.mark.asyncio
    async def test_engine_restores_cwd_after_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            set_workspace_path(tmpdir)

            # Make sure we start from a known-good directory
            os.chdir("/")
            assert os.getcwd() == "/"

            blueprint = {
                "nodes": [
                    {
                        "id": "script",
                        "type": "script/python",
                        "properties": {
                            "code": '# @output name="x" type="number"\n\nx = 1\n'
                        }
                    }
                ],
                "links": []
            }

            engine = ExecutionEngine()
            engine.load_blueprint(blueprint)
            await engine.run(start_node_id="script", start_pin_name="In")

            # After the run, CWD should be restored back to "/"
            assert os.getcwd() == "/"

    @pytest.mark.asyncio
    async def test_script_can_import_custom_module_from_workspace(self):
        import sys
        with tempfile.TemporaryDirectory() as tmpdir:
            set_workspace_path(tmpdir)

            # Write a custom module into the workspace
            module_content = "def calculate_double(val):\n    return val * 2\n"
            module_file = os.path.join(tmpdir, "my_utils.py")
            with open(module_file, "w") as f:
                f.write(module_content)

            blueprint = {
                "nodes": [
                    {
                        "id": "script",
                        "type": "script/python",
                        "properties": {
                            "code": '# @input name="value" type="number" default=6.0\n# @output name="result" type="number"\n\nimport my_utils\nresult = my_utils.calculate_double(value)\n'
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

            assert engine.nodes["print"].last_printed == 12.0

            # Ensure workspace path is cleaned up from sys.path
            assert os.path.realpath(tmpdir) not in sys.path
            assert tmpdir not in sys.path
