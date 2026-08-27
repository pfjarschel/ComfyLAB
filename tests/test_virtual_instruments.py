# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import time
import socket
import pytest
import numpy as np
import pyvisa

from comfylab.virtual.signal_generator import VirtualSignalGenerator
from comfylab.virtual.rc_circuit import VirtualRCCircuit
from comfylab.virtual.oscilloscope import VirtualOscilloscope
from comfylab.virtual.manager import VirtualInstrumentManager
from comfylab.devices.generic.oscilloscope import GenericOscilloscope
from comfylab.devices.generic.siggen import GenericSigGen
from comfylab.engine.executor import ExecutionEngine


def test_scpi_ieee_commands():
    """Verify IEEE 488.2 standard commands across instruments."""
    gen = VirtualSignalGenerator(port=59991)
    gen.start()
    try:
        with socket.create_connection(("127.0.0.1", 59991), timeout=1.0) as s:
            s.sendall(b"*IDN?\n")
            res = s.recv(1024).decode().strip()
            assert res.startswith("ComfyLAB,Virtual Signal Generator")
            assert "VSG1" in res

            s.sendall(b"*OPC?\n")
            res = s.recv(1024).decode().strip()
            assert res == "1"

            s.sendall(b"*ESR?\n")
            res = s.recv(1024).decode().strip()
            assert res == "0"
    finally:
        gen.close()


def test_signal_generator_scpi_commands_and_calculation():
    """Verify SCPI parameter configuration and on-demand waveform synthesis."""
    gen = VirtualSignalGenerator(port=59992)
    gen.start()
    try:
        with socket.create_connection(("127.0.0.1", 59992), timeout=1.0) as s:
            # Configure waveform
            s.sendall(b":SOURce1:FUNCtion SQUARE\n")
            s.sendall(b":SOURce1:FREQuency 2500\n")
            s.sendall(b":SOURce1:VOLTage 4.0\n")
            s.sendall(b":SOURce1:VOLTage:OFFSet 0.5\n")
            s.sendall(b":OUTPut1:STATe ON\n")

            # Query back
            s.sendall(b":SOURce1:FUNCtion?\n")
            assert s.recv(1024).decode().strip() == "SQUARE"

            s.sendall(b":SOURce1:FREQuency?\n")
            freq_val = float(s.recv(1024).decode().strip())
            assert abs(freq_val - 2500.0) < 1e-3

            s.sendall(b":SOURce1:VOLTage?\n")
            amp_val = float(s.recv(1024).decode().strip())
            assert abs(amp_val - 4.0) < 1e-3

            s.sendall(b":SOURce1:VOLTage:OFFSet?\n")
            offs_val = float(s.recv(1024).decode().strip())
            assert abs(offs_val - 0.5) < 1e-3

            s.sendall(b":OUTPut1:STATe?\n")
            assert s.recv(1024).decode().strip() == "1"

        # Check calculated waveform
        t = np.linspace(0, 0.001, 1000)
        wf = gen.calculate_signal(t)
        assert len(wf) == 1000
        # Square wave of 4 Vpp (+-2V) with +0.5V offset gives min -1.5V and max +2.5V
        assert abs(wf.min() - (-1.5)) < 1e-2
        assert abs(wf.max() - 2.5) < 1e-2
    finally:
        gen.close()


