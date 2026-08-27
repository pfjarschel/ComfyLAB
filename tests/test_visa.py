from unittest.mock import MagicMock, patch
import pytest
from comfylab.engine.executor import ExecutionEngine
from comfylab.engine.registry import get_all_blocks_schema

def test_visa_blocks_registration():
    schema = get_all_blocks_schema()
    
    assert "visa/core/resource_manager" in schema
    assert "visa/core/find_device" in schema
    assert "visa/core/device" in schema
    assert "visa/core/write" in schema
    assert "visa/core/read" in schema
    assert "visa/core/query" in schema

    rm_schema = schema["visa/core/resource_manager"]
    assert rm_schema["name"] == "VISA Resource Manager"
    assert rm_schema["category"] == "VISA/Core"
    assert len(rm_schema["dataOuts"]) == 1
    assert rm_schema["dataOuts"][0]["name"] == "Resources"
    assert rm_schema["isDevice"] is False

    fd_schema = schema["visa/core/find_device"]
    assert fd_schema["name"] == "VISA Find Device"
    assert fd_schema["isDevice"] is False

@pytest.mark.asyncio
async def test_visa_blocks_mock_execution():
    # Patch pyvisa inside comfylab.blocks.visa to run unit test without real NI-VISA or device connection
    with patch("comfylab.blocks.visa.pyvisa") as mock_pyvisa:
        mock_rm = MagicMock()
        mock_pyvisa.ResourceManager.return_value = mock_rm
        
        # Setup mock instrument device
        mock_device = MagicMock()
        mock_device.resource_name = "GPIB0::2::INSTR"
        mock_device.query.return_value = "Mock SCPI Instrument (GPIB0::2::INSTR)"
        
        mock_rm.list_resources.return_value = ["GPIB0::2::INSTR"]
        mock_rm.open_resource.return_value = mock_device

        # Reset wrapper to force re-evaluation in this test scope
        from comfylab.blocks.visa import visa_rm_wrapper
        visa_rm_wrapper._rm = None

        blueprint = {
            "blocks": [
                {"id": "device", "type": "visa/core/device", "properties": {
                    "Address": "GPIB0::2::INSTR",
                    "ReadTermination": "\\r",
                    "WriteTermination": "\\r",
                    "Timeout": 0.5
                }},
                {"id": "query", "type": "visa/core/query", "properties": {"Command": "*IDN?"}},
                {"id": "print", "type": "outputs/basic/print", "properties": {}}
            ],
            "links": [
                # Open Device -> Exec Query
                {"id": "l1", "type": "exec", "source_block": "device", "source_pin": "Out", "target_block": "query", "target_pin": "In"},
                # Query -> Exec Print
                {"id": "l2", "type": "exec", "source_block": "query", "source_pin": "Out", "target_block": "print", "target_pin": "In"},
                # Connect Device output pin -> Query Device input pin
                {"id": "l3", "type": "data", "source_block": "device", "source_pin": "Device", "target_block": "query", "target_pin": "Device"},
                # Connect Query Response output pin -> Print Value input pin
                {"id": "l4", "type": "data", "source_block": "query", "source_pin": "Response", "target_block": "print", "target_pin": "Value"}
            ]
        }

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)

        # Execute from device block
        await engine.run(start_block_id="device", start_pin_name="Open")

        # Assert that device was opened and query returned mock response
        device_block = engine.blocks["device"]
        # Device is closed after teardown (which runs automatically on completion)
        assert device_block._device is None
        mock_device.close.assert_called()

        # Assert custom values were unescaped and applied to mock device
        assert mock_device.read_termination == "\r"
        assert mock_device.write_termination == "\r"
        assert mock_device.timeout == 500

        print_block = engine.blocks["print"]
        assert print_block.last_printed == "Mock SCPI Instrument (GPIB0::2::INSTR)"


