import pytest
import os
import json
import zipfile
import shutil
import tempfile
from pathlib import Path
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.main import app
from backend.workspace import get_workspace_path, set_workspace_path
from comfylab.engine.config import get_config, update_config, get_global_user_nodes_dir, get_global_user_clusters_dir
from comfylab.engine.security import get_creator_identity
from comfylab.engine.registry import NODE_REGISTRY
from comfylab.nodes.base import BaseNode
from comfylab.engine.registry import register_node

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_workspace(monkeypatch):
    """Sets up a clean temp workspace for each test."""
    import comfylab.engine.security as security
    security._cached_private_key = None
    
    temp_dir = tempfile.mkdtemp()
    ws_path = Path(temp_dir) / "workspace"
    ws_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("backend.workspace.get_default_workspace_path", lambda: ws_path)
    set_workspace_path(ws_path)
    
    # Configure clean user config dirs in temp
    user_dir = Path(temp_dir) / "user_comfylab"
    user_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("comfylab.engine.config.get_comfylab_base_dir", lambda: user_dir)
    monkeypatch.setattr("comfylab.engine.security.get_comfylab_base_dir", lambda: user_dir)
    
    # Ensure trusted origins starts empty
    update_config({"trusted_origins": [], "creator_identity": get_creator_identity()})
    
    yield ws_path
    
    shutil.rmtree(temp_dir)


def test_list_packages_empty():
    response = client.get("/workspace/packages")
    assert response.status_code == 200
    assert response.json() == {"packages": []}

def test_package_export_load_and_import():
    # 1. Register a dynamic test node in the workspace nodes dir so it's recognized as custom
    ws_nodes = get_workspace_path() / "nodes"
    ws_nodes.mkdir(parents=True, exist_ok=True)
    node_code = """from comfylab.nodes.base import BaseNode
from comfylab.engine.registry import register_node

@register_node("test/custom_pack_node")
class CustomPackNode(BaseNode):
    pass
"""
    node_file = ws_nodes / "custom_pack_node.py"
    node_file.write_text(node_code, encoding="utf-8")
    
    # Force loading it into the registry
    from comfylab.nodes.loader import load_module_from_filepath
    load_module_from_filepath(str(node_file))
    assert "test/custom_pack_node" in NODE_REGISTRY

    # 2. Define a test blueprint using this custom node
    blueprint = {
        "nodes": [
            {"id": "node_1", "type": "test/custom_pack_node", "properties": {}},
            {"id": "node_2", "type": "constants/number", "properties": {"Value": 42}}
        ],
        "links": []
    }
    
    # 3. Export the package
    export_payload = {
        "filename": "my_test_package.cfy",
        "blueprint": blueprint
    }
    response = client.post("/workspace/packages", json=export_payload)
    assert response.status_code == 200
    export_data = response.json()
    assert export_data["filename"] == "my_test_package.cfy"
    
    package_file = Path(export_data["path"])
    assert package_file.exists()
    
    # Check that zip contains expected files
    with zipfile.ZipFile(package_file, "r") as z:
        names = z.namelist()
        assert "blueprint.json" in names
        assert "nodes/custom_pack_node.py" in names

    # 4. Load package preview
    load_payload = {"filename": "my_test_package.cfy"}
    response = client.post("/workspace/packages/load", json=load_payload)
    assert response.status_code == 200
    preview = response.json()
    assert preview["blueprint"]["nodes"][0]["type"] == "test/custom_pack_node"
    assert len(preview["nodes"]) == 1
    assert preview["nodes"][0]["filename"] == "custom_pack_node.py"
    # Export signs nodes with host's key, so it should be valid and trusted
    assert preview["nodes"][0]["is_valid"] is True
    assert preview["nodes"][0]["is_trusted"] is True

    # 5. Import package to user folder (global ~/.comfylab)
    # We clear NODE_REGISTRY first to verify import loads them
    NODE_REGISTRY.pop("test/custom_pack_node", None)
    # Delete original unsigned workspace node to prevent it overriding the signed imported version on reload
    node_file.unlink()
    
    import_payload = {

        "package_filename": "my_test_package.cfy",
        "destination": "user",
        "trust_and_sign": True,
        "delete_package": True
    }
    response = client.post("/workspace/packages/import", json=import_payload)
    assert response.status_code == 200
    
    # Verify package is deleted
    assert not package_file.exists()
    
    # Verify imported files are in global user directory
    user_nodes_dir = get_global_user_nodes_dir()
    imported_node = user_nodes_dir / "custom_pack_node.py"
    assert imported_node.exists()
    
    # Verify blueprint was saved to workspace blueprints
    imported_bp = get_workspace_path() / "blueprints" / "my_test_package.json"
    assert imported_bp.exists()
    
    # Verify node is loaded back in NODE_REGISTRY and is authorized
    assert "test/custom_pack_node" in NODE_REGISTRY
    cls = NODE_REGISTRY["test/custom_pack_node"]
    assert getattr(cls, "unauthorized", False) is False
    
    # Cleanup registry
    NODE_REGISTRY.pop("test/custom_pack_node", None)