def test_rc_circuit_filtering():
    """Verify on-demand RC circuit low-pass filtering and cutoff attenuation."""
    sg = VirtualSignalGenerator()
    sg.amplitude = 2.0  # 1.0 V peak
    sg.frequency = 1000.0  # Below cutoff (~1591.5 Hz)
    sg.wave_type = "SINUSOID"

    rc = VirtualRCCircuit(port=59993)
    rc.set_input_source(sg)
    rc.resistance = 1000.0  # 1 kOhm
    rc.capacitance = 0.1    # 0.1 uF -> tau = 10^-4 s, fc approx 1591 Hz
    rc.start()
    try:
        with socket.create_connection(("127.0.0.1", 59993), timeout=1.0) as s:
            s.sendall(b"*IDN?\n")
            assert "ComfyLAB,Virtual RC Circuit" in s.recv(1024).decode().strip()

            s.sendall(b":RESistance 2000\n")
            s.sendall(b":RESistance?\n")
            assert abs(float(s.recv(1024).decode().strip()) - 2000.0) < 1e-3

            s.sendall(b":CAPacitance 0.2\n")
            s.sendall(b":CAPacitance?\n")
            assert abs(float(s.recv(1024).decode().strip()) - 0.2) < 1e-3

        # Reset to 1k / 0.1uF
        rc.resistance = 1000.0
        rc.capacitance = 0.1
        t = np.linspace(0, 0.01, 2000)
        v_in = sg.calculate_signal(t)
        v_out = rc.calculate_signal(v_in, t)

        # Amplitude response of 1st order RC low-pass: |H(f)| = 1 / sqrt(1 + (f / fc)^2)
        # For f = 1000 Hz, fc = 1591.55 Hz: |H| approx 0.8467
        peak_in = np.max(v_in)
        peak_out = np.max(v_out)
        ratio = peak_out / peak_in
        assert 0.80 < ratio < 0.90, f"Expected ratio around 0.847, got {ratio}"
    finally:
        rc.close()


def test_oscilloscope_binary_and_ascii_acquisition():
    """Verify oscilloscope data acquisition in both ASCII and IEEE 488.2 BYTE binary mode."""
    sg = VirtualSignalGenerator()
    sg.amplitude = 2.0
    sg.frequency = 1000.0

    rc = VirtualRCCircuit()
    rc.set_input_source(sg)

    osc = VirtualOscilloscope(port=59994, ch1_source=sg, ch2_source=rc)
    osc.start()
    try:
        with socket.create_connection(("127.0.0.1", 59994), timeout=1.0) as s:
            s.sendall(b"*IDN?\n")
            assert "ComfyLAB,Virtual Oscilloscope" in s.recv(1024).decode().strip()

            # Test ASCII Channel queries
            s.sendall(b":TIMebase:DATA?\n")
            time_data = s.recv(65536).decode().strip()
            time_pts = [float(x) for x in time_data.split(",") if x]
            assert len(time_pts) == 1000

            s.sendall(b":CHANnel1:DATA?\n")
            ch1_data = s.recv(65536).decode().strip()
            ch1_pts = [float(x) for x in ch1_data.split(",") if x]
            assert len(ch1_pts) == 1000

            # Test IEEE 488.2 BYTE mode
            s.sendall(b":WAVeform:SOURce CHANnel1\n")
            s.sendall(b":WAVeform:FORMat BYTE\n")
            s.sendall(b":WAVeform:DATA?\n")
            raw_response = s.recv(65536)
            assert raw_response.startswith(b"#")
            # Parse header
            num_digits = int(chr(raw_response[1]))
            length = int(raw_response[2:2 + num_digits].decode("ascii"))
            assert length == 1000
    finally:
        osc.close()


def test_manager_singleton_and_cleanup():
    """Verify VirtualInstrumentManager manages singleton server without duplicate processes."""
    # Ensure started
    assert VirtualInstrumentManager.ensure_started()
    assert VirtualInstrumentManager.is_running()
    first_pid = VirtualInstrumentManager._process.pid if VirtualInstrumentManager._process else None

    # Re-call ensure_started - must NOT spawn a new process
    assert VirtualInstrumentManager.ensure_started()
    if first_pid is not None and VirtualInstrumentManager._process is not None:
        assert VirtualInstrumentManager._process.pid == first_pid

    # Client reference counting
    VirtualInstrumentManager.register_client("client_A")
    VirtualInstrumentManager.register_client("client_B")
    VirtualInstrumentManager.unregister_client("client_A", auto_stop=True)
    assert VirtualInstrumentManager.is_running()

    # Unregister final client -> auto_stop triggers
    VirtualInstrumentManager.unregister_client("client_B", auto_stop=True)
    assert len(VirtualInstrumentManager._clients) == 0
    assert VirtualInstrumentManager._process is None


