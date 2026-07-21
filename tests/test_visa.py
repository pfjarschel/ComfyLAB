from unittest.mock import MagicMock, patch
import pytest
from comfylab.engine.executor import ExecutionEngine
from comfylab.engine.registry import get_all_blocks_schema

def test_visa_blocks_registration():
    schema = get_all_blocks_schema()
    
    # Assert they are present in the global registry
    assert "visa/core/resource_manager" in schema
    assert "visa/core/device" in schema
    assert "visa/core/write" in schema
    assert "visa/core/read" in schema
    assert "visa/core/query" in schema

    rm_schema = schema["visa/core/resource_manager"]
    assert rm_schema["name"] == "VISA Resource Manager"
    assert rm_schema["category"] == "VISA/Core"
    assert len(rm_schema["dataOuts"]) == 1
    assert rm_schema["dataOuts"][0]["name"] == "Resources"

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
async def test_pfj_siggen_blocks_execution():
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
                {"id": "config_wave", "type": "visa/signal_generator/config_wave", "properties": {
                    "WaveType": "square",
                    "Frequency": 2500.0,
                    "Amplitude": 2.5,
                    "Offset": -0.5,
                    "Phase": 90.0,
                    "DutyCycle": 30.0
                }},
                {"id": "config_chirp", "type": "visa/signal_generator/config_chirp", "properties": {
                    "Chirp": True,
                    "Variation": 150.0,
                    "Period": 2.0
                }},
                {"id": "set_output", "type": "visa/signal_generator/set_output", "properties": {
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
        assert "wave:wave square" in write_calls
        assert "freq:freq 2500.0" in write_calls
        assert "amp:amp 2.5" in write_calls
        assert "amp:offs -0.5" in write_calls
        assert "wave:phas 90.0" in write_calls
        assert "wave:dc 30.0" in write_calls
        assert "freq:chrp True" in write_calls
        assert "freq:cvar 150.0" in write_calls
        assert "freq:cper 2.0" in write_calls
        assert "out True" in write_calls

        await engine._teardown_all()


@pytest.mark.asyncio
async def test_pfj_osc_blocks_execution():
    with patch("comfylab.blocks.visa.pyvisa") as mock_pyvisa:
        mock_rm = MagicMock()
        mock_pyvisa.ResourceManager.return_value = mock_rm
        
        mock_device = MagicMock()
        mock_device.resource_name = "GPIB0::3::INSTR"
        mock_rm.open_resource.return_value = mock_device

        # Setup queries for time and waveform
        def mock_query(cmd):
            if "horiz:data?" in cmd:
                return "0.0,0.1,0.2"
            if "c1:data?" in cmd:
                return "1.2,1.5,1.8"
            return ""
        mock_device.query.side_effect = mock_query

        from comfylab.blocks.visa import visa_rm_wrapper
        visa_rm_wrapper._rm = None

        blueprint = {
            "blocks": [
                {"id": "device", "type": "visa/core/device", "properties": {"Address": "GPIB0::3::INSTR"}},
                {"id": "timebase", "type": "visa/oscilloscope/timebase", "properties": {
                    "Scale": 0.005,
                    "Offset": -0.001,
                    "Points": 2000
                }},
                {"id": "channel", "type": "visa/oscilloscope/channel", "properties": {
                    "Channel": 1,
                    "Enable": True,
                    "Scale": 2.0,
                    "Offset": 0.1
                }},
                {"id": "trigger", "type": "visa/oscilloscope/trigger", "properties": {
                    "Mode": "free"
                }},
                {"id": "state", "type": "visa/oscilloscope/state", "properties": {
                    "State": "run"
                }},
                {"id": "acquire", "type": "visa/oscilloscope/acquire", "properties": {
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
        assert "horiz:scale 0.005" in write_calls
        assert "horiz:offset -0.001" in write_calls
        assert "acq:points 2000" in write_calls
        assert "c1:enable True" in write_calls
        assert "c1:scale 2.0" in write_calls
        assert "c1:offset 0.1" in write_calls
        assert "trig:free" in write_calls
        assert "run" in write_calls

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
async def test_pfj_osc_connect_block_teardown_sends_stop():
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
                {"id": "connect", "type": "visa/oscilloscope/connect", "properties": {
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

        # Verify teardown sent 'stop' command
        write_calls = [call[0][0] for call in mock_device.write.call_args_list]
        assert "stop" in write_calls
        mock_device.close.assert_called()


@pytest.mark.asyncio
async def test_pfj_siggen_connect_block_teardown_sends_out_off():
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
                {"id": "connect", "type": "visa/signal_generator/connect", "properties": {
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

        # Verify teardown sent 'out False' command
        write_calls = [call[0][0] for call in mock_device.write.call_args_list]
        assert "out False" in write_calls
        mock_device.close.assert_called()


@pytest.mark.asyncio
async def test_pfj_osc_connect_chains_with_other_pfj_blocks():
    """Verify that the PFJOsc connect block output Device handle is usable by other PFJ blocks."""
    with patch("comfylab.blocks.visa.pyvisa") as mock_pyvisa:
        mock_rm = MagicMock()
        mock_pyvisa.ResourceManager.return_value = mock_rm

        mock_device = MagicMock()
        mock_device.resource_name = "GPIB0::3::INSTR"
        mock_rm.open_resource.return_value = mock_device

        def mock_query(cmd):
            if "horiz:data?" in cmd:
                return "0.0,0.1,0.2"
            if "c1:data?" in cmd:
                return "1.0,2.0,3.0"
            return ""
        mock_device.query.side_effect = mock_query

        from comfylab.blocks.visa import visa_rm_wrapper
        visa_rm_wrapper._rm = None

        blueprint = {
            "blocks": [
                {"id": "connect", "type": "visa/oscilloscope/connect", "properties": {
                    "Address": "GPIB0::3::INSTR"
                }},
                {"id": "state", "type": "visa/oscilloscope/state", "properties": {
                    "State": "run"
                }},
                {"id": "acquire", "type": "visa/oscilloscope/acquire", "properties": {
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

        # Verify that state and acquire ran with the device handle
        write_calls = [call[0][0] for call in mock_device.write.call_args_list]
        assert "run" in write_calls

        acquire_block = engine.blocks["acquire"]
        assert list(acquire_block._last_waveform) == [1.0, 2.0, 3.0]

        # Teardown should send 'stop' as safety command
        await engine._teardown_all()
        write_calls = [call[0][0] for call in mock_device.write.call_args_list]
        assert "stop" in write_calls
