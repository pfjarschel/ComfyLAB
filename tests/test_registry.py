import pytest
from comfylab.blocks.base import BaseBlock
from comfylab.engine.registry import register_block, get_block_class, BLOCK_REGISTRY

def test_block_registration():
    @register_block("test/dummy")
    class DummyBlock(BaseBlock):
        pass

    assert "test/dummy" in BLOCK_REGISTRY
    assert get_block_class("test/dummy") is DummyBlock


def test_invalid_class_registration():
    with pytest.raises(TypeError):
        @register_block("test/invalid")
        class NotABlock:
            pass


def test_get_unregistered_block():
    with pytest.raises(KeyError):
        get_block_class("nonexistent/block/type")


def test_all_blocks_schema():
    from comfylab.engine.registry import get_all_blocks_schema
    
    schema = get_all_blocks_schema()
    
    # Check standard and instrument blocks are registered and correctly serialized
    assert "constants/number" in schema
    assert "math/basic/add" in schema
    assert "visa/signal_generator/config_wave" in schema
    assert "visa/oscilloscope/acquire" in schema
    
    number_schema = schema["constants/number"]
    assert number_schema["name"] == "Number"
    assert number_schema["icon"] == "#️⃣"
    assert number_schema["category"] == "CONSTANTS"
    assert number_schema["dataOuts"] == [{"name": "Value", "label": "Value", "type": "number"}]
    
    add_schema = schema["math/basic/add"]
    assert add_schema["name"] == "Add"
    assert add_schema["icon"] == "➕"
    assert add_schema["category"] == "MATH/Basic"
    assert len(add_schema["dataIns"]) == 2
    assert add_schema["dataIns"][0]["name"] == "A"
    assert add_schema["dataIns"][0]["type"] == "number"
    assert add_schema["dataIns"][0]["widget"] == "number"
    assert add_schema["dataIns"][0]["optional"] is False