def test_path_traversal_protection():
    ws_path = get_workspace_path()
    packages_dir = ws_path / "packages"
    packages_dir.mkdir(parents=True, exist_ok=True)
    
    malicious_package = packages_dir / "malicious.cfy"
    
    # Create a malicious zip file trying to write to ../outside.txt
    with zipfile.ZipFile(malicious_package, "w") as z:
        z.writestr("blueprint.json", json.dumps({"nodes": [], "links": []}))
        z.writestr("../outside.txt", "hacked")
        
    # Attempt to load it
    load_payload = {"filename": "malicious.cfy"}
    response = client.post("/workspace/packages/load", json=load_payload)
    assert response.status_code == 400
    assert "Path traversal detected" in response.json()["detail"]

def test_nodes_unauthorized_list_and_authorize():
    ws_nodes = get_workspace_path() / "nodes"
    ws_nodes.mkdir(parents=True, exist_ok=True)
    
    # Unsigned file
    node_file = ws_nodes / "unsigned_node.py"
    node_file.write_text("class TestNode: pass", encoding="utf-8")
    
    # Call list unauthorized
    response = client.get("/workspace/nodes/unauthorized")
    assert response.status_code == 200
    unauth = response.json()["unauthorized"]
    assert len(unauth) == 1
    assert unauth[0]["filename"] == "unsigned_node.py"
    assert unauth[0]["is_valid"] is False
    
    # Authorize it
    auth_payload = {"filepath": str(node_file), "all": False}
    response = client.post("/workspace/nodes/authorize", json=auth_payload)
    assert response.status_code == 200
    
    # Verify it is now signed (comments appended)
    from comfylab.engine.security import verify_python_file
    creator, is_valid = verify_python_file(node_file)
    assert is_valid is True
    assert creator == get_creator_identity()
    
    # Verify it is no longer unauthorized
    response = client.get("/workspace/nodes/unauthorized")
    assert response.status_code == 200
    assert len(response.json()["unauthorized"]) == 0


def test_package_export_react_flow_format():
    # 1. Register a dynamic test node in the workspace nodes dir so it's recognized as custom
    ws_nodes = get_workspace_path() / "nodes"
    ws_nodes.mkdir(parents=True, exist_ok=True)
    node_code = """from comfylab.nodes.base import BaseNode
from comfylab.engine.registry import register_node

@register_node("test/custom_pack_node_rf")
class CustomPackNodeRf(BaseNode):
    pass
"""
    node_file = ws_nodes / "custom_pack_node_rf.py"
    node_file.write_text(node_code, encoding="utf-8")
    
    # Force loading it into the registry
    from comfylab.nodes.loader import load_module_from_filepath
    load_module_from_filepath(str(node_file))
    assert "test/custom_pack_node_rf" in NODE_REGISTRY

    # 2. Define a React Flow formatted blueprint using this custom node
    blueprint = {
        "nodes": [
            {
                "id": "node_1",
                "type": "actionNode",
                "data": {
                    "action": "test/custom_pack_node_rf"
                }
            },
            {
                "id": "node_2",
                "type": "actionNode",
                "data": {
                    "action": "constants/number",
                    "value": 42
                }
            }
        ],
        "links": []
    }
    
    # 3. Export the package
    export_payload = {
        "filename": "my_rf_package.cfy",
        "blueprint": blueprint
    }
    response = client.post("/workspace/packages", json=export_payload)
    assert response.status_code == 200
    export_data = response.json()
    assert export_data["filename"] == "my_rf_package.cfy"
    
    package_file = Path(export_data["path"])
    assert package_file.exists()
    
    # Check that zip contains the custom node
    with zipfile.ZipFile(package_file, "r") as z:
        names = z.namelist()
        assert "blueprint.json" in names
        assert "nodes/custom_pack_node_rf.py" in names

    # Cleanup registry
    NODE_REGISTRY.pop("test/custom_pack_node_rf", None)