@pytest.mark.asyncio
async def test_virt_siggen_blocks_execution():
    with patch("comfylab.blocks.visa.pyvisa") as mock_pyvisa:
        mock_rm = MagicMock()
        mock_pyvisa.ResourceManager.return_value = mock_rm
        
        mock_device = MagicMock()
        mock_device.resource_name = "GPIB0::2::INSTR"
        mock_rm.open_resource.return_value = mock_device

        from comfylab.blocks.visa import visa_rm_wrapper
        visa_rm_wrapper._rm = None

        blueprint = {
            "blocks": [
                {"id": "device", "type": "visa/core/device", "properties": {"Address": "GPIB0::2::INSTR"}},
                {"id": "config_wave", "type": "devices/virtual/signal_generator/config_wave", "properties": {
                    "WaveType": "square",
                    "Frequency": 2500.0,
                    "Amplitude": 2.5,
                    "Offset": -0.5,
                    "Phase": 90.0,
                    "DutyCycle": 30.0
                }},
                {"id": "config_chirp", "type": "devices/virtual/signal_generator/config_chirp", "properties": {
                    "Chirp": True,
                    "Variation": 150.0,
                    "Period": 2.0
                }},
                {"id": "set_output", "type": "devices/virtual/signal_generator/output", "properties": {
                    "Output": True
                }}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_block": "device", "source_pin": "Out", "target_block": "config_wave", "target_pin": "In"},
                {"id": "l2", "type": "exec", "source_block": "config_wave", "source_pin": "Out", "target_block": "config_chirp", "target_pin": "In"},
                {"id": "l3", "type": "exec", "source_block": "config_chirp", "source_pin": "Out", "target_block": "set_output", "target_pin": "In"},
                {"id": "l4", "type": "data", "source_block": "device", "source_pin": "Device", "target_block": "config_wave", "target_pin": "Device"},
                {"id": "l5", "type": "data", "source_block": "device", "source_pin": "Device", "target_block": "config_chirp", "target_pin": "Device"},
                {"id": "l6", "type": "data", "source_block": "device", "source_pin": "Device", "target_block": "set_output", "target_pin": "Device"}
            ]
        }

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)

        await engine.run(start_block_id="device", start_pin_name="Open")

        # Verify calls to device.write
        write_calls = [call[0][0] for call in mock_device.write.call_args_list]
        assert ":SOURce1:FUNCtion SQUARE" in write_calls
        assert ":SOURce1:FREQuency 2500.0" in write_calls
        assert ":SOURce1:VOLTage 2.5" in write_calls
        assert ":SOURce1:VOLTage:OFFSet -0.5" in write_calls
        assert ":SOURce1:PHASe 90.0" in write_calls
        assert ":SOURce1:PULSe:DCYCle 30.0" in write_calls
        assert ":SOURce1:FREQuency:CHIRp ON" in write_calls
        assert ":SOURce1:FREQuency:CVAR 150.0" in write_calls
        assert ":SOURce1:FREQuency:CPER 2.0" in write_calls
        assert ":OUTPut1:STATe ON" in write_calls

        await engine._teardown_all()


