import asyncio
import pytest
from comfylab.engine.executor import ExecutionEngine
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.engine.registry import register_block, BLOCK_REGISTRY

# Keep track of teardowns and executions for assertions
TEARDOWN_COUNTS = {}
EXECUTION_COUNTS = {}
PULL_COUNTS = {}

@register_block("test/persistent_dummy")
class PersistentDummyBlock(BaseBlock):
    inputs_def = [
        ExecIn("In"),
        DataIn("Value", type_hint=float, default=0.0)
    ]
    outputs_def = [
        ExecOut("Out"),
        DataOut("Result", type_hint=float)
    ]

    def __init__(self, block_id: str, properties=None):
        super().__init__(block_id, properties)
        TEARDOWN_COUNTS[block_id] = TEARDOWN_COUNTS.get(block_id, 0)
        EXECUTION_COUNTS[block_id] = EXECUTION_COUNTS.get(block_id, 0)
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


@register_block("test/persistent_pull_dummy")
class PersistentPullDummyBlock(BaseBlock):
    inputs_def = [
        DataIn("Value", type_hint=float, default=0.0)
    ]
    outputs_def = [
        DataOut("Result", type_hint=float)
    ]

    def __init__(self, block_id: str, properties=None):
        super().__init__(block_id, properties)
        TEARDOWN_COUNTS[block_id] = TEARDOWN_COUNTS.get(block_id, 0)
        PULL_COUNTS[block_id] = PULL_COUNTS.get(block_id, 0)

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
    if "test/persistent_dummy" not in BLOCK_REGISTRY:
        BLOCK_REGISTRY["test/persistent_dummy"] = PersistentDummyBlock
    if "test/persistent_pull_dummy" not in BLOCK_REGISTRY:
        BLOCK_REGISTRY["test/persistent_pull_dummy"] = PersistentPullDummyBlock


@pytest.mark.asyncio
async def test_block_persistence_skips_execution():
    # Setup graph where const -> persistent_dummy -> print
    blueprint = {
        "blocks": [
            {"id": "const", "type": "constants/number", "properties": {"value": 5.0}},
            {"id": "block1", "type": "test/persistent_dummy", "properties": {"isPersistent": True}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_block": "const", "source_pin": "Value", "target_block": "block1", "target_pin": "Value"},
            {"id": "l2", "type": "exec", "source_block": "block1", "source_pin": "Out", "target_block": "print", "target_pin": "In"},
            {"id": "l3", "type": "data", "source_block": "block1", "source_pin": "Result", "target_block": "print", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    
    # 1. First execution
    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="block1", start_pin_name="In")
    
    assert EXECUTION_COUNTS["block1"] == 1
    assert engine.blocks["print"].last_printed == 10.0

    # 2. Second execution - same parameters and inputs, should skip execute()
    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="block1", start_pin_name="In")
    
    assert EXECUTION_COUNTS["block1"] == 1  # Still 1 because execute() was skipped!
    assert engine.blocks["print"].last_printed == 10.0  # Uses cached output value

    # 3. Modify input and run again - should re-execute
    blueprint["blocks"][0]["properties"]["value"] = 8.0
    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="block1", start_pin_name="In")
    
    assert EXECUTION_COUNTS["block1"] == 2  # Re-executed because input changed!
    assert engine.blocks["print"].last_printed == 16.0


@pytest.mark.asyncio
async def test_block_persistence_skips_pull():
    blueprint = {
        "blocks": [
            {"id": "const", "type": "constants/number", "properties": {"value": 4.0}},
            {"id": "pull_block", "type": "test/persistent_pull_dummy", "properties": {"isPersistent": True}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_block": "const", "source_pin": "Value", "target_block": "pull_block", "target_pin": "Value"},
            {"id": "l2", "type": "data", "source_block": "pull_block", "source_pin": "Result", "target_block": "print", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    
    # 1. First pull
    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="print", start_pin_name="In")
    
    assert PULL_COUNTS["pull_block"] == 1
    assert engine.blocks["print"].last_printed == 14.0

    # 2. Second pull - unchanged, should skip pull_data()
    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="print", start_pin_name="In")
    
    assert PULL_COUNTS["pull_block"] == 1  # Skipped!
    assert engine.blocks["print"].last_printed == 14.0

    # 3. Change property of pull block and run again
    blueprint["blocks"][1]["properties"]["new_param"] = "test"
    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="print", start_pin_name="In")
    
    assert PULL_COUNTS["pull_block"] == 2  # Re-evaluated because property changed!


@pytest.mark.asyncio
async def test_no_auto_clear_on_input_change_if_disabled():
    blueprint = {
        "blocks": [
            {"id": "const", "type": "constants/number", "properties": {"value": 5.0}},
            {"id": "block1", "type": "test/persistent_dummy", "properties": {"isPersistent": True, "autoClearPersistent": False}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_block": "const", "source_pin": "Value", "target_block": "block1", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    
    # 1. First run
    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="block1", start_pin_name="In")
    assert EXECUTION_COUNTS["block1"] == 1

    # 2. Modify input but run again with auto-clear disabled
    blueprint["blocks"][0]["properties"]["value"] = 8.0
    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="block1", start_pin_name="In")
    
    assert EXECUTION_COUNTS["block1"] == 2
    assert TEARDOWN_COUNTS.get("block1", 0) == 0  # No teardown called because autoClearPersistent is False!
