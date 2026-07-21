import pytest
import tempfile
import json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from comfylab.engine.registry import BLOCK_REGISTRY
from comfylab.engine.config import get_global_user_clusters_dir, get_config
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

def test_cluster_publish_authorize_reload_flow():
    client = TestClient(app)
    
    # 1. Publish cluster (should automatically sign and authorize)
    payload = {
        "display_name": "Test Cluster Block",
        "category": "Test",
        "icon": "📦",
        "description": "A test cluster",
        "internal_blueprint": {
            "blocks": [],
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
    
    # Clear registry of any old clusters
    to_remove = [k for k in BLOCK_REGISTRY if k.startswith("workspace/cluster/")]
    for k in to_remove:
        BLOCK_REGISTRY.pop(k, None)
        
    res = client.post("/blocks/publish_cluster", json=payload)
    assert res.status_code == 200
    type_name = res.json()["type"]
    file_path = res.json()["file_path"]
    
    assert type_name in BLOCK_REGISTRY
    cls = BLOCK_REGISTRY[type_name]
    assert cls.unauthorized is False  # Now automatically signed and authorized on publish!

def test_cluster_unauthorized_auth_reload_flow():
    client = TestClient(app)
    
    ws_path = get_workspace_path()
    clusters_dir = ws_path / "clusters"
    clusters_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a manually written, unsigned cluster file
    cluster_data = {
        "name": "Unsigned Cluster",
        "type_name": "workspace/cluster/unsigned_cluster",
        "category": "Test",
        "icon": "❌",
        "display_name": "Unsigned Cluster",
        "description": "Unsigned cluster test",
        "internal_blueprint": {"blocks": [], "links": []},
        "boundary_pins": {"exec_ins": [], "exec_outs": [], "data_ins": [], "data_outs": []}
    }
    
    file_path = clusters_dir / "unsigned_cluster.cluster.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(cluster_data, f, indent=2)
        
    # Clear registry of the cluster to force fresh loading
    BLOCK_REGISTRY.pop("workspace/cluster/unsigned_cluster", None)
    
    # Trigger a reload to load the unsigned cluster
    res_reload_init = client.post("/blocks/reload")
    assert res_reload_init.status_code == 200
    
    assert "workspace/cluster/unsigned_cluster" in BLOCK_REGISTRY
    cls = BLOCK_REGISTRY["workspace/cluster/unsigned_cluster"]
    assert cls.unauthorized is True  # Manually written, unsigned cluster should be unauthorized!
    
    # 2. Get unauthorized blocks list
    res_unauth = client.get("/workspace/blocks/unauthorized")
    assert res_unauth.status_code == 200
    unauth_list = res_unauth.json()["unauthorized"]
    assert len(unauth_list) > 0
    assert any(item["filepath"] == str(file_path) for item in unauth_list)
    
    # 3. Authorize the cluster via the API
    res_auth = client.post("/workspace/blocks/authorize", json={"filepath": str(file_path)})
    assert res_auth.status_code == 200
    
    # Check registry after authorize (should be dynamically authorized)
    assert "workspace/cluster/unsigned_cluster" in BLOCK_REGISTRY
    cls = BLOCK_REGISTRY["workspace/cluster/unsigned_cluster"]
    assert cls.unauthorized is False  # Should be authorized now!
    
    # 4. Call reload endpoint
    res_reload = client.post("/blocks/reload")
    assert res_reload.status_code == 200
    
    # Check registry after reload (should persist authorized status because file was signed)
    assert "workspace/cluster/unsigned_cluster" in BLOCK_REGISTRY
    cls = BLOCK_REGISTRY["workspace/cluster/unsigned_cluster"]
    assert cls.unauthorized is False