@pytest.mark.asyncio
async def test_virt_osc_blocks_execution():
    with patch("comfylab.blocks.visa.pyvisa") as mock_pyvisa:
        mock_rm = MagicMock()
        mock_pyvisa.ResourceManager.return_value = mock_rm
        
        mock_device = MagicMock()
        mock_device.resource_name = "GPIB0::3::INSTR"
        mock_rm.open_resource.return_value = mock_device

        # Setup queries for time and waveform
        def mock_query(cmd):
            if ":TIMebase:DATA?" in cmd or "horiz:data?" in cmd:
                return "0.0,0.1,0.2"
            if ":CHANnel1:DATA?" in cmd or "c1:data?" in cmd:
                return "1.2,1.5,1.8"
            return ""
        mock_device.query.side_effect = mock_query

        from comfylab.blocks.visa import visa_rm_wrapper
        visa_rm_wrapper._rm = None

        blueprint = {
            "blocks": [
                {"id": "device", "type": "visa/core/device", "properties": {"Address": "GPIB0::3::INSTR"}},
                {"id": "timebase", "type": "devices/virtual/oscilloscope/timebase", "properties": {
                    "Scale": 0.005,
                    "Offset": -0.001,
                    "Points": 2000
                }},
                {"id": "channel", "type": "devices/virtual/oscilloscope/channel", "properties": {
                    "Channel": 1,
                    "Enable": True,
                    "Scale": 2.0,
                    "Offset": 0.1
                }},
                {"id": "trigger", "type": "devices/virtual/oscilloscope/trigger", "properties": {
                    "Mode": "free"
                }},
                {"id": "state", "type": "devices/virtual/oscilloscope/state", "properties": {
                    "State": "run"
                }},
                {"id": "acquire", "type": "devices/virtual/oscilloscope/acquire", "properties": {
                    "Channel": 1
                }}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_block": "device", "source_pin": "Out", "target_block": "timebase", "target_pin": "In"},
                {"id": "l2", "type": "exec", "source_block": "timebase", "source_pin": "Out", "target_block": "channel", "target_pin": "In"},
                {"id": "l3", "type": "exec", "source_block": "channel", "source_pin": "Out", "target_block": "trigger", "target_pin": "In"},
                {"id": "l4", "type": "exec", "source_block": "trigger", "source_pin": "Out", "target_block": "state", "target_pin": "In"},
                {"id": "l5", "type": "exec", "source_block": "state", "source_pin": "Out", "target_block": "acquire", "target_pin": "In"},
                {"id": "l6", "type": "data", "source_block": "device", "source_pin": "Device", "target_block": "timebase", "target_pin": "Device"},
                {"id": "l7", "type": "data", "source_block": "device", "source_pin": "Device", "target_block": "channel", "target_pin": "Device"},
                {"id": "l8", "type": "data", "source_block": "device", "source_pin": "Device", "target_block": "trigger", "target_pin": "Device"},
                {"id": "l9", "type": "data", "source_block": "device", "source_pin": "Device", "target_block": "state", "target_pin": "Device"},
                {"id": "la", "type": "data", "source_block": "device", "source_pin": "Device", "target_block": "acquire", "target_pin": "Device"}
            ]
        }

        # Setup telemetry connection tracker
        telemetry_payloads = []
        async def mock_telemetry_callback(run_id: str, msg):
            telemetry_payloads.append(msg)

        engine = ExecutionEngine()
        engine.telemetry_callback = mock_telemetry_callback
        engine.load_blueprint(blueprint)

        await engine.run(start_block_id="device", start_pin_name="Open")

        # Verify calls to device.write
        write_calls = [call[0][0] for call in mock_device.write.call_args_list]
        assert ":TIMebase:SCALe 0.005" in write_calls
        assert ":TIMebase:POSition -0.001" in write_calls
        assert ":ACQuire:POINts 2000" in write_calls
        assert ":CHANnel1:DISPlay ON" in write_calls
        assert ":CHANnel1:SCALe 2.0" in write_calls
        assert ":CHANnel1:OFFSet 0.1" in write_calls
        assert ":TRIGger:MODE FREE" in write_calls
        assert ":RUN" in write_calls

        # Verify outputs from acquire block
        acquire_block = engine.blocks["acquire"]
        assert list(acquire_block._last_time) == [0.0, 0.1, 0.2]
        assert list(acquire_block._last_waveform) == [1.2, 1.5, 1.8]

        # Verify telemetry binary payload was generated
        binary_payloads = [p for p in telemetry_payloads if isinstance(p, bytes)]
        assert len(binary_payloads) == 1
        bin_data = binary_payloads[0]
        assert len(bin_data) > 40  # Header (36 bytes ID + 4 bytes size) + floats

        await engine._teardown_all()


@pytest.mark.asyncio
async def test_virt_osc_connect_block_teardown_sends_stop():
    with patch("comfylab.blocks.visa.pyvisa") as mock_pyvisa:
        mock_rm = MagicMock()
        mock_pyvisa.ResourceManager.return_value = mock_rm

        mock_device = MagicMock()
        mock_device.resource_name = "GPIB0::3::INSTR"
        mock_rm.open_resource.return_value = mock_device

        from comfylab.blocks.visa import visa_rm_wrapper
        visa_rm_wrapper._rm = None

        blueprint = {
            "blocks": [
                {"id": "connect", "type": "devices/virtual/oscilloscope/connect", "properties": {
                    "Address": "GPIB0::3::INSTR"
                }}
            ],
            "links": []
        }

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)
        await engine.run(start_block_id="connect", start_pin_name="Open")

        # Teardown runs automatically on completion - device should be closed
        connect_block = engine.blocks["connect"]
        assert connect_block._device is None

        # Verify teardown sent ':STOP' command
        write_calls = [call[0][0] for call in mock_device.write.call_args_list]
        assert ":STOP" in write_calls
        mock_device.close.assert_called()


