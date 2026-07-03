import pytest
import tempfile
import json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from comfylab.engine.registry import NODE_REGISTRY
from comfylab.engine.config import get_global_user_macros_dir, get_config
from backend.workspace import set_workspace_path, get_workspace_path

@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    import comfylab.engine.security as security
    security._cached_private_key = None

    base_dir = tmp_path / ".comfylab"
    base_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("comfylab.engine.config.get_comfylab_base_dir", lambda: base_dir)
    monkeypatch.setattr("comfylab.engine.security.get_comfylab_base_dir", lambda: base_dir)
    
    # Generate keys
    from comfylab.engine.security import get_creator_identity
    identity = get_creator_identity()
    
    # Setup workspace
    ws_path = tmp_path / "workspace"
    ws_path.mkdir(parents=True, exist_ok=True)
    set_workspace_path(ws_path)
    
    yield base_dir

def test_macro_publish_authorize_reload_flow():
    client = TestClient(app)
    
    # 1. Publish macro (should automatically sign and authorize)
    payload = {
        "display_name": "Test Macro Node",
        "category": "Test",
        "icon": "📦",
        "description": "A test macro",
        "internal_blueprint": {
            "nodes": [],
            "links": []
        },
        "boundary_pins": {
            "exec_ins": [],
            "exec_outs": [],
            "data_ins": [],
            "data_outs": []
        },
        "destination": "workspace"
    }
    
    # Clear registry of any old macros
    to_remove = [k for k in NODE_REGISTRY if k.startswith("workspace/macro/")]
    for k in to_remove:
        NODE_REGISTRY.pop(k, None)
        
    res = client.post("/nodes/publish_macro", json=payload)
    assert res.status_code == 200
    type_name = res.json()["type"]
    file_path = res.json()["file_path"]
    
    assert type_name in NODE_REGISTRY
    cls = NODE_REGISTRY[type_name]
    assert cls.unauthorized is False  # Now automatically signed and authorized on publish!

def test_macro_unauthorized_auth_reload_flow():
    client = TestClient(app)
    
    ws_path = get_workspace_path()
    macros_dir = ws_path / "macros"
    macros_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a manually written, unsigned macro file
    macro_data = {
        "name": "Unsigned Macro",
        "type_name": "workspace/macro/unsigned_macro",
        "category": "Test",
        "icon": "❌",
        "display_name": "Unsigned Macro",
        "description": "Unsigned macro test",
        "internal_blueprint": {"nodes": [], "links": []},
        "boundary_pins": {"exec_ins": [], "exec_outs": [], "data_ins": [], "data_outs": []}
    }
    
    file_path = macros_dir / "unsigned_macro.macro.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(macro_data, f, indent=2)
        
    # Clear registry of the macro to force fresh loading
    NODE_REGISTRY.pop("workspace/macro/unsigned_macro", None)
    
    # Trigger a reload to load the unsigned macro
    res_reload_init = client.post("/nodes/reload")
    assert res_reload_init.status_code == 200
    
    assert "workspace/macro/unsigned_macro" in NODE_REGISTRY
    cls = NODE_REGISTRY["workspace/macro/unsigned_macro"]
    assert cls.unauthorized is True  # Manually written, unsigned macro should be unauthorized!
    
    # 2. Get unauthorized nodes list
    res_unauth = client.get("/workspace/nodes/unauthorized")
    assert res_unauth.status_code == 200
    unauth_list = res_unauth.json()["unauthorized"]
    assert len(unauth_list) > 0
    assert any(item["filepath"] == str(file_path) for item in unauth_list)
    
    # 3. Authorize the macro via the API
    res_auth = client.post("/workspace/nodes/authorize", json={"filepath": str(file_path)})
    assert res_auth.status_code == 200
    
    # Check registry after authorize (should be dynamically authorized)
    assert "workspace/macro/unsigned_macro" in NODE_REGISTRY
    cls = NODE_REGISTRY["workspace/macro/unsigned_macro"]
    assert cls.unauthorized is False  # Should be authorized now!
    
    # 4. Call reload endpoint
    res_reload = client.post("/nodes/reload")
    assert res_reload.status_code == 200
    
    # Check registry after reload (should persist authorized status because file was signed)
    assert "workspace/macro/unsigned_macro" in NODE_REGISTRY
    cls = NODE_REGISTRY["workspace/macro/unsigned_macro"]
    assert cls.unauthorized is False

