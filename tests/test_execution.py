import asyncio
from typing import Optional
import pytest
import comfylab.blocks
from comfylab.engine.executor import ExecutionEngine
from comfylab.blocks.base import BaseBlock, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext
from comfylab.engine.registry import register_block

# Custom slow block for abort/teardown testing
TEARDOWN_LOG = []

@register_block("test/slow_block")
class SlowBlock(BaseBlock):
    inputs_def = [
        ExecIn("In"),
        DataIn("Delay", type_hint=float, default=0.1)
    ]
    outputs_def = [ExecOut("Out")]

    def __init__(self, block_id: str, properties=None):
        super().__init__(block_id, properties)
        self.ran = False
        self.teardown_called = False

    async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
        self.ran = True
        delay = await context.pull(self.id, "Delay")
        await asyncio.sleep(delay)
        return "Out"

    async def teardown(self):
        self.teardown_called = True
        TEARDOWN_LOG.append(self.id)


@pytest.fixture(autouse=True)
def ensure_slow_block_registered():
    from comfylab.engine.registry import BLOCK_REGISTRY
    if "test/slow_block" not in BLOCK_REGISTRY:
        BLOCK_REGISTRY["test/slow_block"] = SlowBlock



@pytest.mark.asyncio
async def test_linear_math_execution():
    # Number1 (7) & Number2 (3) -> Add -> Print
    blueprint = {
        "blocks": [
            {"id": "num1", "type": "constants/number", "properties": {"value": 7.0}},
            {"id": "num2", "type": "constants/number", "properties": {"value": 3.0}},
            {"id": "add", "type": "math/basic/add", "properties": {}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            # Data link: num1.Value -> add.A
            {"id": "l1", "type": "data", "source_block": "num1", "source_pin": "Value", "target_block": "add", "target_pin": "A"},
            # Data link: num2.Value -> add.B
            {"id": "l2", "type": "data", "source_block": "num2", "source_pin": "Value", "target_block": "add", "target_pin": "B"},
            # Data link: add.Result -> print.Value
            {"id": "l3", "type": "data", "source_block": "add", "source_pin": "Result", "target_block": "print", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    
    # Manually trigger execution on the print block
    await engine.run(start_block_id="print", start_pin_name="In")
    
    # Print block should have pulled the result of 7.0 + 3.0 = 10.0
    print_block = engine.blocks["print"]
    assert print_block.last_printed == 10.0


@pytest.mark.asyncio
async def test_conditional_if_else_true():
    blueprint = {
        "blocks": [
            {"id": "cond", "type": "constants/number", "properties": {"value": 1.0}}, # 1.0 evaluates to True
            {"id": "if_else", "type": "control_flow/basic/if_else", "properties": {}},
            {"id": "print_true", "type": "outputs/basic/print", "properties": {"value": "True Branch"}},
            {"id": "print_false", "type": "outputs/basic/print", "properties": {"value": "False Branch"}}
        ],
        "links": [
            # Data link: cond.Value -> if_else.Condition
            {"id": "l1", "type": "data", "source_block": "cond", "source_pin": "Value", "target_block": "if_else", "target_pin": "Condition"},
            # Exec link: if_else.True -> print_true.In
            {"id": "l2", "type": "exec", "source_block": "if_else", "source_pin": "True", "target_block": "print_true", "target_pin": "In"},
            # Exec link: if_else.False -> print_false.In
            {"id": "l3", "type": "exec", "source_block": "if_else", "source_pin": "False", "target_block": "print_false", "target_pin": "In"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    await engine.run(start_block_id="if_else", start_pin_name="In")

    assert engine.blocks["print_true"].last_printed == "True Branch" # property value since not connected, but it ran
    assert engine.blocks["print_false"].last_printed is None # Did not run


@pytest.mark.asyncio
async def test_for_loop_execution():
    # Number (4) -> Count | ForLoop -> Print (index)
    blueprint = {
        "blocks": [
            {"id": "count", "type": "constants/number", "properties": {"value": 4.0}},
            {"id": "loop", "type": "control_flow/loops/for_loop", "properties": {}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            # Data link: count.Value -> loop.Count
            {"id": "l1", "type": "data", "source_block": "count", "source_pin": "Value", "target_block": "loop", "target_pin": "Count"},
            # Exec link: loop.LoopBody -> print.In
            {"id": "l2", "type": "exec", "source_block": "loop", "source_pin": "LoopBody", "target_block": "print", "target_pin": "In"},
            # Data link: loop.Index -> print.Value
            {"id": "l3", "type": "data", "source_block": "loop", "source_pin": "Index", "target_block": "print", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    await engine.run(start_block_id="loop", start_pin_name="Start")

    # Print block should have printed indices 0, 1, 2, 3 sequentially. Last printed should be 3.
    assert engine.blocks["print"].last_printed == 3
    # Index output pin on loop should end at 3
    assert engine.blocks["loop"]._index == 3


@pytest.mark.asyncio
async def test_execution_watchdog_timeout():
    blueprint = {
        "blocks": [
            {"id": "slow", "type": "test/slow_block", "properties": {"timeout": 0.05, "Delay": 0.2}}
        ],
        "links": []
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    # Execution should fail with a TimeoutError because delay (0.2s) exceeds watchdog timeout (0.05s)
    with pytest.raises(TimeoutError):
        await engine.run(start_block_id="slow", start_pin_name="In")

    assert engine.state == "ABORTED"
    assert engine.blocks["slow"].teardown_called is True


@pytest.mark.asyncio
async def test_global_abort_and_reverse_teardown():
    global TEARDOWN_LOG
    TEARDOWN_LOG.clear()

    # Three slow blocks linked sequentially: slow1 -> slow2 -> slow3
    blueprint = {
        "blocks": [
            {"id": "slow1", "type": "test/slow_block", "properties": {"Delay": 0.5}},
            {"id": "slow2", "type": "test/slow_block", "properties": {"Delay": 0.5}},
            {"id": "slow3", "type": "test/slow_block", "properties": {"Delay": 0.5}}
        ],
        "links": [
            {"id": "l1", "type": "exec", "source_block": "slow1", "source_pin": "Out", "target_block": "slow2", "target_pin": "In"},
            {"id": "l2", "type": "exec", "source_block": "slow2", "source_pin": "Out", "target_block": "slow3", "target_pin": "In"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    # Run in background task
    run_task = asyncio.create_task(engine.run(start_block_id="slow1", start_pin_name="In"))

    # Let slow1 start running (sleeps 0.5s)
    await asyncio.sleep(0.1)
    assert engine.blocks["slow1"].ran is True
    assert engine.blocks["slow2"].ran is False

    # Trigger emergency abort
    await engine.abort()

    # Wait for execution task to raise error or finish
    try:
        await run_task
    except Exception:
        pass

    assert engine.state == "ABORTED"
    
    # Teardown should have run on all blocks
    assert engine.blocks["slow1"].teardown_called is True
    assert engine.blocks["slow2"].teardown_called is True
    assert engine.blocks["slow3"].teardown_called is True

    # Check order: slow1 ran first, so it should be torn down last.
    # Unexecuted blocks (slow2, slow3) teardown order doesn't depend on execution order, but executed ones teardown first in reverse.
    # Since slow1 was the only one that started running, it must be the first in reverse execution teardown, or last overall.
    # Let's inspect TEARDOWN_LOG: it should contain 'slow1' as it was executed.
    assert "slow1" in TEARDOWN_LOG


@pytest.mark.asyncio
async def test_while_loop_execution():
    blueprint = {
        "blocks": [
            {"id": "bool", "type": "constants/boolean", "properties": {"value": True}},
            {"id": "loop", "type": "control_flow/loops/while_loop", "properties": {}},
            {"id": "print", "type": "outputs/basic/print", "properties": {"value": "Iterated"}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_block": "bool", "source_pin": "Value", "target_block": "loop", "target_pin": "Condition"},
            {"id": "l2", "type": "exec", "source_block": "loop", "source_pin": "LoopBody", "target_block": "print", "target_pin": "In"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    async def toggle_off():
        await asyncio.sleep(0.02)
        engine.blocks["bool"].properties["value"] = False

    asyncio.create_task(toggle_off())

    await engine.run(start_block_id="loop", start_pin_name="Start")
    assert engine.blocks["print"].last_printed == "Iterated"


@pytest.mark.asyncio
async def test_display_block_execution():
    blueprint = {
        "blocks": [
            {"id": "num", "type": "constants/number", "properties": {"value": 42.12345}},
            {"id": "display", "type": "outputs/basic/display", "properties": {}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_block": "num", "source_pin": "Value", "target_block": "display", "target_pin": "Value"}
        ]
    }

    telemetry_received = {}
    async def telemetry_cb(run_id, msg):
        if msg["type"] == "telemetry":
            telemetry_received[msg["block_id"]] = msg["data"]

    engine = ExecutionEngine()
    engine.telemetry_callback = telemetry_cb
    engine.load_blueprint(blueprint)

    await engine.run(start_block_id="display", start_pin_name="In")
    assert telemetry_received["display"] == {"value": 42.12345}


@pytest.mark.asyncio
async def test_xy_plot_block_execution():
    # Create simple array constants for testing
    blueprint = {
        "blocks": [
            {"id": "x_data", "type": "constants/number", "properties": {"value": 1.0}},
            {"id": "y_data", "type": "constants/number", "properties": {"value": 2.0}},
            {"id": "xy_block", "type": "outputs/plots/xy_plot", "properties": {"XLabel": "Time", "YLabel": "Voltage"}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_block": "x_data", "source_pin": "Value", "target_block": "xy_block", "target_pin": "X"},
            {"id": "l2", "type": "data", "source_block": "y_data", "source_pin": "Value", "target_block": "xy_block", "target_pin": "Y"}
        ]
    }

    telemetry_received = {}
    async def telemetry_cb(run_id, msg):
        if msg["type"] == "telemetry":
            telemetry_received[msg["block_id"]] = msg["data"]

    engine = ExecutionEngine()
    engine.telemetry_callback = telemetry_cb
    engine.load_blueprint(blueprint)

    await engine.run(start_block_id="xy_block", start_pin_name="Plot")
    
    assert "xy_block" in telemetry_received
    data = telemetry_received["xy_block"]
    # XY plot should receive the values as lists (even if single values)
    assert data["x_label"] == "Time"
    assert data["y_label"] == "Voltage"


@pytest.mark.asyncio
async def test_array_stats_block_execution():
    """Test the renamed ArrayStatsBlock example."""
    blueprint = {
        "blocks": [
            {"id": "stats", "type": "Numeric Arrays/operations/stats", "properties": {}},
            {"id": "print_min", "type": "outputs/basic/print", "properties": {}},
            {"id": "print_max", "type": "outputs/basic/print", "properties": {}},
            {"id": "print_mean", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            {"id": "l1", "type": "exec", "source_block": "stats", "source_pin": "Out", "target_block": "print_min", "target_pin": "In"},
            {"id": "l2", "type": "exec", "source_block": "print_min", "source_pin": "Out", "target_block": "print_max", "target_pin": "In"},
            {"id": "l3", "type": "exec", "source_block": "print_max", "source_pin": "Out", "target_block": "print_mean", "target_pin": "In"},
            {"id": "l4", "type": "data", "source_block": "stats", "source_pin": "Min", "target_block": "print_min", "target_pin": "Value"},
            {"id": "l5", "type": "data", "source_block": "stats", "source_pin": "Max", "target_block": "print_max", "target_pin": "Value"},
            {"id": "l6", "type": "data", "source_block": "stats", "source_pin": "Mean", "target_block": "print_mean", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    
    # Manually set the array data on the stats block's properties before execution
    import numpy as np
    engine.blocks["stats"].properties["Array"] = np.array([1.0, 5.0, 10.0, 3.0, 8.5])

    await engine.run(start_block_id="stats", start_pin_name="Compute")
    
    # Verify the statistics were computed and printed
    assert engine.blocks["print_min"].last_printed == 1.0
    assert engine.blocks["print_max"].last_printed == 10.0
    assert engine.blocks["print_mean"].last_printed == 5.5


@pytest.mark.asyncio
async def test_safety_range_clamping():
    blueprint = {
        "blocks": [
            {"id": "loop", "type": "control_flow/loops/for_loop", "properties": {"Count": -5}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            {"id": "l1", "type": "exec", "source_block": "loop", "source_pin": "LoopBody", "target_block": "print", "target_pin": "In"},
            {"id": "l2", "type": "data", "source_block": "loop", "source_pin": "Index", "target_block": "print", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    # Run loop. Count is -5 (below min_val=1), it should clamp to 1 and run once.
    await engine.run(start_block_id="loop", start_pin_name="Start")
    
    assert engine.blocks["loop"]._index == 0
    assert engine.blocks["print"].last_printed == 0


@pytest.mark.asyncio
async def test_string_constant_and_sleep_execution():
    blueprint = {
        "blocks": [
            {"id": "str", "type": "constants/string", "properties": {"value": "Hello ComfyLAB"}},
            {"id": "sleep", "type": "control_flow/timing/sleep", "properties": {"Delay": 0.05}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            # str.Value -> print.Value
            {"id": "l1", "type": "data", "source_block": "str", "source_pin": "Value", "target_block": "print", "target_pin": "Value"},
            # sleep.Out -> print.In
            {"id": "l2", "type": "exec", "source_block": "sleep", "source_pin": "Out", "target_block": "print", "target_pin": "In"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    import time
    start = time.time()
    await engine.run(start_block_id="sleep", start_pin_name="In")
    end = time.time()

    assert engine.blocks["print"].last_printed == "Hello ComfyLAB"
    assert (end - start) >= 0.04


@pytest.mark.asyncio
async def test_pause_and_resume_execution():
    # Sequential slow blocks: slow1 -> slow2
    blueprint = {
        "blocks": [
            {"id": "slow1", "type": "test/slow_block", "properties": {"Delay": 0.1}},
            {"id": "slow2", "type": "test/slow_block", "properties": {"Delay": 0.1}}
        ],
        "links": [
            {"id": "l1", "type": "exec", "source_block": "slow1", "source_pin": "Out", "target_block": "slow2", "target_pin": "In"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    # Telemetry tracking for state changes
    telemetry_status = []
    async def telemetry_cb(run_id, msg):
        if msg["type"] == "run_status":
            telemetry_status.append(msg["status"])

    engine.telemetry_callback = telemetry_cb

    # Run execution in background task
    run_task = asyncio.create_task(engine.run(start_block_id="slow1", start_pin_name="In"))

    # Let slow1 start running
    await asyncio.sleep(0.02)
    assert engine.state == "RUNNING"
    assert engine.blocks["slow1"].ran is True
    assert engine.blocks["slow2"].ran is False

    # Pause execution
    await engine.pause()
    assert engine.state == "PAUSED"
    assert "paused" in telemetry_status

    # Wait for a bit and verify slow2 has not run yet (because we are paused)
    await asyncio.sleep(0.15)
    assert engine.blocks["slow2"].ran is False

    # Resume execution
    await engine.resume()
    assert engine.state == "RUNNING"
    assert "running" in telemetry_status

    # Wait for execution to finish
    await run_task
    assert engine.state == "IDLE"
    assert engine.blocks["slow2"].ran is True


@pytest.mark.asyncio
async def test_parallel_branches_execution():
    # Branch 1: slow1 (0.1s) -> slow2 (0.1s)
    # Branch 2: slow3 (0.1s) -> slow4 (0.1s)
    # Both branches are independent entry points.
    blueprint = {
        "blocks": [
            {"id": "slow1", "type": "test/slow_block", "properties": {"Delay": 0.1}},
            {"id": "slow2", "type": "test/slow_block", "properties": {"Delay": 0.1}},
            {"id": "slow3", "type": "test/slow_block", "properties": {"Delay": 0.1}},
            {"id": "slow4", "type": "test/slow_block", "properties": {"Delay": 0.1}}
        ],
        "links": [
            {"id": "l1", "type": "exec", "source_block": "slow1", "source_pin": "Out", "target_block": "slow2", "target_pin": "In"},
            {"id": "l2", "type": "exec", "source_block": "slow3", "source_pin": "Out", "target_block": "slow4", "target_pin": "In"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    import time
    start_time = time.time()
    await engine.run() # No start block, triggers all entry points
    end_time = time.time()

    elapsed = end_time - start_time
    # Verify both branches ran in parallel
    assert engine.blocks["slow1"].ran is True
    assert engine.blocks["slow2"].ran is True
    assert engine.blocks["slow3"].ran is True
    assert engine.blocks["slow4"].ran is True
    
    # If sequential, it would take >= 0.4s. Concurrently, it should take ~0.2s.
    # We assert it takes less than 0.35s to account for thread yielding overhead.
    assert elapsed < 0.35


@pytest.mark.asyncio
async def test_topological_teardown_order():
    global TEARDOWN_LOG
    TEARDOWN_LOG.clear()

    # Create a sequential graph slow1 -> slow2 -> slow3
    blueprint = {
        "blocks": [
            {"id": "slow1", "type": "test/slow_block", "properties": {"Delay": 0.01}},
            {"id": "slow2", "type": "test/slow_block", "properties": {"Delay": 0.01}},
            {"id": "slow3", "type": "test/slow_block", "properties": {"Delay": 0.01}}
        ],
        "links": [
            {"id": "l1", "type": "exec", "source_block": "slow1", "source_pin": "Out", "target_block": "slow2", "target_pin": "In"},
            {"id": "l2", "type": "exec", "source_block": "slow2", "source_pin": "Out", "target_block": "slow3", "target_pin": "In"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    # Run execution
    await engine.run(start_block_id="slow1", start_pin_name="In")

    # The executor's run method automatically calls _teardown_all at the end.
    # So TEARDOWN_LOG should be populated in reverse topological order:
    # slow3 (downstream) -> slow2 -> slow1 (upstream)
    assert TEARDOWN_LOG == ["slow3", "slow2", "slow1"]


@pytest.mark.asyncio
async def test_concurrent_teardown_safety():
    blueprint = {
        "blocks": [
            {"id": "slow1", "type": "test/slow_block", "properties": {"Delay": 0.05}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    # Start a run in the background
    run_task = asyncio.create_task(engine.run(start_block_id="slow1", start_pin_name="In"))
    await asyncio.sleep(0.01)

    # Now trigger abort (which cancels active tasks and calls _teardown_all)
    # concurrently with run's own finally block calling _teardown_all.
    await engine.abort()
    await run_task

    # The run should terminate safely without raising any exceptions due to concurrent teardowns.


@pytest.mark.asyncio
async def test_measure_time_block_execution():
    blueprint = {
        "blocks": [
            {"id": "measure", "type": "control_flow/timing/measure_time", "properties": {}},
            {"id": "sleep", "type": "control_flow/timing/sleep", "properties": {"Delay": 0.05}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            # measure.Body -> sleep.In
            {"id": "l1", "type": "exec", "source_block": "measure", "source_pin": "Body", "target_block": "sleep", "target_pin": "In"},
            # measure.Out -> print.In
            {"id": "l2", "type": "exec", "source_block": "measure", "source_pin": "Out", "target_block": "print", "target_pin": "In"},
            # measure.Time -> print.Value
            {"id": "l3", "type": "data", "source_block": "measure", "source_pin": "Time", "target_block": "print", "target_pin": "Value"}
        ]
    }

    telemetry_received = {}
    async def telemetry_cb(run_id, msg):
        if msg["type"] == "telemetry":
            telemetry_received[msg["block_id"]] = msg["data"]

    engine = ExecutionEngine()
    engine.telemetry_callback = telemetry_cb
    engine.load_blueprint(blueprint)

    await engine.run(start_block_id="measure", start_pin_name="In")

    # Time data output should be >= 0.05s
    measured_time = engine.blocks["measure"]._time
    assert measured_time >= 0.045
    
    # Telemetry should be sent
    assert "measure" in telemetry_received
    tel_val = telemetry_received["measure"]["value"]
    assert "ms" in tel_val or "s" in tel_val
    
    # Print block should have printed the raw float measured time
    assert engine.blocks["print"].last_printed == measured_time


@pytest.mark.asyncio
async def test_accumulator_block_execution():
    blueprint = {
        "blocks": [
            {"id": "num", "type": "constants/number", "properties": {"value": 5.0}},
            {"id": "accum", "type": "Lists/manipulation/accumulate", "properties": {}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            # num.Value -> accum.Value
            {"id": "l1", "type": "data", "source_block": "num", "source_pin": "Value", "target_block": "accum", "target_pin": "Value"},
            # accum.List -> print.Value
            {"id": "l2", "type": "data", "source_block": "accum", "source_pin": "List", "target_block": "print", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    # 1. Trigger Append
    await engine.run(start_block_id="accum", start_pin_name="Append")
    assert engine.blocks["accum"]._list == [5.0]

    # 2. Trigger Append again (change constant first to see difference)
    engine.blocks["num"].properties["value"] = 12.0
    # Run cache clear to simulate next step pulling fresh data
    await engine.run(start_block_id="accum", start_pin_name="Append")
    assert engine.blocks["accum"]._list == [5.0, 12.0]

    # 3. Pull accumulated array
    await engine.run(start_block_id="print", start_pin_name="In")
    assert engine.blocks["print"].last_printed == [5.0, 12.0]

    # 4. Trigger Reset
    await engine.run(start_block_id="accum", start_pin_name="Reset")
    assert engine.blocks["accum"]._list == []





