import pytest
import ctypes
import ctypes.util
import asyncio
from comfylab.engine.executor import ExecutionEngine
from comfylab.engine.registry import get_node_class

# Check if libm.so.6 can be found on this platform
lib_path = ctypes.util.find_library("m") or "libm.so.6"
libc_path = ctypes.util.find_library("c") or "libc.so.6"

@pytest.mark.asyncio
async def test_library_loading():
    klass = get_node_class(r"dll\/SO/load")
    loader_node = klass("lib_loader", properties={"LibraryPath": lib_path})
    
    class MockContext:
        async def pull(self, node_id, pin_name):
            return lib_path

    await loader_node.execute(MockContext(), "Load")
    assert loader_node._lib is not None
    assert loader_node._loaded_path == lib_path

    # Clean up / teardown
    await loader_node.teardown()
    assert loader_node._lib is None
    assert loader_node._loaded_path is None


@pytest.mark.asyncio
async def test_library_loading_empty_path():
    blueprint = {
        "nodes": [
            {"id": "lib_loader", "type": r"dll\/SO/load", "properties": {"LibraryPath": ""}}
        ],
        "links": []
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    with pytest.raises(ValueError, match="must not be empty"):
        await engine.run(start_node_id="lib_loader", start_pin_name="Load")


@pytest.mark.asyncio
async def test_library_loading_invalid_path():
    blueprint = {
        "nodes": [
            {"id": "lib_loader", "type": r"dll\/SO/load", "properties": {"LibraryPath": "nonexistent_library.so"}}
        ],
        "links": []
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    with pytest.raises(ValueError, match="Could not load"):
        await engine.run(start_node_id="lib_loader", start_pin_name="Load")


@pytest.mark.asyncio
async def test_library_call_sqrt():
    blueprint = {
        "nodes": [
            {"id": "lib_loader", "type": r"dll\/SO/load", "properties": {"LibraryPath": lib_path}},
            {
                "id": "library_call",
                "type": r"dll\/SO/call",
                "properties": {
                    "FunctionName": "sqrt",
                    "ReturnType": "float64",
                    "library_args": [
                        {"name": "x", "c_type": "float64", "direction": "in"}
                    ],
                    "x": 16.0
                }
            },
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            # Connect library handle
            {"id": "l_lib", "type": "data", "source_node": "lib_loader", "source_pin": "Library", "target_node": "library_call", "target_pin": "Library"},
            # Connect execution path
            {"id": "l_exec1", "type": "exec", "source_node": "lib_loader", "source_pin": "Out", "target_node": "library_call", "target_pin": "Call"},
            {"id": "l_exec2", "type": "exec", "source_node": "library_call", "source_pin": "Out", "target_node": "print", "target_pin": "In"},
            # Connect result value
            {"id": "l_res", "type": "data", "source_node": "library_call", "source_pin": "ReturnValue", "target_node": "print", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    await engine.run(start_node_id="lib_loader", start_pin_name="Load")

    print_node = engine.nodes["print"]
    assert print_node.last_printed == 4.0


@pytest.mark.asyncio
async def test_library_call_modf_pointer():
    # double modf(double x, double* iptr)
    # returns fractional part of x, writes integral part to iptr.
    blueprint = {
        "nodes": [
            {"id": "lib_loader", "type": r"dll\/SO/load", "properties": {"LibraryPath": lib_path}},
            {
                "id": "library_call",
                "type": r"dll\/SO/call",
                "properties": {
                    "FunctionName": "modf",
                    "ReturnType": "float64",
                    "library_args": [
                        {"name": "x", "c_type": "float64", "direction": "in"},
                        {"name": "iptr", "c_type": "float64", "direction": "out_ptr"}
                    ],
                    "x": 3.14
                }
            },
            {"id": "print_frac", "type": "outputs/basic/print", "properties": {}},
            {"id": "print_int", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            {"id": "l_lib", "type": "data", "source_node": "lib_loader", "source_pin": "Library", "target_node": "library_call", "target_pin": "Library"},
            {"id": "l_exec1", "type": "exec", "source_node": "lib_loader", "source_pin": "Out", "target_node": "library_call", "target_pin": "Call"},
            
            # Print fractional part
            {"id": "l_exec2", "type": "exec", "source_node": "library_call", "source_pin": "Out", "target_node": "print_frac", "target_pin": "In"},
            {"id": "l_res1", "type": "data", "source_node": "library_call", "source_pin": "ReturnValue", "target_node": "print_frac", "target_pin": "Value"},
            
            # Print integral part
            {"id": "l_exec3", "type": "exec", "source_node": "print_frac", "source_pin": "Out", "target_node": "print_int", "target_pin": "In"},
            {"id": "l_res2", "type": "data", "source_node": "library_call", "source_pin": "iptr", "target_node": "print_int", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    await engine.run(start_node_id="lib_loader", start_pin_name="Load")

    print_frac = engine.nodes["print_frac"]
    print_int = engine.nodes["print_int"]

    # 3.14 -> fractional part ~ 0.14, integral part = 3.0
    assert abs(print_frac.last_printed - 0.14) < 1e-9
    assert print_int.last_printed == 3.0


@pytest.mark.asyncio
async def test_library_call_invalid_function():
    blueprint = {
        "nodes": [
            {"id": "lib_loader", "type": r"dll\/SO/load", "properties": {"LibraryPath": lib_path}},
            {
                "id": "library_call",
                "type": r"dll\/SO/call",
                "properties": {
                    "FunctionName": "nonexistent_function_abc123",
                    "ReturnType": "void"
                }
            }
        ],
        "links": [
            {"id": "l_lib", "type": "data", "source_node": "lib_loader", "source_pin": "Library", "target_node": "library_call", "target_pin": "Library"},
            {"id": "l_exec", "type": "exec", "source_node": "lib_loader", "source_pin": "Out", "target_node": "library_call", "target_pin": "Call"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    with pytest.raises(ValueError, match="was not found in the loaded library"):
        await engine.run(start_node_id="lib_loader", start_pin_name="Load")


@pytest.mark.asyncio
async def test_library_call_bounds_check():
    # Setup out_buffer with invalid size_arg <= 0
    blueprint = {
        "nodes": [
            {"id": "lib_loader", "type": r"dll\/SO/load", "properties": {"LibraryPath": lib_path}},
            {
                "id": "library_call",
                "type": r"dll\/SO/call",
                "properties": {
                    "FunctionName": "sqrt",
                    "ReturnType": "float64",
                    "library_args": [
                        {"name": "buf", "c_type": "float64", "direction": "out_buffer", "size_arg": "size"},
                        {"name": "size", "c_type": "int32", "direction": "in"}
                    ],
                    "size": -5
                }
            }
        ],
        "links": [
            {"id": "l_lib", "type": "data", "source_node": "lib_loader", "source_pin": "Library", "target_node": "library_call", "target_pin": "Library"},
            {"id": "l_exec", "type": "exec", "source_node": "lib_loader", "source_pin": "Out", "target_node": "library_call", "target_pin": "Call"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    with pytest.raises(ValueError, match="must be > 0"):
        await engine.run(start_node_id="lib_loader", start_pin_name="Load")


@pytest.mark.asyncio
async def test_library_call_out_buffer_memset():
    # void* memset(void* s, int c, size_t n)
    blueprint = {
        "nodes": [
            {"id": "lib_loader", "type": r"dll\/SO/load", "properties": {"LibraryPath": libc_path}},
            {
                "id": "library_call",
                "type": r"dll\/SO/call",
                "properties": {
                    "FunctionName": "memset",
                    "ReturnType": "void", # we discard return value
                    "library_args": [
                        {"name": "buf", "c_type": "uint8", "direction": "out_buffer", "size_arg": "size"},
                        {"name": "c", "c_type": "int32", "direction": "in"},
                        {"name": "size", "c_type": "uint64", "direction": "in"}
                    ],
                    "c": 123.0,
                    "size": 5.0
                }
            }
        ],
        "links": [
            {"id": "l_lib", "type": "data", "source_node": "lib_loader", "source_pin": "Library", "target_node": "library_call", "target_pin": "Library"},
            {"id": "l_exec", "type": "exec", "source_node": "lib_loader", "source_pin": "Out", "target_node": "library_call", "target_pin": "Call"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    await engine.run(start_node_id="lib_loader", start_pin_name="Load")

    call_node = engine.nodes["library_call"]
    assert call_node._outputs.get("buf") == [123, 123, 123, 123, 123]


@pytest.mark.asyncio
async def test_library_call_inout_buffer_memset():
    # void* memset(void* s, int c, size_t n)
    blueprint = {
        "nodes": [
            {"id": "lib_loader", "type": r"dll\/SO/load", "properties": {"LibraryPath": libc_path}},
            {
                "id": "library_call",
                "type": r"dll\/SO/call",
                "properties": {
                    "FunctionName": "memset",
                    "ReturnType": "void",
                    "library_args": [
                        {"name": "buf", "c_type": "uint8", "direction": "inout_buffer"},
                        {"name": "c", "c_type": "int32", "direction": "in"},
                        {"name": "size", "c_type": "uint64", "direction": "in"}
                    ],
                    "buf": [1.0, 2.0, 3.0, 4.0],
                    "c": 99.0,
                    "size": 4.0
                }
            }
        ],
        "links": [
            {"id": "l_lib", "type": "data", "source_node": "lib_loader", "source_pin": "Library", "target_node": "library_call", "target_pin": "Library"},
            {"id": "l_exec", "type": "exec", "source_node": "lib_loader", "source_pin": "Out", "target_node": "library_call", "target_pin": "Call"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)

    await engine.run(start_node_id="lib_loader", start_pin_name="Load")

    call_node = engine.nodes["library_call"]
    assert call_node._outputs.get("buf") == [99, 99, 99, 99]
