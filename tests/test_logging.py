import io
import json
import logging
from pathlib import Path
import pytest
import asyncio
from comfylab.engine.logging import run_id_var, node_id_var, setup_logging, StructuredLoggingFilter, JsonFormatter

def test_context_vars_and_filter():
    # Setup test logger
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    # Custom stream to capture output
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    formatter = logging.Formatter("[%(run_id)s] [%(node_id)s] %(message)s")
    handler.setFormatter(formatter)
    handler.addFilter(StructuredLoggingFilter())
    logger.addHandler(handler)

    try:
        # Default state (N/A)
        logger.info("Message 1")
        assert "[N/A] [N/A] Message 1" in stream.getvalue()

        # Set context variables
        run_token = run_id_var.set("test-run-123")
        node_token = node_id_var.set("test-node-abc")
        
        stream.seek(0)
        stream.truncate()
        logger.info("Message 2")
        assert "[test-run-123] [test-node-abc] Message 2" in stream.getvalue()
        
        # Reset context variables
        run_id_var.reset(run_token)
        node_id_var.reset(node_token)
        
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
    record.node_id = "node-888"
    
    formatter = JsonFormatter()
    formatted = formatter.format(record)
    data = json.loads(formatted)
    
    assert data["level"] == "INFO"
    assert data["name"] == "test_logger"
    assert data["message"] == "Structured log message"
    assert data["run_id"] == "run-999"
    assert data["node_id"] == "node-888"
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_async_context_propagation():
    logger = logging.getLogger("test_async")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    formatter = logging.Formatter("[%(run_id)s] [%(node_id)s] %(message)s")
    handler.setFormatter(formatter)
    handler.addFilter(StructuredLoggingFilter())
    logger.addHandler(handler)

    async def log_task(run_id, node_id, delay):
        run_token = run_id_var.set(run_id)
        node_token = node_id_var.set(node_id)
        try:
            logger.info("Before sleep")
            await asyncio.sleep(delay)
            logger.info("After sleep")
        finally:
            run_id_var.reset(run_token)
            node_id_var.reset(node_token)

    try:
        # Launch two concurrent tasks with different context
        await asyncio.gather(
            log_task("run-A", "node-A", 0.05),
            log_task("run-B", "node-B", 0.02)
        )
        
        output = stream.getvalue()
        # Ensure context was kept separate and isolated across sleep cycles
        assert "[run-A] [node-A] Before sleep" in output
        assert "[run-A] [node-A] After sleep" in output
        assert "[run-B] [node-B] Before sleep" in output
        assert "[run-B] [node-B] After sleep" in output
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

class MockNode:
    def __init__(self, node_id, display_name):
        self.id = node_id
        self.display_name = display_name

class MockClusterNode(MockNode):
    _cluster_file_path = "workspace/clusters/test_cluster.json"

def test_set_node_context_helper():
    from comfylab.engine.logging import set_node_context, reset_node_context, node_id_var, node_name_var, node_file_var
    
    node = MockNode("node_1", "Virtual Sensor")
    tokens = set_node_context(node)
    try:
        assert node_id_var.get() == "node_1"
        assert node_name_var.get() == "Virtual Sensor"
        assert "test_logging.py" in node_file_var.get()
    finally:
        reset_node_context(tokens)
        
    assert node_id_var.get() == ""
    assert node_name_var.get() == ""
    assert node_file_var.get() == ""
    
    # Test cluster node custom path
    cluster_node = MockClusterNode("cluster_1", "My Cluster")
    tokens = set_node_context(cluster_node)
    try:
        assert node_id_var.get() == "cluster_1"
        assert node_name_var.get() == "My Cluster"
        assert node_file_var.get() == "workspace/clusters/test_cluster.json"
    finally:
        reset_node_context(tokens)
