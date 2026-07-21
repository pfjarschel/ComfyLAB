# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import pytest
import math
import os
import csv
import asyncio
from comfylab.engine.executor import ExecutionEngine
from comfylab.blocks.base import ExecutionContext


@pytest.mark.asyncio
async def test_timer_block():
    engine = ExecutionEngine()
    
    # Store ticks
    tick_count = 0
    
    # Custom telemetry callback to track tick executions
    async def mock_telemetry(run_id, message):
        nonlocal tick_count
        if message.get("type") == "status" and message.get("status") == "success":
            if message.get("block_id") == "tick_counter":
                tick_count += 1

    engine.telemetry_callback = mock_telemetry

    blueprint = {
        "blocks": [
            {"id": "timer", "type": "control_flow/timing/timer", "properties": {"Interval": 20.0, "Count": 3}},
            {"id": "tick_counter", "type": "utility/exec_passthrough", "properties": {}}
        ],
        "links": [
            {"id": "l1", "type": "exec", "source_block": "timer", "source_pin": "Tick", "target_block": "tick_counter", "target_pin": "In"}
        ]
    }
    
    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="timer", start_pin_name="Start")
    
    # Check that it ticked exactly 3 times
    assert tick_count == 3


@pytest.mark.asyncio
async def test_filter_block():
    blueprint = {
        "blocks": [
            {"id": "filter_ma", "type": "math/signal_processing/filter", "properties": {"FilterType": "Moving Average", "Window": 3}},
            {"id": "filter_lp", "type": "math/signal_processing/filter", "properties": {"FilterType": "Low-pass", "Cutoff": 0.2, "Order": 2}},
            {"id": "filter_bp", "type": "math/signal_processing/filter", "properties": {"FilterType": "Band-pass", "LowCutoff": 0.1, "HighCutoff": 0.4, "Order": 2}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)

    # Test signal: sine wave + high-frequency noise
    import numpy as np
    t = np.array([i * 0.05 for i in range(100)])
    signal_noise = np.array([math.sin(x) + 0.5 * math.sin(20 * x) for x in t])

    # 1. Moving average
    engine.blocks["filter_ma"].properties["Signal"] = signal_noise
    await engine.blocks["filter_ma"].execute(context, "Filter")
    res_ma = await engine.blocks["filter_ma"].pull_data(context, "Filtered")
    assert isinstance(res_ma, np.ndarray)
    assert len(res_ma) == len(signal_noise)
    assert res_ma[0] != signal_noise[0]  # Smoothed

    # 2. Low pass
    engine.blocks["filter_lp"].properties["Signal"] = signal_noise
    await engine.blocks["filter_lp"].execute(context, "Filter")
    res_lp = await engine.blocks["filter_lp"].pull_data(context, "Filtered")
    assert isinstance(res_lp, np.ndarray)
    assert len(res_lp) == len(signal_noise)

    # 3. Band pass
    engine.blocks["filter_bp"].properties["Signal"] = signal_noise
    await engine.blocks["filter_bp"].execute(context, "Filter")
    res_bp = await engine.blocks["filter_bp"].pull_data(context, "Filtered")
    assert isinstance(res_bp, np.ndarray)
    assert len(res_bp) == len(signal_noise)


@pytest.mark.asyncio
async def test_heatmap_plot_block():
    telemetry_payload = None
    async def mock_telemetry(run_id, message):
        nonlocal telemetry_payload
        if message.get("type") == "telemetry" and message.get("block_id") == "heatmap":
            telemetry_payload = message.get("data")

    engine = ExecutionEngine()
    engine.telemetry_callback = mock_telemetry

    blueprint = {
        "blocks": [
            {"id": "heatmap", "type": "outputs/plots/heatmap_plot", "properties": {
                "Z": [[1, 2], [3, 4]], "X": [10, 20], "Y": [100, 200], "PlotType": "contour", "Colormap": "Wave"
            }}
        ],
        "links": []
    }
    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="heatmap", start_pin_name="Plot")

    assert telemetry_payload is not None
    assert telemetry_payload["z"] == [[1, 2], [3, 4]]
    assert telemetry_payload["x"] == [10, 20]
    assert telemetry_payload["y"] == [100, 200]
    assert telemetry_payload["plot_type"] == "contour"
    assert telemetry_payload["colormap"] == "Wave"


@pytest.mark.asyncio
async def test_calculator_block():
    blueprint = {
        "blocks": [
            {"id": "calc1", "type": "math/basic/calculator", "properties": {"Expression": "a + b * sin(c)", "variables": ["a", "b", "c"]}},
            {"id": "calc2", "type": "math/basic/calculator", "properties": {"Expression": "x ^ y", "variables": ["x", "y"]}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)

    # calc1: 5.0 + 2.0 * sin(pi/2) -> 5.0 + 2.0 * 1.0 = 7.0
    calc1 = engine.blocks["calc1"]
    calc1.properties["a"] = 5.0
    calc1.properties["b"] = 2.0
    calc1.properties["c"] = math.pi / 2
    res1 = await calc1.pull_data(context, "Result")
    assert abs(res1 - 7.0) < 1e-5

    # calc2: 2^3 -> 8.0 (converts ^ to **)
    calc2 = engine.blocks["calc2"]
    calc2.properties["x"] = 2.0
    calc2.properties["y"] = 3.0
    res2 = await calc2.pull_data(context, "Result")
    assert abs(res2 - 8.0) < 1e-5


@pytest.mark.asyncio
async def test_linear_scale_block():
    blueprint = {
        "blocks": [
            {"id": "scale_scalar", "type": "math/operations/linear_scale", "properties": {"A": 2.0, "B": 1.5, "X": 10.0}},
            {"id": "scale_array", "type": "math/operations/linear_scale", "properties": {"A": 0.5, "B": -1.0, "X": [10.0, 20.0, 30.0]}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)

    # Scalar: 2.0 * 10.0 + 1.5 = 21.5
    res_s = await engine.blocks["scale_scalar"].pull_data(context, "Result")
    assert res_s == 21.5

    # Array: 0.5 * x - 1.0
    res_a = await engine.blocks["scale_array"].pull_data(context, "Result")
    assert res_a == [4.0, 9.0, 14.0]


@pytest.mark.asyncio
async def test_ramp_generator_block():
    blueprint = {
        "blocks": [
            {"id": "ramp", "type": "Numeric Arrays/manipulation/linspace", "properties": {"Start": 1.0, "Stop": 5.0, "Steps": 5}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)

    arr = await engine.blocks["ramp"].pull_data(context, "Array")
    import numpy as np
    assert isinstance(arr, np.ndarray)
    assert list(arr) == [1.0, 2.0, 3.0, 4.0, 5.0]


@pytest.mark.asyncio
async def test_has_changed_block():
    blueprint = {
        "blocks": [
            {"id": "has_changed", "type": "logic/has_changed", "properties": {"Value": 10.0}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)

    block = engine.blocks["has_changed"]

    # 1) First execution (should flag as changed/true)
    await block.execute(context, "In")
    changed1 = await block.pull_data(context, "Changed")
    assert changed1 is True

    # 2) Second execution with same value (should flag as false)
    await block.execute(context, "In")
    changed2 = await block.pull_data(context, "Changed")
    assert changed2 is False

    # 3) Third execution with different value (should flag as true)
    block.properties["Value"] = 15.0
    await block.execute(context, "In")
    changed3 = await block.pull_data(context, "Changed")
    assert changed3 is True


@pytest.mark.asyncio
async def test_led_block():
    telemetry_state = None
    async def mock_telemetry(run_id, message):
        nonlocal telemetry_state
        if message.get("type") == "telemetry" and message.get("block_id") == "led":
            telemetry_state = message.get("data", {}).get("state")

    engine = ExecutionEngine()
    engine.telemetry_callback = mock_telemetry

    blueprint = {
        "blocks": [
            {"id": "led", "type": "outputs/basic/led_indicator", "properties": {"State": True}}
        ],
        "links": []
    }
    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="led", start_pin_name="In")

    assert telemetry_state is True


@pytest.mark.asyncio
async def test_file_path_generator_and_logger():
    # Test path generation
    blueprint_gen = {
        "blocks": [
            {"id": "gen", "type": "File I\\/O/path_generator", "properties": {
                "Prefix": "test_log", "Extension": "csv", "Subfolder": "test_outputs"
            }}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint_gen)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)

    filepath = await engine.blocks["gen"].pull_data(context, "FilePath")
    assert filepath.startswith("test_outputs/test_log_")
    assert filepath.endswith(".csv")

    # Clean up directories afterwards
    os.makedirs("test_outputs", exist_ok=True)
    test_filepath = os.path.abspath("test_outputs/test_logger_file.csv")
    if os.path.exists(test_filepath):
        os.remove(test_filepath)

    # Test logger
    blueprint_log = {
        "blocks": [
            {"id": "logger", "type": "File I\\/O/save_csv", "properties": {
                "FilePath": test_filepath,
                "Data": {"time": [0, 1], "voltage": [2.5, 3.1]},
                "mode": "overwrite"
            }}
        ],
        "links": []
    }
    engine.load_blueprint(blueprint_log)
    await engine.run(start_block_id="logger", start_pin_name="Write")

    # Assert file exists and columns are correct
    assert os.path.exists(test_filepath)
    with open(test_filepath, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
        assert len(reader) == 3 # header + 2 rows
        assert reader[0] == ["time", "voltage"]
        assert reader[1] == ["0", "2.5"]
        assert reader[2] == ["1", "3.1"]

    # Clean up
    if os.path.exists(test_filepath):
        os.remove(test_filepath)
    try:
        os.rmdir("test_outputs")
    except Exception:
        pass
