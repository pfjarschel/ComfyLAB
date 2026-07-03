import pytest
from comfylab.nodes.base import BaseNode
from comfylab.engine.registry import register_node, get_node_class, NODE_REGISTRY

def test_node_registration():
    @register_node("test/dummy")
    class DummyNode(BaseNode):
        pass

    assert "test/dummy" in NODE_REGISTRY
    assert get_node_class("test/dummy") is DummyNode


def test_invalid_class_registration():
    with pytest.raises(TypeError):
        @register_node("test/invalid")
        class NotANode:
            pass


def test_get_unregistered_node():
    with pytest.raises(KeyError):
        get_node_class("nonexistent/node/type")


def test_all_nodes_schema():
    from comfylab.engine.registry import get_all_nodes_schema
    
    schema = get_all_nodes_schema()
    
    # Check standard and instrument nodes are registered and correctly serialized
    assert "constants/number" in schema
    assert "math/arithmetic/add" in schema
    assert "visa/signal_generator/config_wave" in schema
    assert "visa/oscilloscope/acquire" in schema
    
    number_schema = schema["constants/number"]
    assert number_schema["name"] == "Number"
    assert number_schema["icon"] == "#️⃣"
    assert number_schema["category"] == "CONSTANTS"
    assert number_schema["dataOuts"] == [{"name": "Value", "label": "Value", "type": "number"}]
    
    add_schema = schema["math/arithmetic/add"]
    assert add_schema["name"] == "Add"
    assert add_schema["icon"] == "➕"
    assert add_schema["category"] == "MATH/Arithmetic"
    assert len(add_schema["dataIns"]) == 2
    assert add_schema["dataIns"][0]["name"] == "A"
    assert add_schema["dataIns"][0]["type"] == "number"
    assert add_schema["dataIns"][0]["widget"] == "number"
    assert add_schema["dataIns"][0]["optional"] is False