@pytest.mark.asyncio
async def test_virt_siggen_connect_block_teardown_sends_out_off():
    with patch("comfylab.blocks.visa.pyvisa") as mock_pyvisa:
        mock_rm = MagicMock()
        mock_pyvisa.ResourceManager.return_value = mock_rm

        mock_device = MagicMock()
        mock_device.resource_name = "GPIB0::2::INSTR"
        mock_rm.open_resource.return_value = mock_device

        from comfylab.blocks.visa import visa_rm_wrapper
        visa_rm_wrapper._rm = None

        blueprint = {
            "blocks": [
                {"id": "connect", "type": "devices/virtual/signal_generator/connect", "properties": {
                    "Address": "GPIB0::2::INSTR"
                }}
            ],
            "links": []
        }

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)
        await engine.run(start_block_id="connect", start_pin_name="Open")

        # Teardown runs automatically on completion - device should be closed
        connect_block = engine.blocks["connect"]
        assert connect_block._device is None

        # Verify teardown sent ':OUTPut1:STATe OFF' command
        write_calls = [call[0][0] for call in mock_device.write.call_args_list]
        assert ":OUTPut1:STATe OFF" in write_calls
        mock_device.close.assert_called()


@pytest.mark.asyncio
async def test_virt_osc_connect_chains_with_other_virt_blocks():
    """Verify that the VirtOsc connect block output Device handle is usable by other Virt blocks."""
    with patch("comfylab.blocks.visa.pyvisa") as mock_pyvisa:
        mock_rm = MagicMock()
        mock_pyvisa.ResourceManager.return_value = mock_rm

        mock_device = MagicMock()
        mock_device.resource_name = "GPIB0::3::INSTR"
        mock_rm.open_resource.return_value = mock_device

        def mock_query(cmd):
            if ":TIMebase:DATA?" in cmd or "horiz:data?" in cmd:
                return "0.0,0.1,0.2"
            if ":CHANnel1:DATA?" in cmd or "c1:data?" in cmd:
                return "1.0,2.0,3.0"
            return ""
        mock_device.query.side_effect = mock_query

        from comfylab.blocks.visa import visa_rm_wrapper
        visa_rm_wrapper._rm = None

        blueprint = {
            "blocks": [
                {"id": "connect", "type": "devices/virtual/oscilloscope/connect", "properties": {
                    "Address": "GPIB0::3::INSTR"
                }},
                {"id": "state", "type": "devices/virtual/oscilloscope/state", "properties": {
                    "State": "run"
                }},
                {"id": "acquire", "type": "devices/virtual/oscilloscope/acquire", "properties": {
                    "Channel": 1
                }}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_block": "connect", "source_pin": "Out", "target_block": "state", "target_pin": "In"},
                {"id": "l2", "type": "exec", "source_block": "state", "source_pin": "Out", "target_block": "acquire", "target_pin": "In"},
                {"id": "l3", "type": "data", "source_block": "connect", "source_pin": "Device", "target_block": "state", "target_pin": "Device"},
                {"id": "l4", "type": "data", "source_block": "connect", "source_pin": "Device", "target_block": "acquire", "target_pin": "Device"}
            ]
        }

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)
        await engine.run(start_block_id="connect", start_pin_name="Open")

        write_calls = [call[0][0] for call in mock_device.write.call_args_list]
        assert ":RUN" in write_calls

        acquire_block = engine.blocks["acquire"]
        assert list(acquire_block._last_waveform) == [1.0, 2.0, 3.0]

        # Teardown should send ':STOP' as safety command
        await engine._teardown_all()
        write_calls = [call[0][0] for call in mock_device.write.call_args_list]
        assert ":STOP" in write_calls


def test_match_visa_device():
    from comfylab.blocks.visa import match_visa_device

    dev_keysight = {
        "address": "USB0::0x0957::0x17A6::MY50340123::INSTR",
        "idn": "KEYSIGHT TECHNOLOGIES,DSO-X 3024A,MY50340123,02.43.2018020600",
        "vendor": "KEYSIGHT TECHNOLOGIES",
        "model": "DSO-X 3024A"
    }

    # Empty query matches all
    assert match_visa_device(dev_keysight, "") is True
    assert match_visa_device(dev_keysight, "   ") is True

    # Case-insensitive substring match
    assert match_visa_device(dev_keysight, "keysight") is True
    assert match_visa_device(dev_keysight, "DSO-X") is True
    assert match_visa_device(dev_keysight, "3024A") is True
    assert match_visa_device(dev_keysight, "Tektronix") is False

    # Address matching
    assert match_visa_device(dev_keysight, "0x0957") is True
    assert match_visa_device(dev_keysight, "MY50340123") is True

    # Comma-separated multi-token match (all tokens must match)
    assert match_visa_device(dev_keysight, "Keysight, 3024") is True
    assert match_visa_device(dev_keysight, "Keysight, Tektronix") is False

    # Regex matching
    assert match_visa_device(dev_keysight, r"DSO-?X\s*3024[A-Z]?") is True
    assert match_visa_device(dev_keysight, r"^USB\d+::") is True


