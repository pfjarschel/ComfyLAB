import pytest
from comfylab.engine.executor import ExecutionEngine
from comfylab.nodes.macro import register_macro_node
from comfylab.engine.models import MacroDefinitionModel

@pytest.mark.asyncio
async def test_macro_data_pull_execution():
    """
    Test that a macro node with data inputs and data outputs correctly delegates
    lazy pulls across boundaries and computes the correct result.
    """
    macro_json = {
        "name": "Add Macro",
        "type_name": "user/macro/add_macro",
        "category": "User/Macros",
        "icon": "➕",
        "display_name": "Add Macro",
        "description": "Adds two numbers via nested engine",
        "internal_blueprint": {
            "nodes": [
                {"id": "add_node", "type": "math/arithmetic/add", "properties": {}}
            ],
            "links": []
        },
        "boundary_pins": {
            "exec_ins": [],
            "exec_outs": [],
            "data_ins": [
                {"name": "ext_A", "type": "number", "default": 0.0, "maps_to": {"node_id": "add_node", "pin": "A"}},
                {"name": "ext_B", "type": "number", "default": 0.0, "maps_to": {"node_id": "add_node", "pin": "B"}}
            ],
            "data_outs": [
                {"name": "ext_Result", "type": "number", "maps_from": {"node_id": "add_node", "pin": "Result"}}
            ]
        }
    }

    # Register the macro node dynamic class in the engine registry
    macro_def = MacroDefinitionModel.model_validate(macro_json)
    register_macro_node(macro_def)

    # Build a parent blueprint using the registered macro node
    parent_blueprint = {
        "nodes": [
            {"id": "num1", "type": "constants/number", "properties": {"value": 15.0}},
            {"id": "num2", "type": "constants/number", "properties": {"value": 25.0}},
            {"id": "my_macro_node", "type": "user/macro/add_macro", "properties": {}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            # parent num1.Value -> macro.ext_A
            {"id": "l1", "type": "data", "source_node": "num1", "source_pin": "Value", "target_node": "my_macro_node", "target_pin": "ext_A"},
            # parent num2.Value -> macro.ext_B
            {"id": "l2", "type": "data", "source_node": "num2", "source_pin": "Value", "target_node": "my_macro_node", "target_pin": "ext_B"},
            # macro.ext_Result -> parent print.Value
            {"id": "l3", "type": "data", "source_node": "my_macro_node", "source_pin": "ext_Result", "target_node": "print", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(parent_blueprint)

    # Run the execution starting on the print node
    await engine.run(start_node_id="print", start_pin_name="In")

    # Assert the lazy evaluation executed inside the macro, pulling data from parent and printing 40.0
    print_node = engine.nodes["print"]
    assert print_node.last_printed == 40.0


@pytest.mark.asyncio
async def test_macro_execution_flow():
    """
    Test that a macro node with execution pins triggers its internal workflow
    and continues downstream parent execution.
    """
    macro_exec_json = {
        "name": "Print Macro",
        "type_name": "user/macro/print_macro",
        "category": "User/Macros",
        "icon": "📦",
        "display_name": "Print Macro",
        "description": "Prints a message from execution flow",
        "internal_blueprint": {
            "nodes": [
                {"id": "print_node", "type": "outputs/basic/print", "properties": {"value": "Hello from macro"}}
            ],
            "links": []
        },
        "boundary_pins": {
            "exec_ins": [
                {"name": "ext_In", "maps_to": {"node_id": "print_node", "pin": "In"}}
            ],
            "exec_outs": [
                {"name": "ext_Out", "maps_from": {"node_id": "print_node", "pin": "Out"}}
            ],
            "data_ins": [],
            "data_outs": []
        }
    }

    # Register the macro print node dynamic class
    macro_exec_def = MacroDefinitionModel.model_validate(macro_exec_json)
    register_macro_node(macro_exec_def)

    # Build parent blueprint using the macro
    parent_blueprint = {
        "nodes": [
            {"id": "trigger_macro", "type": "user/macro/print_macro", "properties": {}},
            {"id": "print_done", "type": "outputs/basic/print", "properties": {"value": "Macro Executed"}}
        ],
        "links": [
            # parent trigger_macro.ext_Out -> print_done.In
            {"id": "l1", "type": "exec", "source_node": "trigger_macro", "source_pin": "ext_Out", "target_node": "print_done", "target_pin": "In"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(parent_blueprint)

    # Trigger macro node
    await engine.run(start_node_id="trigger_macro", start_pin_name="ext_In")

    # Assert that print_node inside macro ran (printing "Hello from macro")
    macro_node = engine.nodes["trigger_macro"]
    assert macro_node._sub_engine is not None
    assert macro_node._sub_engine.nodes["macro_trigger_macro_d0_print_node"].last_printed == "Hello from macro"

    # Assert that downstream node ran (printing "Macro Executed")
    assert engine.nodes["print_done"].last_printed == "Macro Executed"


@pytest.mark.asyncio
async def test_macro_boundary_nodes_data_evaluation():
    """
    Test that a macro node using macro/boundary/input and macro/boundary/output boundary nodes
    correctly delegates pulling of data across the macro boundary.
    """
    macro_json = {
        "name": "Boundary Nodes Macro",
        "type_name": "user/macro/boundary_nodes_macro",
        "category": "User/Macros",
        "icon": "➕",
        "display_name": "Boundary Nodes Macro",
        "description": "Adds two numbers using boundary nodes",
        "internal_blueprint": {
            "nodes": [
                {"id": "in_A", "type": "macro/boundary/input", "properties": {"Name": "ext_A", "Type": "data", "DataType": "number"}},
                {"id": "in_B", "type": "macro/boundary/input", "properties": {"Name": "ext_B", "Type": "data", "DataType": "number"}},
                {"id": "add_node", "type": "math/arithmetic/add", "properties": {}},
                {"id": "out_res", "type": "macro/boundary/output", "properties": {"Name": "ext_Result", "Type": "data"}}
            ],
            "links": [
                {"id": "l_in_a", "type": "data", "source_node": "in_A", "source_pin": "Value", "target_node": "add_node", "target_pin": "A"},
                {"id": "l_in_b", "type": "data", "source_node": "in_B", "source_pin": "Value", "target_node": "add_node", "target_pin": "B"},
                {"id": "l_out", "type": "data", "source_node": "add_node", "source_pin": "Result", "target_node": "out_res", "target_pin": "Value"}
            ]
        },
        "boundary_pins": {
            "exec_ins": [],
            "exec_outs": [],
            "data_ins": [
                {"name": "ext_A", "type": "number", "default": 0.0, "maps_to": {"node_id": "in_A", "pin": "Value"}},
                {"name": "ext_B", "type": "number", "default": 0.0, "maps_to": {"node_id": "in_B", "pin": "Value"}}
            ],
            "data_outs": [
                {"name": "ext_Result", "type": "number", "maps_from": {"node_id": "out_res", "pin": "Value"}}
            ]
        }
    }

    macro_def = MacroDefinitionModel.model_validate(macro_json)
    register_macro_node(macro_def)

    parent_blueprint = {
        "nodes": [
            {"id": "num1", "type": "constants/number", "properties": {"value": 12.0}},
            {"id": "num2", "type": "constants/number", "properties": {"value": 18.0}},
            {"id": "my_macro_node", "type": "user/macro/boundary_nodes_macro", "properties": {}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_node": "num1", "source_pin": "Value", "target_node": "my_macro_node", "target_pin": "ext_A"},
            {"id": "l2", "type": "data", "source_node": "num2", "source_pin": "Value", "target_node": "my_macro_node", "target_pin": "ext_B"},
            {"id": "l3", "type": "data", "source_node": "my_macro_node", "source_pin": "ext_Result", "target_node": "print", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(parent_blueprint)

    await engine.run(start_node_id="print", start_pin_name="In")

    print_node = engine.nodes["print"]
    assert print_node.last_printed == 30.0


@pytest.mark.asyncio
async def test_macro_boundary_nodes_exec_flow():
    """
    Test that execution and control flow flows correctly into macro/boundary/input and
    bubbles out of macro/boundary/output boundary nodes to propagate parent flow.
    """
    macro_exec_json = {
        "name": "Boundary Exec Macro",
        "type_name": "user/macro/boundary_exec_macro",
        "category": "User/Macros",
        "icon": "📦",
        "display_name": "Boundary Exec Macro",
        "description": "Prints using macro boundary exec nodes",
        "internal_blueprint": {
            "nodes": [
                {"id": "in_exec", "type": "macro/boundary/input", "properties": {"Name": "ext_In", "Type": "exec"}},
                {"id": "print_node", "type": "outputs/basic/print", "properties": {"value": "Hello from boundary macro"}},
                {"id": "out_exec", "type": "macro/boundary/output", "properties": {"Name": "ext_Out", "Type": "exec"}}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_node": "in_exec", "source_pin": "Out", "target_node": "print_node", "target_pin": "In"},
                {"id": "l2", "type": "exec", "source_node": "print_node", "source_pin": "Out", "target_node": "out_exec", "target_pin": "In"}
            ]
        },
        "boundary_pins": {
            "exec_ins": [
                {"name": "ext_In", "maps_to": {"node_id": "in_exec", "pin": "Out"}}
            ],
            "exec_outs": [
                {"name": "ext_Out", "maps_from": {"node_id": "out_exec", "pin": "In"}}
            ],
            "data_ins": [],
            "data_outs": []
        }
    }

    macro_exec_def = MacroDefinitionModel.model_validate(macro_exec_json)
    register_macro_node(macro_exec_def)

    parent_blueprint = {
        "nodes": [
            {"id": "trigger_macro", "type": "user/macro/boundary_exec_macro", "properties": {}},
            {"id": "print_done", "type": "outputs/basic/print", "properties": {"value": "Macro Executed"}}
        ],
        "links": [
            {"id": "l1", "type": "exec", "source_node": "trigger_macro", "source_pin": "ext_Out", "target_node": "print_done", "target_pin": "In"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(parent_blueprint)

    await engine.run(start_node_id="trigger_macro", start_pin_name="ext_In")

    macro_node = engine.nodes["trigger_macro"]
    assert macro_node._sub_engine is not None
    assert macro_node._sub_engine.nodes["macro_trigger_macro_d0_print_node"].last_printed == "Hello from boundary macro"
    assert engine.nodes["print_done"].last_printed == "Macro Executed"