def test_temporary_package_import():
    # 1. Register a dynamic test node in workspace nodes dir
    ws_nodes = get_workspace_path() / "nodes"
    ws_nodes.mkdir(parents=True, exist_ok=True)
    node_code = """from comfylab.nodes.base import BaseNode
from comfylab.engine.registry import register_node

@register_node("test/custom_temp_node")
class CustomTempNode(BaseNode):
    pass
"""
    node_file = ws_nodes / "custom_temp_node.py"
    node_file.write_text(node_code, encoding="utf-8")
    
    from comfylab.nodes.loader import load_module_from_filepath
    load_module_from_filepath(str(node_file))
    assert "test/custom_temp_node" in NODE_REGISTRY

    # 1.1 Save a mock cluster to workspace clusters dir
    ws_clusters = get_workspace_path() / "clusters"
    ws_clusters.mkdir(parents=True, exist_ok=True)
    cluster_json = {
        "name": "My Temp Cluster",
        "type_name": "workspace/cluster/test_temp_cluster",
        "category": "User/Clusters",
        "icon": "📦",
        "display_name": "My Temp Cluster",
        "description": "Temp test cluster",
        "internal_blueprint": {
            "nodes": [],
            "links": []
        },
        "boundary_pins": {
            "exec_ins": [],
            "exec_outs": [],
            "data_ins": [],
            "data_outs": []
        }
    }
    cluster_file = ws_clusters / "test_temp_cluster.cluster.json"
    cluster_file.write_text(json.dumps(cluster_json), encoding="utf-8")

    from comfylab.nodes.cluster import load_cluster_from_file
    load_cluster_from_file(str(cluster_file))

    # 2. Define blueprint and export package
    blueprint = {
        "nodes": [
            {"id": "node_1", "type": "test/custom_temp_node", "properties": {}},
            {"id": "node_2", "type": "workspace/cluster/test_temp_cluster", "properties": {}}
        ],
        "links": []
    }
    
    export_payload = {
        "filename": "my_temp_package.cfy",
        "blueprint": blueprint
    }
    response = client.post("/workspace/packages", json=export_payload)
    assert response.status_code == 200
    export_data = response.json()
    package_file = Path(export_data["path"])
    
    # 3. Clean up the dynamic node and cluster from registry and delete files
    NODE_REGISTRY.pop("test/custom_temp_node", None)
    NODE_REGISTRY.pop("workspace/cluster/test_temp_cluster", None)
    node_file.unlink()
    cluster_file.unlink()
    
    # 4. Import package temporarily
    import_payload = {
        "package_filename": "my_temp_package.cfy",
        "destination": "workspace",
        "trust_and_sign": True,
        "delete_package": True, # Should be ignored because import_permanent is False
        "import_permanent": False
    }
    response = client.post("/workspace/packages/import", json=import_payload)
    assert response.status_code == 200
    
    # Verify package file is NOT deleted
    assert package_file.exists()
    
    # Verify files are extracted to .temp folders
    assert (get_workspace_path() / "blueprints" / ".temp" / "my_temp_package.json").exists()
    assert (get_workspace_path() / "nodes" / ".temp" / "custom_temp_node.py").exists()
    assert (get_workspace_path() / "clusters" / ".temp" / "test_temp_cluster.cluster.json").exists()
    
    # Verify node and cluster are loaded back in registry
    assert "test/custom_temp_node" in NODE_REGISTRY
    assert "workspace/cluster/test_temp_cluster" in NODE_REGISTRY
    
    # Assert GET /cluster/{type_name} retrieves the temporary cluster definition successfully
    cluster_res = client.get("/cluster/workspace/cluster/test_temp_cluster")
    assert cluster_res.status_code == 200
    assert cluster_res.json()["name"] == "My Temp Cluster"
    
    # Cleanup registry
    NODE_REGISTRY.pop("test/custom_temp_node", None)
    NODE_REGISTRY.pop("workspace/cluster/test_temp_cluster", None)


