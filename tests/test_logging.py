import io
import json
import logging
from pathlib import Path
import pytest
import asyncio
from comfylab.engine.logging import run_id_var, block_id_var, setup_logging, StructuredLoggingFilter, JsonFormatter

def test_context_vars_and_filter():
    # Setup test logger
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    # Custom stream to capture output
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    formatter = logging.Formatter("[%(run_id)s] [%(block_id)s] %(message)s")
    handler.setFormatter(formatter)
    handler.addFilter(StructuredLoggingFilter())
    logger.addHandler(handler)

    try:
        # Default state (N/A)
        logger.info("Message 1")
        assert "[N/A] [N/A] Message 1" in stream.getvalue()

        # Set context variables
        run_token = run_id_var.set("test-run-123")
        block_token = block_id_var.set("test-block-abc")
        
        stream.seek(0)
        stream.truncate()
        logger.info("Message 2")
        assert "[test-run-123] [test-block-abc] Message 2" in stream.getvalue()
        
        # Reset context variables
        run_id_var.reset(run_token)
        block_id_var.reset(block_token)
        
        stream.seek(0)
        stream.truncate()
        logger.info("Message 3")
        assert "[N/A] [N/A] Message 3" in stream.getvalue()
    finally:
        logger.removeHandler(handler)

def test_json_formatter():
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Structured log message",
        args=(),
        exc_info=None
    )
    record.run_id = "run-999"
    record.block_id = "block-888"
    
    formatter = JsonFormatter()
    formatted = formatter.format(record)
    data = json.loads(formatted)
    
    assert data["level"] == "INFO"
    assert data["name"] == "test_logger"
    assert data["message"] == "Structured log message"
    assert data["run_id"] == "run-999"
    assert data["block_id"] == "block-888"
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_async_context_propagation():
    logger = logging.getLogger("test_async")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    formatter = logging.Formatter("[%(run_id)s] [%(block_id)s] %(message)s")
    handler.setFormatter(formatter)
    handler.addFilter(StructuredLoggingFilter())
    logger.addHandler(handler)

    async def log_task(run_id, block_id, delay):
        run_token = run_id_var.set(run_id)
        block_token = block_id_var.set(block_id)
        try:
            logger.info("Before sleep")
            await asyncio.sleep(delay)
            logger.info("After sleep")
        finally:
            run_id_var.reset(run_token)
            block_id_var.reset(block_token)

    try:
        # Launch two concurrent tasks with different context
        await asyncio.gather(
            log_task("run-A", "block-A", 0.05),
            log_task("run-B", "block-B", 0.02)
        )
        
        output = stream.getvalue()
        # Ensure context was kept separate and isolated across sleep cycles
        assert "[run-A] [block-A] Before sleep" in output
        assert "[run-A] [block-A] After sleep" in output
        assert "[run-B] [block-B] Before sleep" in output
        assert "[run-B] [block-B] After sleep" in output
    finally:
        logger.removeHandler(handler)

def test_setup_logging_initialization():
    setup_logging()
    
    # Assert logs directory exists and is created
    log_dir = Path.home() / ".comfylab" / "logs"
    assert log_dir.exists()
    
    log_file = log_dir / "comfylab.log"
    assert log_file.exists()
    
    # Root logger should have setup handlers
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) >= 2
    
    # We should have a StreamHandler and a RotatingFileHandler
    handler_types = [type(h) for h in root_logger.handlers]
    assert logging.StreamHandler in handler_types
    assert any(isinstance(h, logging.handlers.RotatingFileHandler) for h in root_logger.handlers)

def test_setup_logging_levels_from_env(monkeypatch):
    monkeypatch.setenv("COMFYLAB_CONSOLE_LEVEL", "ERROR")
    monkeypatch.setenv("COMFYLAB_FILE_LEVEL", "DEBUG")
    setup_logging()
    
    root_logger = logging.getLogger()
    console_handler = next(h for h in root_logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.handlers.RotatingFileHandler))
    file_handler = next(h for h in root_logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler))
    
    assert console_handler.level == logging.ERROR
    assert file_handler.level == logging.DEBUG

class MockBlock:
    def __init__(self, block_id, display_name):
        self.id = block_id
        self.display_name = display_name

class MockClusterBlock(MockBlock):
    _cluster_file_path = "workspace/clusters/test_cluster.json"

def test_set_block_context_helper():
    from comfylab.engine.logging import set_block_context, reset_block_context, block_id_var, block_name_var, block_file_var
    
    block = MockBlock("block_1", "Virtual Sensor")
    tokens = set_block_context(block)
    try:
        assert block_id_var.get() == "block_1"
        assert block_name_var.get() == "Virtual Sensor"
        assert "test_logging.py" in block_file_var.get()
    finally:
        reset_block_context(tokens)
        
    assert block_id_var.get() == ""
    assert block_name_var.get() == ""
    assert block_file_var.get() == ""
    
    # Test cluster block custom path
    cluster_block = MockClusterBlock("cluster_1", "My Cluster")
    tokens = set_block_context(cluster_block)
    try:
        assert block_id_var.get() == "cluster_1"
        assert block_name_var.get() == "My Cluster"
        assert block_file_var.get() == "workspace/clusters/test_cluster.json"
    finally:
        reset_block_context(tokens)
