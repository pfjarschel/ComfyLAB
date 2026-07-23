# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import pytest
from unittest.mock import MagicMock
import numpy as np

# Test pure Python driver imports
from comfylab.devices.tektronix.tbs1062 import TBS1062
from comfylab.devices.owon.dge2000 import DGE2000
from comfylab.devices.minipa.mfg4230 import MFG4230
from comfylab.devices.bk_precision.bk4052 import BK4052
from comfylab.devices.generic.esa import GenericESA
from comfylab.devices.generic.dmm import GenericDMM
from comfylab.devices.generic.power_supply import GenericPowerSupply
from comfylab.devices.generic.siggen import GenericSigGen
from comfylab.devices.generic.oscilloscope import GenericOscilloscope
from comfylab.devices.generic.camera import GenericCamera

# Phase 4 & Extended Device Driver Imports
from comfylab.devices.thorlabs.pm100d import ThorlabsPM100D
from comfylab.devices.keysight.agilent_816x import Agilent816x
from comfylab.devices.yokogawa.aq6370 import AQ6370
from comfylab.devices.keithley.k2400 import Keithley2400
from comfylab.devices.srs.sr830 import SR830

# Extended Commercial Instruments
from comfylab.devices.keysight.dsox_series import KeysightDSOX
from comfylab.devices.agilent.e4407b import AgilentE4407B
from comfylab.devices.agilent.hp34401a import HP34401A
from comfylab.devices.advantest.q8384 import AdvantestQ8384
from comfylab.devices.keopsys.edfa import KeopsysEDFA
from comfylab.devices.thorlabs.lts200 import ThorlabsLTS200
from comfylab.devices.thorlabs.mdt69x import ThorlabsMDT69X
from comfylab.devices.ni.nidaqmx_device import NIDAQmxDevice
from comfylab.devices.mcc.mcdaq1208ls import MCCDAQ1208LS

# Test block discovery & registration
from comfylab.blocks.loader import load_blocks_from_directory
from comfylab.engine.registry import get_registered_blocks


def test_tbs1062_driver_mock():
    mock_visa = MagicMock()
    mock_visa.query.side_effect = lambda cmd: {
        "WFMPRe:XINcr?": "1e-6",
        "WFMPRe:XZERo?": "0.0",
        "WFMPRe:YMUlt?": "0.01",
        "WFMPRe:YOFF?": "0.0",
        "WFMPRe:YZERo?": "0.0",
        "HORizontal:MAIn:SCALE?": "0.001",
    }.get(cmd, "0")

    mock_visa.query_raw.return_value = b"#10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

    drv = TBS1062(mock_visa)
    drv.set_timebase(scale=0.001, position=0.0)
    mock_visa.write.assert_any_call("HORizontal:MAIn:SCALE 0.001")

    drv.set_channel(channel=1, enable=True, scale=2.0)
    mock_visa.write.assert_any_call("CH1:SCALE 2.0")

    t, v = drv.acquire_waveform(channel=1)
    assert isinstance(t, np.ndarray)
    assert isinstance(v, np.ndarray)


def test_keysight_dsox_mock():
    mock_visa = MagicMock()
    mock_visa.query.side_effect = lambda cmd: {
        ":WAVeform:PREamble?": "1,0,1000,1,1e-6,0.0,0.0,0.01,0.0,0.0"
    }.get(cmd, "0")
    # 4 bytes = 2 uint16 numbers
    mock_visa.query_raw.return_value = b"#14\x00\x00\x01\x00"

    drv = KeysightDSOX(mock_visa)
    drv.set_timebase(scale=0.001)
    mock_visa.write.assert_any_call(":TIMebase:SCALe 0.001")

    t, v = drv.acquire_waveform(channel=1)
    assert len(v) == 2


def test_agilent_e4407b_mock():
    mock_visa = MagicMock()
    mock_visa.query.side_effect = lambda cmd: {
        ":SENSe:FREQuency:STARt?": "1000000000.0",
        ":SENSe:FREQuency:STOP?": "1100000000.0",
        ":TRACe:DATA? TRACE1": "-10.0, -15.0, -20.0"
    }.get(cmd, "0")

    drv = AgilentE4407B(mock_visa)
    drv.set_frequency(center_hz=1e9, span_hz=100e6)
    mock_visa.write.assert_any_call(":SENSe:FREQuency:CENTer 1000000000.0")

    f, p = drv.acquire_trace(1)
    assert len(f) == 3
    assert len(p) == 3


