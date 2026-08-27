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
import numpy as np
from comfylab.engine.executor import ExecutionEngine
from comfylab.engine.registry import BLOCK_REGISTRY


def test_plot_blocks_registered():
    """Verify all 7 new plot blocks are properly registered in the BLOCK_REGISTRY."""
    expected_blocks = [
        "outputs/plots/histogram_plot",
        "outputs/plots/dual_y_plot",
        "outputs/plots/polar_plot",
        "outputs/plots/bar_plot",
        "outputs/plots/box_plot",
        "outputs/plots/plot_3d",
        "outputs/plots/waterfall_plot",
    ]
    for block_type in expected_blocks:
        assert block_type in BLOCK_REGISTRY, f"Missing registered block: {block_type}"


@pytest.mark.asyncio
async def test_histogram_plot_execution():
    engine = ExecutionEngine()
    telemetry_received = []

    async def mock_telemetry(run_id, message):
        if message.get("type") == "telemetry" and message.get("block_id") == "hist1":
            telemetry_received.append(message.get("data"))

    engine.telemetry_callback = mock_telemetry

    blueprint = {
        "blocks": [
            {
                "id": "hist1",
                "type": "outputs/plots/histogram_plot",
                "properties": {
                    "Data": [1.0, 2.0, 2.5, 3.0, 3.5, 3.5, 4.0, 5.0],
                    "Bins": 10,
                    "BinSize": 0.5,
                    "Normalization": "Probability",
                    "Cumulative": True,
                    "XLabel": "Sample Value",
                    "YLabel": "Probability",
                    "ShowStats": True
                }
            }
        ],
        "links": []
    }

    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="hist1", start_pin_name="Plot")

    assert len(telemetry_received) == 1
    data = telemetry_received[0]
    assert data["bins"] == 10
    assert data["bin_size"] == 0.5
    assert data["normalization"] == "Probability"
    assert data["cumulative"] is True
    assert data["x_label"] == "Sample Value"
    assert data["y_label"] == "Probability"
    assert data["show_stats"] is True
    assert len(data["data"]) == 8


@pytest.mark.asyncio
async def test_dual_y_plot_execution():
    engine = ExecutionEngine()
    telemetry_received = []

    async def mock_telemetry(run_id, message):
        if message.get("type") == "telemetry" and message.get("block_id") == "dualy1":
            telemetry_received.append(message.get("data"))

    engine.telemetry_callback = mock_telemetry

    blueprint = {
        "blocks": [
            {
                "id": "dualy1",
                "type": "outputs/plots/dual_y_plot",
                "properties": {
                    "X": [1, 2, 3, 4],
                    "Y1": [10.0, 20.0, 30.0, 40.0],
                    "Y2": [100.0, 50.0, 25.0, 12.5],
                    "XLabel": "Time (s)",
                    "Y1Label": "Voltage (V)",
                    "Y2Label": "Current (mA)",
                    "Y1TraceName": "V_out",
                    "Y2TraceName": "I_load",
                    "Y1Log": False,
                    "Y2Log": True
                }
            }
        ],
        "links": []
    }

    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="dualy1", start_pin_name="Plot")

    assert len(telemetry_received) == 1
    data = telemetry_received[0]
    assert data["x"] == [1, 2, 3, 4]
    assert data["y1"] == [10.0, 20.0, 30.0, 40.0]
    assert data["y2"] == [100.0, 50.0, 25.0, 12.5]
    assert data["y1_label"] == "Voltage (V)"
    assert data["y2_label"] == "Current (mA)"
    assert data["y1_name"] == "V_out"
    assert data["y2_name"] == "I_load"
    assert data["y2_log"] is True


@pytest.mark.asyncio
async def test_polar_plot_execution():
    engine = ExecutionEngine()
    telemetry_received = []

    async def mock_telemetry(run_id, message):
        if message.get("type") == "telemetry" and message.get("block_id") == "polar1":
            telemetry_received.append(message.get("data"))

    engine.telemetry_callback = mock_telemetry

    blueprint = {
        "blocks": [
            {
                "id": "polar1",
                "type": "outputs/plots/polar_plot",
                "properties": {
                    "R": [0, 1, 2, 3],
                    "Theta": [0, 90, 180, 270],
                    "AngleUnit": "Degrees",
                    "PlotMode": "Lines+Markers",
                    "Direction": "Clockwise"
                }
            }
        ],
        "links": []
    }

    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="polar1", start_pin_name="Plot")

    assert len(telemetry_received) == 1
    data = telemetry_received[0]
    assert data["r"] == [0, 1, 2, 3]
    assert data["theta"] == [0, 90, 180, 270]
    assert data["angle_unit"] == "degrees"
    assert data["plot_mode"] == "lines+markers"
    assert data["direction"] == "clockwise"


