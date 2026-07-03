import asyncio
import pytest
from comfylab.engine.executor import ExecutionEngine
from comfylab.nodes.base import BaseNode, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.engine.registry import register_node, NODE_REGISTRY

# Keep track of teardowns and executions for assertions
TEARDOWN_COUNTS = {}
EXECUTION_COUNTS = {}
PULL_COUNTS = {}

@register_node("test/persistent_dummy")
class PersistentDummyNode(BaseNode):
    inputs_def = [
        ExecIn("In"),
        DataIn("Value", type_hint=float, default=0.0)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Result", type_hint=float)
    ]

    def __init__(self, node_id: str, properties=None):
        super().__init__(node_id, properties)
        TEARDOWN_COUNTS[node_id] = TEARDOWN_COUNTS.get(node_id, 0)
        EXECUTION_COUNTS[node_id] = EXECUTION_COUNTS.get(node_id, 0)
        self.result_val = 0.0

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> str:
        EXECUTION_COUNTS[self.id] = EXECUTION_COUNTS.get(self.id, 0) + 1
        val = await context.pull(self.id, "Value")
        self.result_val = val * 2
        return "Out"

    async def pull_data(self, context: ExecutionContext, pin_name: str) -> float:
        if pin_name == "Result":
            return self.result_val
        return 0.0

    async def teardown(self):
        TEARDOWN_COUNTS[self.id] = TEARDOWN_COUNTS.get(self.id, 0) + 1


@register_node("test/persistent_pull_dummy")
class PersistentPullDummyNode(BaseNode):
    inputs_def = [
        DataIn("Value", type_hint=float, default=0.0)
    ]
    outputs_def = [
        DataOut("Result", type_hint=float)
    ]

    def __init__(self, node_id: str, properties=None):
        super().__init__(node_id, properties)
        TEARDOWN_COUNTS[node_id] = TEARDOWN_COUNTS.get(node_id, 0)
        PULL_COUNTS[node_id] = PULL_COUNTS.get(node_id, 0)

    async def pull_data(self, context: ExecutionContext, output_pin_name: str) -> float:
        PULL_COUNTS[self.id] = PULL_COUNTS.get(self.id, 0) + 1
        val = await context.pull(self.id, "Value")
        return val + 10.0

    async def teardown(self):
        TEARDOWN_COUNTS[self.id] = TEARDOWN_COUNTS.get(self.id, 0) + 1


@pytest.fixture(autouse=True)
def clean_test_logs():
    TEARDOWN_COUNTS.clear()
    EXECUTION_COUNTS.clear()
    PULL_COUNTS.clear()
    if "test/persistent_dummy" not in NODE_REGISTRY:
        NODE_REGISTRY["test/persistent_dummy"] = PersistentDummyNode
    if "test/persistent_pull_dummy" not in NODE_REGISTRY:
        NODE_REGISTRY["test/persistent_pull_dummy"] = PersistentPullDummyNode


@pytest.mark.asyncio
async def test_node_persistence_skips_execution():
    # Setup graph where const -> persistent_dummy -> print
    blueprint = {
        "nodes": [
            {"id": "const", "type": "constants/number", "properties": {"value": 5.0}},
            {"id": "node1", "type": "test/persistent_dummy", "properties": {"isPersistent": True}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_node": "const", "source_pin": "Value", "target_node": "node1", "target_pin": "Value"},
            {"id": "l2", "type": "exec", "source_node": "node1", "source_pin": "Out", "target_node": "print", "target_pin": "In"},
            {"id": "l3", "type": "data", "source_node": "node1", "source_pin": "Result", "target_node": "print", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    
    # 1. First execution
    engine.load_blueprint(blueprint)
    await engine.run(start_node_id="node1", start_pin_name="In")
    
    assert EXECUTION_COUNTS["node1"] == 1
    assert engine.nodes["print"].last_printed == 10.0

    # 2. Second execution - same parameters and inputs, should skip execute()
    engine.load_blueprint(blueprint)
    await engine.run(start_node_id="node1", start_pin_name="In")
    
    assert EXECUTION_COUNTS["node1"] == 1  # Still 1 because execute() was skipped!
    assert engine.nodes["print"].last_printed == 10.0  # Uses cached output value

    # 3. Modify input and run again - should re-execute
    blueprint["nodes"][0]["properties"]["value"] = 8.0
    engine.load_blueprint(blueprint)
    await engine.run(start_node_id="node1", start_pin_name="In")
    
    assert EXECUTION_COUNTS["node1"] == 2  # Re-executed because input changed!
    assert engine.nodes["print"].last_printed == 16.0


@pytest.mark.asyncio
async def test_node_persistence_skips_pull():
    blueprint = {
        "nodes": [
            {"id": "const", "type": "constants/number", "properties": {"value": 4.0}},
            {"id": "pull_node", "type": "test/persistent_pull_dummy", "properties": {"isPersistent": True}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_node": "const", "source_pin": "Value", "target_node": "pull_node", "target_pin": "Value"},
            {"id": "l2", "type": "data", "source_node": "pull_node", "source_pin": "Result", "target_node": "print", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    
    # 1. First pull
    engine.load_blueprint(blueprint)
    await engine.run(start_node_id="print", start_pin_name="In")
    
    assert PULL_COUNTS["pull_node"] == 1
    assert engine.nodes["print"].last_printed == 14.0

    # 2. Second pull - unchanged, should skip pull_data()
    engine.load_blueprint(blueprint)
    await engine.run(start_node_id="print", start_pin_name="In")
    
    assert PULL_COUNTS["pull_node"] == 1  # Skipped!
    assert engine.nodes["print"].last_printed == 14.0

    # 3. Change property of pull node and run again
    blueprint["nodes"][1]["properties"]["new_param"] = "test"
    engine.load_blueprint(blueprint)
    await engine.run(start_node_id="print", start_pin_name="In")
    
    assert PULL_COUNTS["pull_node"] == 2  # Re-evaluated because property changed!


@pytest.mark.asyncio
async def test_no_auto_clear_on_input_change_if_disabled():
    blueprint = {
        "nodes": [
            {"id": "const", "type": "constants/number", "properties": {"value": 5.0}},
            {"id": "node1", "type": "test/persistent_dummy", "properties": {"isPersistent": True, "autoClearPersistent": False}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_node": "const", "source_pin": "Value", "target_node": "node1", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    
    # 1. First run
    engine.load_blueprint(blueprint)
    await engine.run(start_node_id="node1", start_pin_name="In")
    assert EXECUTION_COUNTS["node1"] == 1

    # 2. Modify input but run again with auto-clear disabled
    blueprint["nodes"][0]["properties"]["value"] = 8.0
    engine.load_blueprint(blueprint)
    await engine.run(start_node_id="node1", start_pin_name="In")
    
    assert EXECUTION_COUNTS["node1"] == 2
    assert TEARDOWN_COUNTS.get("node1", 0) == 0  # No teardown called because autoClearPersistent is False!