def test_discover_visa_devices():
    from comfylab.blocks.visa import discover_visa_devices, visa_rm_wrapper

    with patch("comfylab.blocks.visa.pyvisa") as mock_pyvisa:
        mock_rm = MagicMock()
        mock_pyvisa.ResourceManager.return_value = mock_rm
        visa_rm_wrapper._rm = None

        mock_rm.list_resources.return_value = [
            "USB0::0x0957::0x17A6::MY50340123::INSTR",
            "GPIB0::24::INSTR",
            "ASRL1::INSTR"
        ]

        dev_usb = MagicMock()
        dev_usb.query.return_value = "KEYSIGHT TECHNOLOGIES,DSO-X 3024A,MY50340123,02.43"

        dev_gpib = MagicMock()
        dev_gpib.query.return_value = "KEITHLEY INSTRUMENTS INC.,MODEL 2400,1234567,C30"

        dev_asrl = MagicMock()
        dev_asrl.query.return_value = "GENERIC,SERIAL_DEV,111,1.0"

        def open_side_effect(addr):
            if addr.startswith("USB"): return dev_usb
            if addr.startswith("GPIB"): return dev_gpib
            if addr.startswith("ASRL"): return dev_asrl
            raise ValueError(f"Unknown {addr}")

        mock_rm.open_resource.side_effect = open_side_effect

        # Default scan: USB, GPIB, TCPIP (safely excludes ASRL)
        res_default = discover_visa_devices()
        assert len(res_default) == 2
        addresses = [d["address"] for d in res_default]
        assert "USB0::0x0957::0x17A6::MY50340123::INSTR" in addresses
        assert "GPIB0::24::INSTR" in addresses
        assert "ASRL1::INSTR" not in addresses

        # Scan including Serial
        res_all = discover_visa_devices("All (incl. Serial)")
        assert len(res_all) == 3

        # USB only
        res_usb = discover_visa_devices("USB")
        assert len(res_usb) == 1
        assert res_usb[0]["model"] == "DSO-X 3024A"


@pytest.mark.asyncio
async def test_visa_find_device_block_execution():
    with patch("comfylab.blocks.visa.pyvisa") as mock_pyvisa:
        mock_rm = MagicMock()
        mock_pyvisa.ResourceManager.return_value = mock_rm

        from comfylab.blocks.visa import visa_rm_wrapper
        visa_rm_wrapper._rm = None

        mock_rm.list_resources.return_value = [
            "USB0::0x0957::0x17A6::MY50340123::INSTR",
            "GPIB0::24::INSTR"
        ]

        dev_usb = MagicMock()
        dev_usb.query.return_value = "KEYSIGHT TECHNOLOGIES,DSO-X 3024A,MY50340123,02.43"

        dev_gpib = MagicMock()
        dev_gpib.query.return_value = "KEITHLEY INSTRUMENTS INC.,MODEL 2400,1234567,C30"

        def open_side_effect(addr, **kwargs):
            if addr.startswith("USB"): return dev_usb
            if addr.startswith("GPIB"): return dev_gpib
            raise ValueError(f"Unknown {addr}")

        mock_rm.open_resource.side_effect = open_side_effect

        blueprint = {
            "blocks": [
                {"id": "find", "type": "visa/core/find_device", "properties": {
                    "Query": "3024A"
                }},
                {"id": "connect", "type": "visa/core/device", "properties": {}},
                {"id": "query", "type": "visa/core/query", "properties": {"Command": "*IDN?"}}
            ],
            "links": [
                # find -> connect -> query
                {"id": "l1", "type": "exec", "source_block": "find", "source_pin": "Out", "target_block": "connect", "target_pin": "Open"},
                {"id": "l2", "type": "exec", "source_block": "connect", "source_pin": "Out", "target_block": "query", "target_pin": "In"},
                # find Address output -> connect Address input
                {"id": "l3", "type": "data", "source_block": "find", "source_pin": "Address", "target_block": "connect", "target_pin": "Address"},
                # connect Device -> query Device
                {"id": "l4", "type": "data", "source_block": "connect", "source_pin": "Device", "target_block": "query", "target_pin": "Device"}
            ]
        }

        engine = ExecutionEngine()
        engine.load_blueprint(blueprint)
        await engine.run(start_block_id="find", start_pin_name="In")

        find_block = engine.blocks["find"]
        assert find_block._found is True
        assert find_block._matched_address == "USB0::0x0957::0x17A6::MY50340123::INSTR"
        assert "KEYSIGHT" in find_block._matched_idn
        assert len(find_block._all_devices) == 2


