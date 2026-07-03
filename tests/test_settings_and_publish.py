import os
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from comfylab.engine.config import (
    get_config,
    save_config,
    update_config,
    get_config_file_path,
    get_global_user_nodes_dir
)
from comfylab.nodes.loader import load_nodes_from_directory
from comfylab.engine.registry import NODE_REGISTRY
from backend.routers.settings import generate_node_class_code

@pytest.fixture
def temp_comfylab_dir(tmp_path, monkeypatch):
    """Mocks the comfylab base directory to a temporary path for test isolation."""
    import comfylab.engine.security as security
    security._cached_private_key = None

    base_dir = tmp_path / ".comfylab"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Patch base dir functions
    monkeypatch.setattr("comfylab.engine.config.get_comfylab_base_dir", lambda: base_dir)
    monkeypatch.setattr("comfylab.engine.security.get_comfylab_base_dir", lambda: base_dir)
    return base_dir

def test_config_defaults_and_saving(temp_comfylab_dir):
    # Verify defaults are retrieved when no file exists
    config = get_config()
    assert config["script_timeout"] == 30.0
    assert config["custom_node_dirs"] == []
    
    # Verify file was created
    config_file = get_config_file_path()
    assert config_file.exists()
    
    # Verify updating configuration updates keys and saves to disk
    update_config({"script_timeout": 45.0, "visa_backend": "@py"})
    updated = get_config()
    assert updated["script_timeout"] == 45.0
    assert updated["visa_backend"] == "@py"
    
    # Read raw JSON to double check
    with open(config_file, "r") as f:
        raw = json.load(f)
    assert raw["script_timeout"] == 45.0

def test_dynamic_node_class_generation():
    inputs = [
        {"name": "voltage", "type": "number", "default": 2.5, "widget": "slider", "min": 0.0, "max": 5.0},
        {"name": "label", "type": "text", "default": "test"}
    ]
    outputs = [
        {"name": "result", "type": "number"}
    ]
    
    code = "result = voltage * 2.0"
    
    class_code = generate_node_class_code(
        display_name="My Calculator",
        class_name="MyCalculatorNode",
        type_name="user/my_calculator",
        category="Test",
        icon="📊",
        description="A test calculator",
        inputs=inputs,
        outputs=outputs,
        original_code=code
    )
    
    # Assert code generation contains expected definitions
    assert '@register_node("user/my_calculator")' in class_code
    assert 'class MyCalculatorNode(BaseNode):' in class_code
    assert 'category = "Test"' in class_code
    assert 'icon = "📊"' in class_code
    assert 'original_code = """result = voltage * 2.0"""' in class_code
    assert 'DataIn("voltage", type_hint=float, default=2.5, widget="slider", min_val=0.0, max_val=5.0)' in class_code
    assert 'DataIn("label", type_hint=str, default="test")' in class_code
    assert 'DataOut("result", type_hint=float)' in class_code
    
    # Verify syntax check compile compiles successfully
    compiled = compile(class_code, "<test_compile>", "exec")
    assert compiled is not None

def test_dynamic_node_loading(temp_comfylab_dir):
    # Setup a dummy node file in a temporary folder
    user_nodes_dir = get_global_user_nodes_dir()
    dummy_node_code = """
from comfylab.nodes.base import BaseNode, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.engine.registry import register_node

@register_node("user/test_dummy_node")
class TestDummyNode(BaseNode):
    category = "Test"
    icon = "🧪"
    display_name = "Dummy Node"
    
    inputs_def = [ExecIn("In")]
    outputs_def = [ExecOut("Out")]
    
    async def execute(self, context, trigger_pin):
        return "Out"
"""
    node_file = user_nodes_dir / "test_dummy_node.py"
    with open(node_file, "w") as f:
        f.write(dummy_node_code)
        
    # Check that it's not in registry yet
    if "user/test_dummy_node" in NODE_REGISTRY:
        del NODE_REGISTRY["user/test_dummy_node"]
        
    # Load nodes from directory
    load_nodes_from_directory(str(user_nodes_dir))
    
    # Verify it was successfully dynamically loaded and registered!
    assert "user/test_dummy_node" in NODE_REGISTRY
    node_class = NODE_REGISTRY["user/test_dummy_node"]
    assert node_class.display_name == "Dummy Node"
    assert node_class.category == "Test"
    assert node_class.icon == "🧪"
    
    # Cleanup registry for standard test consistency
    del NODE_REGISTRY["user/test_dummy_node"]


def test_publish_node_auto_signs(temp_comfylab_dir, tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import app
    from comfylab.engine.security import verify_python_file
    from backend.workspace import set_workspace_path
    
    # Setup workspace
    ws_path = tmp_path / "workspace"
    ws_path.mkdir(parents=True, exist_ok=True)
    set_workspace_path(ws_path)
    
    # Ensure creator identity exists
    from comfylab.engine.security import get_creator_identity
    identity = get_creator_identity()
    
    client = TestClient(app)
    
    payload = {
        "display_name": "Test Publish Node",
        "category": "Test",
        "icon": "🚀",
        "description": "A node published in test",
        "code": "result = value * 3.0",
        "inputs": [
            {"name": "value", "type": "number", "default": 2.0}
        ],
        "outputs": [
            {"name": "result", "type": "number"}
        ],
        "destination": "workspace"
    }
    
    # Clear registry
    NODE_REGISTRY.pop("workspace/test_publish_node", None)
    
    res = client.post("/nodes/publish", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    file_path = Path(data["file_path"])
    
    # 1. Verify file exists
    assert file_path.exists()
    
    # 2. Verify file is signed and creator matches our identity
    creator, is_valid = verify_python_file(file_path)
    assert is_valid is True
    assert creator == identity
    
    # 3. Verify registry state
    assert "workspace/test_publish_node" in NODE_REGISTRY
    cls = NODE_REGISTRY["workspace/test_publish_node"]
    assert cls.unauthorized is False
    
    # 4. Verify editing/updating works and keeps it signed
    payload_edit = payload.copy()
    payload_edit["code"] = "result = value * 5.0"
    
    res_edit = client.post("/nodes/publish", json=payload_edit)
    assert res_edit.status_code == 200
    
    # Verify file is still signed and valid
    creator_edit, is_valid_edit = verify_python_file(file_path)
    assert is_valid_edit is True
    assert creator_edit == identity
    
    # Verify updated registry class
    cls_edit = NODE_REGISTRY["workspace/test_publish_node"]
    assert cls_edit.unauthorized is False