def test_publish_temp_cluster():
    # 1. POST to /nodes/publish_cluster with destination="temp"
    payload = {
        "display_name": "My Temp Cluster Test",
        "category": "User/Clusters",
        "icon": "📦",
        "description": "Temp cluster for testing",
        "internal_blueprint": {"nodes": [], "links": []},
        "boundary_pins": {"exec_ins": [], "exec_outs": [], "data_ins": [], "data_outs": []},
        "destination": "temp",
        "type_name": "workspace/cluster/my_temp_cluster_test"
    }
    
    # Clear registry if exists
    NODE_REGISTRY.pop("workspace/cluster/my_temp_cluster_test", None)
    
    res = client.post("/nodes/publish_cluster", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["type"] == "workspace/cluster/my_temp_cluster_test"
    
    # 2. GET the cluster definition and check _is_temp is True
    cluster_res = client.get("/cluster/workspace/cluster/my_temp_cluster_test")
    assert cluster_res.status_code == 200
    cluster_data = cluster_res.json()
    assert cluster_data["_is_temp"] is True
    assert cluster_data["name"] == "My Temp Cluster Test"
    
    # Cleanup file
    Path(data["file_path"]).unlink()
    NODE_REGISTRY.pop("workspace/cluster/my_temp_cluster_test", None)


@pytest.mark.asyncio
async def test_executor_local_code_override():
    # 1. Publish a dynamic user node first
    payload = {
        "display_name": "Temp Exec Node",
        "category": "Test",
        "icon": "🚀",
        "description": "Temp exec node",
        "code": "result = value * 2.0",
        "inputs": [
            {"name": "value", "type": "number", "default": 5.0}
        ],
        "outputs": [
            {"name": "result", "type": "number"}
        ],
        "destination": "workspace"
    }
    
    NODE_REGISTRY.pop("workspace/temp_exec_node", None)
    res = client.post("/nodes/publish", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    file_path = Path(data["file_path"])
    
    # 2. Build blueprint running this node but WITH a code override properties["code"] = "result = value + 100.0"
    blueprint = {
        "nodes": [
            {
                "id": "node_override",
                "type": "workspace/temp_exec_node",
                "properties": {
                    "value": 5.0,
                    "code": "# @input name=\"value\" type=\"number\"\n# @output name=\"result\" type=\"number\"\nresult = value + 100.0"
                }
            },
            {
                "id": "print_node",
                "type": "outputs/basic/print",
                "properties": {}
            }
        ],
        "links": [
            {
                "id": "link_exec",
                "type": "exec",
                "source_node": "node_override",
                "source_pin": "Out",
                "target_node": "print_node",
                "target_pin": "In"
            },
            {
                "id": "link_data",
                "type": "data",
                "source_node": "node_override",
                "source_pin": "result",
                "target_node": "print_node",
                "target_pin": "Value"
            }
        ]
    }
    
    from comfylab.engine.executor import ExecutionEngine
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    
    # Run graph execution starting at node_override.In
    await engine.run(start_node_id="node_override", start_pin_name="In")
    
    # Assert printed value is 105.0 (from code override) instead of 10.0 (from original code)
    print_node = engine.nodes["print_node"]
    assert print_node.last_printed == 105.0
    
    # Cleanup files & registry
    file_path.unlink()
    NODE_REGISTRY.pop("workspace/temp_exec_node", None)


@pytest.mark.asyncio
async def test_temp_cleanup_and_clear_endpoint():
    # 1. Register a dynamic test node in the workspace nodes dir so it's recognized as custom
    ws_nodes = get_workspace_path() / "nodes"
    ws_nodes.mkdir(parents=True, exist_ok=True)
    node_code = """from comfylab.nodes.base import BaseNode
from comfylab.engine.registry import register_node

@register_node("test/custom_temp_cleanup_node")
class CustomTempCleanupNode(BaseNode):
    pass
"""
    node_file = ws_nodes / "custom_temp_cleanup_node.py"
    node_file.write_text(node_code, encoding="utf-8")
    
    from comfylab.nodes.loader import load_module_from_filepath
    load_module_from_filepath(str(node_file))
    assert "test/custom_temp_cleanup_node" in NODE_REGISTRY

    # Create package
    blueprint = {
        "nodes": [{"id": "node_1", "type": "test/custom_temp_cleanup_node", "properties": {}}],
        "links": []
    }
    
    export_payload = {
        "filename": "cleanup_test_package.cfy",
        "blueprint": blueprint
    }
    response = client.post("/workspace/packages", json=export_payload)
    assert response.status_code == 200
    export_data = response.json()
    
    # Remove from registry and delete original
    NODE_REGISTRY.pop("test/custom_temp_cleanup_node", None)
    node_file.unlink()
    
    # Import package temporarily
    import_payload = {
        "package_filename": "cleanup_test_package.cfy",
        "destination": "workspace",
        "trust_and_sign": True,
        "delete_package": False,
        "import_permanent": False
    }
    response = client.post("/workspace/packages/import", json=import_payload)
    assert response.status_code == 200
    
    # Verify temp folders exist
    temp_bp = get_workspace_path() / "blueprints" / ".temp" / "cleanup_test_package.json"
    temp_node = get_workspace_path() / "nodes" / ".temp" / "custom_temp_cleanup_node.py"
    assert temp_bp.exists()
    assert temp_node.exists()
    assert "test/custom_temp_cleanup_node" in NODE_REGISTRY
    assert NODE_REGISTRY["test/custom_temp_cleanup_node"].category.startswith("Temporary/")
    
    # Test POST /workspace/packages/clear_temp
    clear_response = client.post("/workspace/packages/clear_temp")
    assert clear_response.status_code == 200
    assert clear_response.json() == {"success": True}
    
    # Verify deleted
    assert not temp_bp.exists()
    assert not temp_node.exists()
    assert "test/custom_temp_cleanup_node" not in NODE_REGISTRY
    
    # Import again temporarily to test that standard load DOES NOT auto-cleanup anymore
    response = client.post("/workspace/packages/import", json=import_payload)
    assert response.status_code == 200
    assert temp_bp.exists()
    assert temp_node.exists()
    assert "test/custom_temp_cleanup_node" in NODE_REGISTRY
    
    # Save a standard blueprint
    bp_save_payload = {
        "filename": "standard_bp.json",
        "blueprint": {"nodes": [], "links": []}
    }
    save_response = client.post("/workspace/blueprints", json=bp_save_payload)
    assert save_response.status_code == 200
    
    # Load the standard blueprint
    load_response = client.get("/workspace/blueprints/standard_bp.json")
    assert load_response.status_code == 200
    
    # Verify temp files are still there (no auto-purge on load anymore)
    assert temp_bp.exists()
    assert temp_node.exists()
    assert "test/custom_temp_cleanup_node" in NODE_REGISTRY
    
    # Test startup event cleanup
    from backend.main import startup_event
    from comfylab.engine.config import update_config
    update_config({"last_workspace": str(get_workspace_path())})
    
    # Trigger startup_event
    await startup_event()
    
    # Verify startup event successfully cleaned up temp files
    assert not temp_bp.exists()
    assert not temp_node.exists()
    
    # Clean up standard blueprint file
    (get_workspace_path() / "blueprints" / "standard_bp.json").unlink()



