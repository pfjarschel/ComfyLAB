import pytest
from pathlib import Path
import tempfile
import json
from comfylab.engine.security import (
    get_creator_identity,
    sign_data,
    verify_data,
    sign_python_file,
    verify_python_file,
    sign_json,
    verify_json
)
@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Mocks the comfylab base directory to a temporary path for test isolation."""
    import comfylab.engine.security as security
    security._cached_private_key = None

    base_dir = tmp_path / ".comfylab"
    base_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("comfylab.engine.config.get_comfylab_base_dir", lambda: base_dir)
    monkeypatch.setattr("comfylab.engine.security.get_comfylab_base_dir", lambda: base_dir)
    
    # Generate clean keys and populate config.json
    get_creator_identity()
    
    yield base_dir
def test_creator_identity():
    identity = get_creator_identity()
    assert len(identity) == 64  # Hex Ed25519 public key is 32 bytes = 64 hex characters
    assert all(c in "0123456789abcdef" for c in identity)

def test_sign_verify_raw_data():
    data = b"hello, comfylab world!"
    sig = sign_data(data)
    identity = get_creator_identity()
    
    assert verify_data(data, sig, identity) is True
    # Tampered data should fail
    assert verify_data(b"hello, comfylab world! tampered", sig, identity) is False
    # Tampered signature should fail
    assert verify_data(data, sig[:-5] + "aaaaa", identity) is False
    # Different key should fail (using an arbitrary/invalid public key hex)
    fake_identity = "0" * 64
    assert verify_data(data, sig, fake_identity) is False

def test_sign_verify_python_file():
    content = """def my_block():
    return "result"
"""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(content)
        temp_path = Path(f.name)
        
    try:
        # Sign it
        sign_python_file(temp_path)
        
        # Verify it
        creator, is_valid = verify_python_file(temp_path)
        assert is_valid is True
        assert creator == get_creator_identity()
        
        # Read file to check comments
        lines = temp_path.read_text(encoding="utf-8").splitlines()
        assert lines[-2].startswith("# @creator_identity:")
        assert lines[-1].startswith("# @signature:")
        
        # Tamper the file
        tampered_content = temp_path.read_text(encoding="utf-8") + "\n# some comment"
        temp_path.write_text(tampered_content, encoding="utf-8")
        
        _, is_valid_tampered = verify_python_file(temp_path)
        assert is_valid_tampered is False
    finally:
        temp_path.unlink()

def test_sign_verify_json():
    data = {
        "name": "Test Blueprint",
        "blocks": [
            {"id": "1", "type": "math/basic/add"}
        ],
        "links": []
    }
    
    signed = sign_json(data)
    assert "creator_identity" in signed
    assert "signature" in signed
    assert signed["creator_identity"] == get_creator_identity()
    
    creator, is_valid = verify_json(signed)
    assert is_valid is True
    assert creator == get_creator_identity()
    
    # Tamper value
    tampered_1 = signed.copy()
    tampered_1["name"] = "Tampered Blueprint Name"
    _, is_valid_1 = verify_json(tampered_1)
    assert is_valid_1 is False
    
    # Add key
    tampered_2 = signed.copy()
    tampered_2["new_key"] = "hacked"
    _, is_valid_2 = verify_json(tampered_2)
    assert is_valid_2 is False

def test_dynamic_block_authorization_flow():
    from comfylab.blocks.loader import load_module_from_filepath
    from comfylab.engine.registry import BLOCK_REGISTRY, get_block_class
    
    # 1. Unsigned dynamic block
    code_unsigned = """from comfylab.blocks.base import BaseBlock
from comfylab.engine.registry import register_block

@register_block("test/dynamic_unsigned")
class DynamicUnsignedBlock(BaseBlock):
    pass
"""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(code_unsigned)
        temp_path = Path(f.name)
        
    try:
        load_module_from_filepath(str(temp_path))
        assert "test/dynamic_unsigned" in BLOCK_REGISTRY
        cls = get_block_class("test/dynamic_unsigned")
        assert getattr(cls, "unauthorized", False) is True
    finally:
        temp_path.unlink()
        BLOCK_REGISTRY.pop("test/dynamic_unsigned", None)

    # 2. Signed dynamic block
    code_signed = """from comfylab.blocks.base import BaseBlock
from comfylab.engine.registry import register_block

@register_block("test/dynamic_signed")
class DynamicSignedBlock(BaseBlock):
    pass
"""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(code_signed)
        temp_path = Path(f.name)
        
    try:
        sign_python_file(temp_path)
        load_module_from_filepath(str(temp_path))
        assert "test/dynamic_signed" in BLOCK_REGISTRY
        cls = get_block_class("test/dynamic_signed")
        assert getattr(cls, "unauthorized", False) is False
    finally:
        temp_path.unlink()
        BLOCK_REGISTRY.pop("test/dynamic_signed", None)

def test_unauthorized_block_execution_blocked():
    from comfylab.blocks.base import BaseBlock
    from comfylab.engine.registry import register_block, BLOCK_REGISTRY
    from comfylab.engine.executor import ExecutionEngine
    
    @register_block("test/blocked_block")
    class BlockedBlock(BaseBlock):
        pass
        
    BlockedBlock.unauthorized = True
    
    engine = ExecutionEngine()
    blueprint = {
        "blocks": [
            {"id": "block_1", "type": "test/blocked_block", "properties": {}}
        ],
        "links": []
    }
    
    with pytest.raises(ValueError, match="Cannot execute unauthorized custom block"):
        engine.load_blueprint(blueprint)
        
    BLOCK_REGISTRY.pop("test/blocked_block", None)

