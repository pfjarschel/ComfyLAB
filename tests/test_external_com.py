import pytest
from unittest.mock import patch, AsyncMock
from comfylab.blocks import external_com
from comfylab.blocks.external_com import (
    COMOpenSessionBlock,
    COMInvokeMemberBlock,
    COMCloseSessionBlock,
    COMControllerBlock
)
from comfylab.blocks.base import ExecutionContext
from comfylab.engine.executor import ExecutionEngine


def test_com_blocks_metadata():
    open_block = COMOpenSessionBlock("open_1")
    assert open_block.display_name == "Open COM Session"
    assert "Session" in open_block.outputs

    call_block = COMInvokeMemberBlock("call_1")
    assert call_block.display_name == "Invoke COM Member"
    assert "Result" in call_block.outputs
    assert "Session" in call_block.inputs

    close_block = COMCloseSessionBlock("close_1")
    assert close_block.display_name == "Close COM Session"
    assert "Session" in close_block.inputs

    ctrl_block = COMControllerBlock("ctrl_1")
    assert ctrl_block.display_name == "ActiveX / COM Controller"
    assert "Result" in ctrl_block.outputs


@pytest.mark.asyncio
async def test_com_session_lifecycle():
    engine = ExecutionEngine()
    context = ExecutionContext(engine, "test_run", engine.lock_manager)

    # 1. Open Session
    open_block = COMOpenSessionBlock("open_1", {
        "ProgID": "Excel.Application",
        "Bitness": "Auto"
    })
    engine.blocks["open_1"] = open_block

    with patch("comfylab.blocks.external_com._run_com_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"status": "ok"}
        out_pin = await open_block.execute(context, "In")
        assert out_pin == "Out"

    session_id = await open_block.pull_data(context, "Session")
    assert session_id is not None
    assert session_id in external_com._ACTIVE_COM_SESSIONS

    # 2. Invoke Member
    call_block = COMInvokeMemberBlock("call_1", {
        "Session": session_id,
        "MemberName": "Version",
        "ActionType": "Get Property"
    })
    engine.blocks["call_1"] = call_block

    with patch("comfylab.blocks.external_com._run_com_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"result": "16.0"}
        out_pin = await call_block.execute(context, "In")
        assert out_pin == "Out"

    result_val = await call_block.pull_data(context, "Result")
    assert result_val == "16.0"

    # 3. Close Session
    close_block = COMCloseSessionBlock("close_1", {
        "Session": session_id
    })
    engine.blocks["close_1"] = close_block

    out_pin = await close_block.execute(context, "In")
    assert out_pin == "Out"
    assert session_id not in external_com._ACTIVE_COM_SESSIONS