def test_generic_drivers_integration():
    """Verify GenericOscilloscope and GenericSigGen communicate with live virtual instruments."""
    try:
        assert VirtualInstrumentManager.ensure_started()
        rm = pyvisa.ResourceManager()

        # Connect to Signal Generator
        sg_dev = rm.open_resource("TCPIP0::127.0.0.1::51235::SOCKET", read_termination="\n", write_termination="\n")
        gen_driver = GenericSigGen(sg_dev)
        gen_driver.set_channel_wave(channel=1, shape="SINUSOID", frequency=1200.0, amplitude=3.0, offset=0.0)
        gen_driver.set_output(channel=1, enable=True)

        # Connect to Oscilloscope
        osc_dev = rm.open_resource("TCPIP0::127.0.0.1::51234::SOCKET", read_termination="\n", write_termination="\n")
        osc_driver = GenericOscilloscope(osc_dev)
        osc_driver.set_timebase(scale=0.001, position=0.0)
        osc_driver.set_channel(channel=1, enable=True, scale=1.0)
        osc_driver.set_channel(channel=2, enable=True, scale=1.0)

        # Acquire Channel 1 (SigGen)
        t1, v1 = osc_driver.acquire_waveform(channel=1)
        assert len(v1) == 1000
        assert len(t1) == 1000

        # Acquire Channel 2 (RC circuit)
        t2, v2 = osc_driver.acquire_waveform(channel=2)
        assert len(v2) == 1000
        assert len(t2) == 1000

        sg_dev.close()
        osc_dev.close()
    finally:
        VirtualInstrumentManager.stop()


@pytest.mark.asyncio
async def test_virtual_blocks_full_workflow():
    """Test executing a ComfyLAB blueprint with VirtSigGen and VirtOsc connect, config, and acquire blocks."""
    from comfylab.blocks.visa import visa_rm_wrapper
    visa_rm_wrapper._rm = None
    try:
        blueprint = {
            "blocks": [
                {"id": "siggen_conn", "type": "devices/virtual/signal_generator/connect", "properties": {
                    "Address": "VIRT::SIGGEN"
                }},
                {"id": "config_wave", "type": "devices/virtual/signal_generator/config_wave", "properties": {
                    "WaveType": "sine",
                    "Frequency": 1000.0,
                    "Amplitude": 2.0
                }},
                {"id": "set_output", "type": "devices/virtual/signal_generator/output", "properties": {
                    "Output": True
                }},
                {"id": "osc_conn", "type": "devices/virtual/oscilloscope/connect", "properties": {
                    "Address": "VIRT::OSC"
                }},
                {"id": "osc_state", "type": "devices/virtual/oscilloscope/state", "properties": {
                    "State": "run"
                }},
                {"id": "osc_acquire", "type": "devices/virtual/oscilloscope/acquire", "properties": {
                    "Channel": 1
                }}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_block": "siggen_conn", "source_pin": "Out", "target_block": "config_wave", "target_pin": "In"},
                {"id": "l2", "type": "exec", "source_block": "config_wave", "source_pin": "Out", "target_block": "set_output", "target_pin": "In"},
                {"id": "l3", "type": "exec", "source_block": "set_output", "source_pin": "Out", "target_block": "osc_conn", "target_pin": "In"},
                {"id": "l4", "type": "exec", "source_block": "osc_conn", "source_pin": "Out", "target_block": "osc_state", "target_pin": "In"},
                {"id": "l5", "type": "exec", "source_block": "osc_state", "source_pin": "Out", "target_block": "osc_acquire", "target_pin": "In"},
                {"id": "l6", "type": "data", "source_block": "siggen_conn", "source_pin": "Device", "target_block": "config_wave", "target_pin": "Device"},
                {"id": "l7", "type": "data", "source_block": "siggen_conn", "source_pin": "Device", "target_block": "set_output", "target_pin": "Device"},
                {"id": "l8", "type": "data", "source_block": "osc_conn", "source_pin": "Device", "target_block": "osc_state", "target_pin": "Device"},
                {"id": "l9", "type": "data", "source_block": "osc_conn", "source_pin": "Device", "target_block": "osc_acquire", "target_pin": "Device"}
            ]
        }

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)

        await engine.run(start_block_id="siggen_conn", start_pin_name="Open")

        acq_block = engine.blocks["osc_acquire"]
        assert len(acq_block._last_waveform) == 1000
        assert len(acq_block._last_time) == 1000
        assert abs(acq_block._last_waveform.max() - 1.0) < 0.1

        await engine._teardown_all()
    finally:
        VirtualInstrumentManager.stop()