@pytest.mark.asyncio
async def test_bar_plot_execution():
    engine = ExecutionEngine()
    telemetry_received = []

    async def mock_telemetry(run_id, message):
        if message.get("type") == "telemetry" and message.get("block_id") == "bar1":
            telemetry_received.append(message.get("data"))

    engine.telemetry_callback = mock_telemetry

    blueprint = {
        "blocks": [
            {
                "id": "bar1",
                "type": "outputs/plots/bar_plot",
                "properties": {
                    "Values": [15, 28, 42],
                    "Categories": ["Channel 1", "Channel 2", "Channel 3"],
                    "Orientation": "Horizontal",
                    "BarMode": "Group"
                }
            }
        ],
        "links": []
    }

    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="bar1", start_pin_name="Plot")

    assert len(telemetry_received) == 1
    data = telemetry_received[0]
    assert data["values"] == [15, 28, 42]
    assert data["categories"] == ["Channel 1", "Channel 2", "Channel 3"]
    assert data["orientation"] == "h"
    assert data["barmode"] == "group"


@pytest.mark.asyncio
async def test_box_plot_execution():
    engine = ExecutionEngine()
    telemetry_received = []

    async def mock_telemetry(run_id, message):
        if message.get("type") == "telemetry" and message.get("block_id") == "box1":
            telemetry_received.append(message.get("data"))

    engine.telemetry_callback = mock_telemetry

    blueprint = {
        "blocks": [
            {
                "id": "box1",
                "type": "outputs/plots/box_plot",
                "properties": {
                    "Data": [[1, 2, 3, 4, 5], [2, 4, 6, 8, 10]],
                    "PlotType": "Violin",
                    "Points": "All",
                    "Labels": ["Batch A", "Batch B"]
                }
            }
        ],
        "links": []
    }

    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="box1", start_pin_name="Plot")

    assert len(telemetry_received) == 1
    data = telemetry_received[0]
    assert data["plot_type"] == "violin"
    assert data["points"] == "all"
    assert data["labels"] == ["Batch A", "Batch B"]


@pytest.mark.asyncio
async def test_plot_3d_execution():
    engine = ExecutionEngine()
    telemetry_received = []

    async def mock_telemetry(run_id, message):
        if message.get("type") == "telemetry" and message.get("block_id") == "p3d1":
            telemetry_received.append(message.get("data"))

    engine.telemetry_callback = mock_telemetry

    blueprint = {
        "blocks": [
            {
                "id": "p3d1",
                "type": "outputs/plots/plot_3d",
                "properties": {
                    "Z": [[1, 2], [3, 4]],
                    "PlotType": "Surface",
                    "Colormap": "Turbo",
                    "ZLabel": "Elevation (um)"
                }
            }
        ],
        "links": []
    }

    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="p3d1", start_pin_name="Plot")

    assert len(telemetry_received) == 1
    data = telemetry_received[0]
    assert data["z"] == [[1, 2], [3, 4]]
    assert data["plot_type"] == "surface"
    assert data["colormap"] == "Turbo"
    assert data["z_label"] == "Elevation (um)"


@pytest.mark.asyncio
async def test_waterfall_plot_execution():
    engine = ExecutionEngine()
    telemetry_received = []

    async def mock_telemetry(run_id, message):
        if message.get("type") == "telemetry" and message.get("block_id") == "wf1":
            telemetry_received.append(message.get("data"))

    engine.telemetry_callback = mock_telemetry

    blueprint = {
        "blocks": [
            {
                "id": "wf1",
                "type": "outputs/plots/waterfall_plot",
                "properties": {
                    "Spectrum": [10.5, 20.2, 5.1, 1.2],
                    "XCoords": [1550.0, 1550.5, 1551.0, 1551.5],
                    "MaxHistory": 100,
                    "Colormap": "Inferno"
                }
            }
        ],
        "links": []
    }

    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="wf1", start_pin_name="Plot")

    assert len(telemetry_received) == 1
    data = telemetry_received[0]
    assert data["spectrum"] == [10.5, 20.2, 5.1, 1.2]
    assert data["x_coords"] == [1550.0, 1550.5, 1551.0, 1551.5]
    assert data["max_history"] == 100
    assert data["colormap"] == "Inferno"
