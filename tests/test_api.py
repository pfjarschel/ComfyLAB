import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.main import app
from comfylab.engine.executor import ExecutionEngine
import comfylab.nodes


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Mocks the comfylab base directory to a temporary path for API test isolation."""
    import comfylab.engine.security as security
    security._cached_private_key = None

    base_dir = tmp_path / ".comfylab"
    base_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("comfylab.engine.config.get_comfylab_base_dir", lambda: base_dir)
    monkeypatch.setattr("comfylab.engine.security.get_comfylab_base_dir", lambda: base_dir)
    
    # Generate keys
    from comfylab.engine.security import get_creator_identity
    identity = get_creator_identity()
    
    # Write a default config with a test creator_identity
    config_file = base_dir / "config.json"
    default_config = {
        "custom_node_dirs": [],
        "last_workspace": "",
        "script_timeout": 30.0,
        "visa_backend": "",
        "enable_lua_scripting": False,
        "enable_julia_scripting": False,
        "enable_js_scripting": False,
        "enable_rust_scripting": False,
        "external_python_path": "",
        "creator_identity": identity,
        "trusted_origins": [],
        "custom_users": {}
    }
    import json
    config_file.write_text(json.dumps(default_config, indent=2), encoding="utf-8")
    
    yield base_dir


def test_api_root_and_status():
    client = TestClient(app)
    
    # Verify REST API root
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

    # Verify status API
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json()["state"] == "IDLE"


def test_api_run_endpoint_spawns_task():
    client = TestClient(app)
    
    # Simple blueprint: Constants/Number -> Output/Print
    blueprint = {
        "nodes": [
            {"id": "num", "type": "constants/number", "properties": {"value": 5.5}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            {
                "id": "l1",
                "type": "data",
                "source_node": "num",
                "source_pin": "Value",
                "target_node": "print",
                "target_pin": "Value"
            }
        ]
    }
    
    # Trigger execution
    response = client.post("/run", json=blueprint)
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "started"
    
    # Clean up state
    client.post("/abort")


@pytest.mark.asyncio
async def test_telemetry_generation_via_callbacks():
    # Instantiate engine and register a direct local telemetry callback
    engine = ExecutionEngine()
    received_messages = []

    async def mock_telemetry_callback(run_id: str, msg: dict):
        received_messages.append(msg)

    engine.telemetry_callback = mock_telemetry_callback

    # Blueprint: Constants/Number -> Output/Print
    blueprint = {
        "nodes": [
            {"id": "num", "type": "constants/number", "properties": {"value": 42.0}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            {
                "id": "l1",
                "type": "data",
                "source_node": "num",
                "source_pin": "Value",
                "target_node": "print",
                "target_pin": "Value"
            }
        ]
    }

    engine.load_blueprint(blueprint)
    await engine.run(start_node_id="print", start_pin_name="In")

    # Check that status updates were broadcast
    assert len(received_messages) >= 2
    
    # Should have a 'running' and 'success' status for print node
    print_statuses = [m for m in received_messages if m.get("node_id") == "print"]
    assert len(print_statuses) == 2
    assert print_statuses[0]["status"] == "running"
    assert print_statuses[1]["status"] == "success"


def test_settings_api_preserves_multilang():
    client = TestClient(app)
    
    # Get initial settings
    get_res = client.get("/settings")
    assert get_res.status_code == 200
    initial_data = get_res.json()
    
    # Build updated payload
    payload = {
        "custom_node_dirs": initial_data.get("custom_node_dirs", []),
        "script_timeout": 15.0,
        "visa_backend": initial_data.get("visa_backend", ""),
        "last_workspace": initial_data.get("last_workspace", ""),
        "enable_lua_scripting": True,
        "enable_julia_scripting": False,
        "enable_js_scripting": True,
        "enable_rust_scripting": False
    }
    
    # Save settings
    post_res = client.post("/settings", json=payload)
    assert post_res.status_code == 200
    saved_data = post_res.json()
    
    assert saved_data["script_timeout"] == 15.0
    assert saved_data["enable_lua_scripting"] is True
    assert saved_data["enable_js_scripting"] is True
    assert saved_data["enable_julia_scripting"] is False
    assert saved_data["enable_rust_scripting"] is False
    
    # Retrieve again to verify persistence
    get_res_again = client.get("/settings")
    assert get_res_again.status_code == 200
    final_data = get_res_again.json()
    assert final_data["enable_lua_scripting"] is True
    assert final_data["enable_js_scripting"] is True


def test_blueprint_origin_verification():
    from backend.workspace import set_workspace_path
    from comfylab.engine.config import get_config, update_config
    from pathlib import Path
    import tempfile
    import json

    with tempfile.TemporaryDirectory() as tmpdir:
        set_workspace_path(tmpdir)
        blueprints_dir = Path(tmpdir) / "blueprints"
        blueprints_dir.mkdir(parents=True, exist_ok=True)

        config = get_config()
        current_identity = config.get("creator_identity", "")
        if not current_identity:
            from comfylab.engine.security import get_creator_identity
            current_identity = get_creator_identity()

        update_config({"trusted_origins": ["trusted-identity-1"]})

        client = TestClient(app)

        # Case 1: Matching origin_uuid
        bp_match = {
            "nodes": [],
            "edges": [],
            "origin_uuid": current_identity
        }
        (blueprints_dir / "match.json").write_text(json.dumps(bp_match), encoding="utf-8")

        res = client.get("/workspace/blueprints/match.json")
        assert res.status_code == 200
        assert res.json()["origin_trusted"] is True
        assert res.json()["origin_uuid"] == current_identity

        # Case 2: Missing origin_uuid
        bp_missing = {
            "nodes": [],
            "edges": []
        }
        (blueprints_dir / "missing.json").write_text(json.dumps(bp_missing), encoding="utf-8")

        res = client.get("/workspace/blueprints/missing.json")
        assert res.status_code == 200
        assert res.json()["origin_trusted"] is False
        assert "no creator metadata" in res.json()["origin_warning"]
        assert res.json()["origin_uuid"] == ""

        # Case 3: Trusted origin_uuid
        bp_trusted = {
            "nodes": [],
            "edges": [],
            "origin_uuid": "trusted-identity-1"
        }
        (blueprints_dir / "trusted.json").write_text(json.dumps(bp_trusted), encoding="utf-8")

        res = client.get("/workspace/blueprints/trusted.json")
        assert res.status_code == 200
        assert res.json()["origin_trusted"] is True

        # Case 4: Untrusted origin_uuid (mismatch)
        bp_untrusted = {
            "nodes": [],
            "edges": [],
            "origin_uuid": "untrusted-uuid"
        }
        (blueprints_dir / "untrusted.json").write_text(json.dumps(bp_untrusted), encoding="utf-8")

        res = client.get("/workspace/blueprints/untrusted.json")
        assert res.status_code == 200
        assert res.json()["origin_trusted"] is False
        assert "created by developer" in res.json()["origin_warning"]
        assert res.json()["origin_uuid"] == "untrusted-uuid"


def test_save_settings_preserves_custom_users_and_identity():
    from comfylab.engine.config import get_config, update_config
    
    # Save a mock user and creator identity in config
    update_config({
        "custom_users": {"test_user": "secret_pwd"},
        "creator_identity": "some-creator-identity",
        "trusted_origins": ["some-trusted-origin"]
    })
    
    client = TestClient(app)
    
    # Verify GET /settings does NOT leak custom_users
    get_res = client.get("/settings")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert "custom_users" not in get_data
    assert get_data["creator_identity"] == "some-creator-identity"
    
    # POST settings without custom_users, creator_identity, and trusted_origins
    payload = {
        "custom_node_dirs": [],
        "script_timeout": 20.0,
        "visa_backend": "",
        "last_workspace": "",
        "enable_lua_scripting": False,
        "enable_julia_scripting": False,
        "enable_js_scripting": False,
        "enable_rust_scripting": False,
        "enable_r_scripting": False,
        "enable_octave_scripting": False,
        "enable_wolfram_scripting": False,
        "external_python_path": "/usr/bin/python3"
    }
    
    post_res = client.post("/settings", json=payload)
    assert post_res.status_code == 200
    
    # Verify configuration on disk preserved the sensitive values
    config = get_config()
    assert config["custom_users"] == {"test_user": "secret_pwd"}
    assert config["creator_identity"] == "some-creator-identity"
    assert config["trusted_origins"] == ["some-trusted-origin"]
    assert config["script_timeout"] == 20.0
    assert config["external_python_path"] == "/usr/bin/python3"


def test_clear_node_data_endpoint():
    from backend.routers.execution import engine
    client = TestClient(app)
    
    # 1. Test clearing a node that is not loaded (graceful skip)
    response = client.post("/nodes/nonexistent_node/clear")
    assert response.status_code == 200
    assert response.json()["status"] == "skipped"
    assert "not loaded" in response.json()["reason"]
    
    # 2. Test clearing a node that is loaded
    blueprint = {
        "nodes": [
            {"id": "test_print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": []
    }
    # Load blueprint directly to instantiate the nodes
    engine.load_blueprint(blueprint)
    
    # Clear the node
    response = client.post("/nodes/test_print/clear")
    assert response.status_code == 200
    assert response.json()["status"] == "success"