def test_hp34401a_mock():
    mock_visa = MagicMock()
    mock_visa.query.side_effect = lambda cmd: {
        "READ?": "3.14159",
        "FETC?": "1.23, 1.25"
    }.get(cmd, "0")

    drv = HP34401A(mock_visa)
    drv.configure("VOLT:DC")
    mock_visa.write.assert_any_call("CONF:VOLT:DC")

    v = drv.read_voltage_dc()
    assert v == 1.24


def test_advantest_q8384_mock():
    mock_visa = MagicMock()
    mock_visa.query.side_effect = lambda cmd: {
        "CNT?": "CNT 1550.0",
        "SPAN?": "SPAN 20.0",
        "LDAT": "-20.0, -10.0, -25.0"
    }.get(cmd, "0")

    drv = AdvantestQ8384(mock_visa)
    drv.set_sweep_config(center_nm=1550.0, span_nm=20.0)
    mock_visa.write.assert_any_call("CNT 1550.0")

    wl, p = drv.acquire_trace()
    assert len(wl) == 3
    assert p[1] == -10.0


def test_keopsys_edfa_mock():
    mock_visa = MagicMock()
    mock_visa.query.side_effect = lambda cmd: {
        "TD2?": "TD2=2500"
    }.get(cmd, "0")

    drv = KeopsysEDFA(mock_visa)
    drv.set_pump_state(True)
    mock_visa.write.assert_any_call("K1")

    drv.set_control_mode("ACC")
    mock_visa.write.assert_any_call("ASS=1")

    t = drv.read_temperature()
    assert t == 25.0


def test_thorlabs_lts200_and_mdt69x_mock():
    mock_visa = MagicMock()
    mock_visa.query.side_effect = lambda cmd: {
        "pos": "pos 12.345",
        "xvoltage?": "xvoltage=[50.0]"
    }.get(cmd, "0")

    lts = ThorlabsLTS200(mock_visa)
    lts.move_absolute(12.345)
    mock_visa.write.assert_called_with("ma 12.345")

    p = lts.get_position()
    assert p == 12.345

    mdt = ThorlabsMDT69X(mock_visa)
    mdt.set_voltage("X", 50.0)
    mock_visa.write.assert_called_with("xvoltage=50.0")

    v = mdt.get_voltage("X")
    assert v == 50.0


def test_mcdaq1208ls_mock():
    mock_visa = MagicMock()
    mock_visa.query.side_effect = lambda cmd: {
        "AIN 0": "AIN 2.50"
    }.get(cmd, "0")

    mcc = MCCDAQ1208LS(mock_visa)
    val = mcc.read_analog_channel(0)
    assert val == 2.5


def test_nidaqmx_error_raising_when_uninstalled(monkeypatch):
    import comfylab.devices.ni.nidaqmx_device as ni_mod
    monkeypatch.setattr(ni_mod, "NIDAQMX_AVAILABLE", False)

    with pytest.raises(RuntimeError, match="not installed on this system"):
        ni_mod.NIDAQmxDevice("Dev1")


def test_block_registration_discovery():
    import comfylab.blocks.loader as loader
    import comfylab.blocks.devices as devices_pkg
    from pathlib import Path

    devices_dir = str(Path(devices_pkg.__file__).parent)
    loader.load_blocks_from_directory(devices_dir)

    registered = get_registered_blocks()
    
    # Check block discovery for newly added devices
    assert "devices/keysight/dsox_series/connect" in registered
    assert "devices/agilent/e4407b/connect" in registered
    assert "devices/agilent/hp34401a/connect" in registered
    assert "devices/advantest/q8384/connect" in registered
    assert "devices/keopsys/edfa/connect" in registered
    assert "devices/thorlabs/lts200/connect" in registered
    assert "devices/thorlabs/mdt69x/connect" in registered
    assert "devices/ni/nidaqmx/connect" in registered
    assert "devices/mcc/mcdaq1208ls/connect" in registered
    assert "devices/generic/oscilloscope/connect" in registered
    assert "devices/generic/camera/connect" in registered