def test_visa_scan_api_endpoint():
    from fastapi.testclient import TestClient
    from backend.main import app
    from comfylab.blocks.visa import visa_rm_wrapper

    with patch("comfylab.blocks.visa.pyvisa") as mock_pyvisa:
        mock_rm = MagicMock()
        mock_pyvisa.ResourceManager.return_value = mock_rm
        visa_rm_wrapper._rm = None

        mock_rm.list_resources.return_value = ["GPIB0::24::INSTR"]
        dev_mock = MagicMock()
        dev_mock.query.return_value = "KEITHLEY INSTRUMENTS INC.,MODEL 2400,1234567,C30"
        mock_rm.open_resource.return_value = dev_mock

        client = TestClient(app)
        response = client.get("/blocks/visa/scan")
        assert response.status_code == 200
        data = response.json()
        assert "devices" in data
        assert data["count"] == 1
        assert data["devices"][0]["model"] == "MODEL 2400"


def test_managed_visa_device_auto_clear_on_timeout():
    from comfylab.blocks.visa import ManagedVISADevice
    import pyvisa

    mock_rm = MagicMock()
    mock_raw_dev = MagicMock()
    mock_raw_dev.resource_name = "USB0::0x1234::INSTR"
    mock_rm.open_resource.return_value = mock_raw_dev

    # Simulate timeout error on query
    tmo_err = pyvisa.errors.VisaIOError(pyvisa.constants.VI_ERROR_TMO)
    mock_raw_dev.query.side_effect = tmo_err

    managed = ManagedVISADevice(mock_rm, "USB0::0x1234::INSTR")
    with pytest.raises(pyvisa.errors.VisaIOError):
        managed.query("*IDN?")

    # Auto-clear should have been executed to un-stall the USB endpoint
    mock_raw_dev.clear.assert_called()


def test_managed_visa_device_auto_reconnect_on_conn_lost():
    from comfylab.blocks.visa import ManagedVISADevice
    import pyvisa

    mock_rm = MagicMock()
    dev1 = MagicMock()
    dev1.resource_name = "USB0::0x1234::INSTR"
    dev2 = MagicMock()
    dev2.resource_name = "USB0::0x1234::INSTR"
    mock_rm.open_resource.side_effect = [dev1, dev2]

    # First device encounters connection lost (e.g. instrument rebooted / cable unplugged)
    conn_err = pyvisa.errors.VisaIOError(pyvisa.constants.VI_ERROR_CONN_LOST)
    dev1.write.side_effect = conn_err

    managed = ManagedVISADevice(mock_rm, "USB0::0x1234::INSTR")
    assert managed.raw_device is dev1

    with pytest.raises(pyvisa.errors.VisaIOError):
        managed.write("*RST")

    # dev1 should have been closed and dev2 opened via reconnect
    dev1.close.assert_called()
    assert mock_rm.open_resource.call_count == 2
    assert managed.raw_device is dev2


def test_base_instrument_driver_auto_clear_on_error():
    from comfylab.devices.base import BaseInstrumentDriver

    mock_dev = MagicMock()
    mock_dev.resource_name = "USB0::0x5678::INSTR"
    mock_dev.query.side_effect = RuntimeError("Stalled USB pipe")
    mock_dev.read_raw.side_effect = RuntimeError("Read timeout")

    driver = BaseInstrumentDriver(mock_dev)

    with pytest.raises(RuntimeError):
        driver.query(":WAVeform:PREamble?")
    mock_dev.clear.assert_called()

    mock_dev.clear.reset_mock()
    with pytest.raises(RuntimeError):
        driver.query_raw(":WAVeform:DATA?")
    mock_dev.clear.assert_called()


