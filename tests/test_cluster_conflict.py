import pytest
import tempfile
import json
import logging
from pathlib import Path
from comfylab.engine.registry import BLOCK_REGISTRY, register_block
from comfylab.blocks.base import BaseBlock, ExecIn, DataIn, DataOut
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


def _make_cluster_json(type_name, inner_blocks, boundary_pins=None):
    if boundary_pins is None:
        boundary_pins = {"exec_ins": [], "exec_outs": [], "data_ins": [], "data_outs": []}
    return {
        "name": type_name.split("/")[-1],
        "type_name": type_name,
        "category": "Test",
        "icon": "📦",
        "display_name": type_name.split("/")[-1],
        "description": "",
        "internal_blueprint": {"blocks": inner_blocks, "links": []},
        "boundary_pins": boundary_pins,
    }


def test_broken_cluster_does_not_shadow_working(tmp_path):
    type_name = "user/cluster/test_shadow"

    class DummyBlock(BaseBlock):
        inputs_def = []
        outputs_def = [DataOut("Value", type_hint=float)]

    register_block("test/valid_dep")(DummyBlock)

    good_data = _make_cluster_json(type_name, [{"id": "n1", "type": "test/valid_dep", "position": {}, "properties": {}}])
    bad_data = _make_cluster_json(type_name, [{"id": "n1", "type": "visa/pfj_osc/stale_type", "position": {}, "properties": {}}])

    good_file = tmp_path / "good.cluster.json"
    bad_file = tmp_path / "bad.cluster.json"
    good_file.write_text(json.dumps(good_data))
    bad_file.write_text(json.dumps(bad_data))

    from comfylab.blocks.cluster import load_cluster_from_file

    load_cluster_from_file(str(good_file))
    assert type_name in BLOCK_REGISTRY
    assert getattr(BLOCK_REGISTRY[type_name], "broken", False) is False

    load_cluster_from_file(str(bad_file))
    assert type_name in BLOCK_REGISTRY
    assert getattr(BLOCK_REGISTRY[type_name], "broken", False) is False
    assert "stale_type" not in getattr(BLOCK_REGISTRY[type_name], "broken_reason", "")

    BLOCK_REGISTRY.pop(type_name, None)
    BLOCK_REGISTRY.pop("test/valid_dep", None)


def test_broken_cluster_registered_when_no_good_copy(tmp_path, caplog):
    type_name = "user/cluster/test_broken_standalone"
    bad_data = _make_cluster_json(type_name, [
        {"id": "n1", "type": "visa/pfj_stale/fake_block", "position": {}, "properties": {}},
        {"id": "n2", "type": "math/basic/multiply", "position": {}, "properties": {}},
    ])
    cluster_file = tmp_path / "stale.cluster.json"
    cluster_file.write_text(json.dumps(bad_data))

    from comfylab.blocks.cluster import load_cluster_from_file

    BLOCK_REGISTRY.pop(type_name, None)
    with caplog.at_level(logging.ERROR, logger="comfylab.blocks.cluster"):
        load_cluster_from_file(str(cluster_file))

    assert type_name in BLOCK_REGISTRY
    cls = BLOCK_REGISTRY[type_name]
    assert getattr(cls, "broken", False) is True
    assert "visa/pfj_stale/fake_block" in getattr(cls, "broken_reason", "")
    assert "math/basic/multiply" not in getattr(cls, "broken_reason", "")
    assert any("broken" in r.message.lower() or "missing" in r.message.lower() for r in caplog.records)

    BLOCK_REGISTRY.pop(type_name, None)


def test_register_block_conflict_warning(caplog):
    type_name = "test/conflict_block"

    class BlockA(BaseBlock):
        inputs_def = []
        outputs_def = []
        _cluster_file_path = "/fake/path_a.py"

    class BlockB(BaseBlock):
        inputs_def = []
        outputs_def = []
        _cluster_file_path = "/fake/path_b.py"

    BLOCK_REGISTRY.pop(type_name, None)

    with caplog.at_level(logging.WARNING, logger="comfylab.engine.registry"):
        register_block(type_name)(BlockA)
        caplog.clear()
        register_block(type_name)(BlockB)

    assert any(type_name in r.message and "Duplicate" in r.message for r in caplog.records)
    assert BLOCK_REGISTRY[type_name] is BlockB

    BLOCK_REGISTRY.pop(type_name, None)