def test_signal_generator_noise_and_jitter():
    """Verify amplitude noise and phase jitter simulation and SCPI control."""
    gen = VirtualSignalGenerator(port=59995)
    gen.start()
    try:
        with socket.create_connection(("127.0.0.1", 59995), timeout=1.0) as s:
            s.sendall(b":SOURce1:NOISe:STATe ON\n")
            s.sendall(b":SOURce1:NOISe:LEVel 0.1\n")
            s.sendall(b":SOURce1:JITTer 1e-6\n")

            s.sendall(b":SOURce1:NOISe:STATe?\n")
            assert s.recv(1024).decode().strip() == "1"

            s.sendall(b":SOURce1:NOISe:LEVel?\n")
            noise_val = float(s.recv(1024).decode().strip())
            assert abs(noise_val - 0.1) < 1e-3

            s.sendall(b":SOURce1:JITTer?\n")
            jitter_val = float(s.recv(1024).decode().strip())
            assert abs(jitter_val - 1e-6) < 1e-9

        t = np.linspace(0, 0.001, 1000)
        # Without noise:
        gen.noise_enabled = False
        gen.jitter = 0.0
        clean_wf = gen.calculate_signal(t)

        # With noise:
        gen.noise_enabled = True
        gen.noise_level = 0.2  # 200 mV noise
        noisy_wf = gen.calculate_signal(t)

        # Ensure noise was added (difference is non-zero and within expected envelope)
        diff = np.abs(noisy_wf - clean_wf)
        assert np.max(diff) > 0.01
        assert np.max(diff) <= 0.15
    finally:
        gen.close()


@pytest.mark.asyncio
async def test_bode_diagram_virtual_blueprint():
    """Verify Bode_Diagram_Virtual example blueprint and virtual clusters execute end-to-end."""
    import json
    from pathlib import Path
    from comfylab.blocks.loader import load_all_blocks, load_all_clusters
    from comfylab.blocks.visa import visa_rm_wrapper

    visa_rm_wrapper._rm = None
    load_all_blocks()
    load_all_clusters()

    example_path = Path(__file__).resolve().parent.parent / "comfylab" / "examples" / "Bode_Diagram_Virtual.json"
    assert example_path.exists(), f"Example file {example_path} does not exist"

    with open(example_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Use 3 frequency steps for quick verification: 100 Hz, 3162 Hz, 100 kHz
    for b in data["blocks"]:
        if b["id"] == "block_freq_logspace":
            b["data"]["Steps"] = 3

    blueprint_blocks = []
    for b in data["blocks"]:
        props = dict(b["data"])
        btype = props.pop("action", "")
        blueprint_blocks.append({
            "id": b["id"],
            "type": btype,
            "properties": props
        })

    blueprint_links = []
    for e in data["edges"]:
        is_exec = (
            e.get("style", {}).get("animated", False)
            or "Out" in e.get("sourceHandle", "")
            or "Done" in e.get("sourceHandle", "")
            or "LoopBody" in e.get("sourceHandle", "")
            or "Plot" in e.get("targetHandle", "")
            or "Write" in e.get("targetHandle", "")
        )
        blueprint_links.append({
            "id": e["id"],
            "type": "exec" if is_exec else "data",
            "source_block": e["source"],
            "source_pin": e["sourceHandle"],
            "target_block": e["target"],
            "target_pin": e["targetHandle"]
        })

    engine_blueprint = {
        "blocks": blueprint_blocks,
        "links": blueprint_links
    }

    engine = ExecutionEngine()
    engine.load_blueprint(engine_blueprint)

    try:
        await engine.run(start_block_id="cluster_setup", start_pin_name="In")
        accum_gain = engine.blocks["block_accum_gain"]
        assert len(accum_gain._list) == 3
        # 100 Hz: flat passband (gain > -1.5 dB)
        assert accum_gain._list[0] > -1.5
        # 100 kHz: heavily attenuated (gain < -25 dB)
        assert accum_gain._list[-1] < -25.0
    finally:
        await engine._teardown_all()
        VirtualInstrumentManager.stop()
