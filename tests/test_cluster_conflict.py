import pytest
import tempfile
import json
import logging
from pathlib import Path
from comfylab.engine.registry import NODE_REGISTRY, register_node
from comfylab.nodes.base import BaseNode, ExecIn, DataIn, DataOut
from comfylab.engine.config import get_global_user_clusters_dir, get_config
from backend.workspace import set_workspace_path


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    import comfylab.engine.security as security
    security._cached_private_key = None

    base_dir = tmp_path / ".comfylab"
    base_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("comfylab.engine.config.get_comfylab_base_dir", lambda: base_dir)
    monkeypatch.setattr("comfylab.engine.security.get_comfylab_base_dir", lambda: base_dir)

    from comfylab.engine.security import get_creator_identity
    identity = get_creator_identity()

    ws_path = tmp_path / "workspace"
    ws_path.mkdir(parents=True, exist_ok=True)
    set_workspace_path(ws_path)

    yield base_dir


def _make_cluster_json(type_name, inner_nodes, boundary_pins=None):
    if boundary_pins is None:
        boundary_pins = {"exec_ins": [], "exec_outs": [], "data_ins": [], "data_outs": []}
    return {
        "name": type_name.split("/")[-1],
        "type_name": type_name,
        "category": "Test",
        "icon": "📦",
        "display_name": type_name.split("/")[-1],
        "description": "",
        "internal_blueprint": {"nodes": inner_nodes, "links": []},
        "boundary_pins": boundary_pins,
    }


def test_broken_cluster_does_not_shadow_working(tmp_path):
    type_name = "user/cluster/test_shadow"

    class DummyNode(BaseNode):
        inputs_def = []
        outputs_def = [DataOut("Value", type_hint=float)]

    register_node("test/valid_dep")(DummyNode)

    good_data = _make_cluster_json(type_name, [{"id": "n1", "type": "test/valid_dep", "position": {}, "properties": {}}])
    bad_data = _make_cluster_json(type_name, [{"id": "n1", "type": "visa/pfj_osc/stale_type", "position": {}, "properties": {}}])

    good_file = tmp_path / "good.cluster.json"
    bad_file = tmp_path / "bad.cluster.json"
    good_file.write_text(json.dumps(good_data))
    bad_file.write_text(json.dumps(bad_data))

    from comfylab.nodes.cluster import load_cluster_from_file

    load_cluster_from_file(str(good_file))
    assert type_name in NODE_REGISTRY
    assert getattr(NODE_REGISTRY[type_name], "broken", False) is False

    load_cluster_from_file(str(bad_file))
    assert type_name in NODE_REGISTRY
    assert getattr(NODE_REGISTRY[type_name], "broken", False) is False
    assert "stale_type" not in getattr(NODE_REGISTRY[type_name], "broken_reason", "")

    NODE_REGISTRY.pop(type_name, None)
    NODE_REGISTRY.pop("test/valid_dep", None)


def test_broken_cluster_registered_when_no_good_copy(tmp_path, caplog):
    type_name = "user/cluster/test_broken_standalone"
    bad_data = _make_cluster_json(type_name, [
        {"id": "n1", "type": "visa/pfj_stale/fake_node", "position": {}, "properties": {}},
        {"id": "n2", "type": "math/basic/multiply", "position": {}, "properties": {}},
    ])
    cluster_file = tmp_path / "stale.cluster.json"
    cluster_file.write_text(json.dumps(bad_data))

    from comfylab.nodes.cluster import load_cluster_from_file

    NODE_REGISTRY.pop(type_name, None)
    with caplog.at_level(logging.ERROR, logger="comfylab.nodes.cluster"):
        load_cluster_from_file(str(cluster_file))

    assert type_name in NODE_REGISTRY
    cls = NODE_REGISTRY[type_name]
    assert getattr(cls, "broken", False) is True
    assert "visa/pfj_stale/fake_node" in getattr(cls, "broken_reason", "")
    assert "math/basic/multiply" not in getattr(cls, "broken_reason", "")
    assert any("broken" in r.message.lower() or "missing" in r.message.lower() for r in caplog.records)

    NODE_REGISTRY.pop(type_name, None)


def test_register_node_conflict_warning(caplog):
    type_name = "test/conflict_node"

    class NodeA(BaseNode):
        inputs_def = []
        outputs_def = []
        _cluster_file_path = "/fake/path_a.py"

    class NodeB(BaseNode):
        inputs_def = []
        outputs_def = []
        _cluster_file_path = "/fake/path_b.py"

    NODE_REGISTRY.pop(type_name, None)

    with caplog.at_level(logging.WARNING, logger="comfylab.engine.registry"):
        register_node(type_name)(NodeA)
        caplog.clear()
        register_node(type_name)(NodeB)

    assert any(type_name in r.message and "Duplicate" in r.message for r in caplog.records)
    assert NODE_REGISTRY[type_name] is NodeB

    NODE_REGISTRY.pop(type_name, None)
