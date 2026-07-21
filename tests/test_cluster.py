import pytest
from comfylab.engine.executor import ExecutionEngine
from comfylab.blocks.cluster import register_cluster_block
from comfylab.engine.models import ClusterDefinitionModel

@pytest.mark.asyncio
async def test_cluster_data_pull_execution():
    """
    Test that a cluster block with data inputs and data outputs correctly delegates
    lazy pulls across boundaries and computes the correct result.
    """
    cluster_json = {
        "name": "Add Cluster",
        "type_name": "user/cluster/add_cluster",
        "category": "User/Clusters",
        "icon": "➕",
        "display_name": "Add Cluster",
        "description": "Adds two numbers via nested engine",
        "internal_blueprint": {
            "blocks": [
                {"id": "add_block", "type": "math/basic/add", "properties": {}}
            ],
            "links": []
        },
        "boundary_pins": {
            "exec_ins": [],
            "exec_outs": [],
            "data_ins": [
                {"name": "ext_A", "type": "number", "default": 0.0, "maps_to": {"block_id": "add_block", "pin": "A"}},
                {"name": "ext_B", "type": "number", "default": 0.0, "maps_to": {"block_id": "add_block", "pin": "B"}}
            ],
            "data_outs": [
                {"name": "ext_Result", "type": "number", "maps_from": {"block_id": "add_block", "pin": "Result"}}
            ]
        }
    }

    # Register the cluster block dynamic class in the engine registry
    cluster_def = ClusterDefinitionModel.model_validate(cluster_json)
    register_cluster_block(cluster_def)

    # Build a parent blueprint using the registered cluster block
    parent_blueprint = {
        "blocks": [
            {"id": "num1", "type": "constants/number", "properties": {"value": 15.0}},
            {"id": "num2", "type": "constants/number", "properties": {"value": 25.0}},
            {"id": "my_cluster_block", "type": "user/cluster/add_cluster", "properties": {}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            # parent num1.Value -> cluster.ext_A
            {"id": "l1", "type": "data", "source_block": "num1", "source_pin": "Value", "target_block": "my_cluster_block", "target_pin": "ext_A"},
            # parent num2.Value -> cluster.ext_B
            {"id": "l2", "type": "data", "source_block": "num2", "source_pin": "Value", "target_block": "my_cluster_block", "target_pin": "ext_B"},
            # cluster.ext_Result -> parent print.Value
            {"id": "l3", "type": "data", "source_block": "my_cluster_block", "source_pin": "ext_Result", "target_block": "print", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(parent_blueprint)

    # Run the execution starting on the print block
    await engine.run(start_block_id="print", start_pin_name="In")

    # Assert the lazy evaluation executed inside the cluster, pulling data from parent and printing 40.0
    print_block = engine.blocks["print"]
    assert print_block.last_printed == 40.0


@pytest.mark.asyncio
async def test_cluster_execution_flow():
    """
    Test that a cluster block with execution pins triggers its internal workflow
    and continues downstream parent execution.
    """
    cluster_exec_json = {
        "name": "Print Cluster",
        "type_name": "user/cluster/print_cluster",
        "category": "User/Clusters",
        "icon": "📦",
        "display_name": "Print Cluster",
        "description": "Prints a message from execution flow",
        "internal_blueprint": {
            "blocks": [
                {"id": "print_block", "type": "outputs/basic/print", "properties": {"value": "Hello from cluster"}}
            ],
            "links": []
        },
        "boundary_pins": {
            "exec_ins": [
                {"name": "ext_In", "maps_to": {"block_id": "print_block", "pin": "In"}}
            ],
            "exec_outs": [
                {"name": "ext_Out", "maps_from": {"block_id": "print_block", "pin": "Out"}}
            ],
            "data_ins": [],
            "data_outs": []
        }
    }

    # Register the cluster print block dynamic class
    cluster_exec_def = ClusterDefinitionModel.model_validate(cluster_exec_json)
    register_cluster_block(cluster_exec_def)

    # Build parent blueprint using the cluster
    parent_blueprint = {
        "blocks": [
            {"id": "trigger_cluster", "type": "user/cluster/print_cluster", "properties": {}},
            {"id": "print_done", "type": "outputs/basic/print", "properties": {"value": "Cluster Executed"}}
        ],
        "links": [
            # parent trigger_cluster.ext_Out -> print_done.In
            {"id": "l1", "type": "exec", "source_block": "trigger_cluster", "source_pin": "ext_Out", "target_block": "print_done", "target_pin": "In"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(parent_blueprint)

    # Trigger cluster block
    await engine.run(start_block_id="trigger_cluster", start_pin_name="ext_In")

    # Assert that print_block inside cluster ran (printing "Hello from cluster")
    cluster_block = engine.blocks["trigger_cluster"]
    assert cluster_block._sub_engine is not None
    assert cluster_block._sub_engine.blocks["cluster_trigger_cluster_d0_print_block"].last_printed == "Hello from cluster"

    # Assert that downstream block ran (printing "Cluster Executed")
    assert engine.blocks["print_done"].last_printed == "Cluster Executed"


@pytest.mark.asyncio
async def test_cluster_boundary_blocks_data_evaluation():
    """
    Test that a cluster block using cluster/boundary/input and cluster/boundary/output boundary blocks
    correctly delegates pulling of data across the cluster boundary.
    """
    cluster_json = {
        "name": "Boundary Blocks Cluster",
        "type_name": "user/cluster/boundary_blocks_cluster",
        "category": "User/Clusters",
        "icon": "➕",
        "display_name": "Boundary Blocks Cluster",
        "description": "Adds two numbers using boundary blocks",
        "internal_blueprint": {
            "blocks": [
                {"id": "in_A", "type": "cluster/boundary/input", "properties": {"Name": "ext_A", "Type": "data", "DataType": "number"}},
                {"id": "in_B", "type": "cluster/boundary/input", "properties": {"Name": "ext_B", "Type": "data", "DataType": "number"}},
                {"id": "add_block", "type": "math/basic/add", "properties": {}},
                {"id": "out_res", "type": "cluster/boundary/output", "properties": {"Name": "ext_Result", "Type": "data"}}
            ],
            "links": [
                {"id": "l_in_a", "type": "data", "source_block": "in_A", "source_pin": "Value", "target_block": "add_block", "target_pin": "A"},
                {"id": "l_in_b", "type": "data", "source_block": "in_B", "source_pin": "Value", "target_block": "add_block", "target_pin": "B"},
                {"id": "l_out", "type": "data", "source_block": "add_block", "source_pin": "Result", "target_block": "out_res", "target_pin": "Value"}
            ]
        },
        "boundary_pins": {
            "exec_ins": [],
            "exec_outs": [],
            "data_ins": [
                {"name": "ext_A", "type": "number", "default": 0.0, "maps_to": {"block_id": "in_A", "pin": "Value"}},
                {"name": "ext_B", "type": "number", "default": 0.0, "maps_to": {"block_id": "in_B", "pin": "Value"}}
            ],
            "data_outs": [
                {"name": "ext_Result", "type": "number", "maps_from": {"block_id": "out_res", "pin": "Value"}}
            ]
        }
    }

    cluster_def = ClusterDefinitionModel.model_validate(cluster_json)
    register_cluster_block(cluster_def)

    parent_blueprint = {
        "blocks": [
            {"id": "num1", "type": "constants/number", "properties": {"value": 12.0}},
            {"id": "num2", "type": "constants/number", "properties": {"value": 18.0}},
            {"id": "my_cluster_block", "type": "user/cluster/boundary_blocks_cluster", "properties": {}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_block": "num1", "source_pin": "Value", "target_block": "my_cluster_block", "target_pin": "ext_A"},
            {"id": "l2", "type": "data", "source_block": "num2", "source_pin": "Value", "target_block": "my_cluster_block", "target_pin": "ext_B"},
            {"id": "l3", "type": "data", "source_block": "my_cluster_block", "source_pin": "ext_Result", "target_block": "print", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(parent_blueprint)

    await engine.run(start_block_id="print", start_pin_name="In")

    print_block = engine.blocks["print"]
    assert print_block.last_printed == 30.0


@pytest.mark.asyncio
async def test_cluster_boundary_blocks_exec_flow():
    """
    Test that execution and control flow flows correctly into cluster/boundary/input and
    bubbles out of cluster/boundary/output boundary blocks to propagate parent flow.
    """
    cluster_exec_json = {
        "name": "Boundary Exec Cluster",
        "type_name": "user/cluster/boundary_exec_cluster",
        "category": "User/Clusters",
        "icon": "📦",
        "display_name": "Boundary Exec Cluster",
        "description": "Prints using cluster boundary exec blocks",
        "internal_blueprint": {
            "blocks": [
                {"id": "in_exec", "type": "cluster/boundary/input", "properties": {"Name": "ext_In", "Type": "exec"}},
                {"id": "print_block", "type": "outputs/basic/print", "properties": {"value": "Hello from boundary cluster"}},
                {"id": "out_exec", "type": "cluster/boundary/output", "properties": {"Name": "ext_Out", "Type": "exec"}}
            ],
            "links": [
                {"id": "l1", "type": "exec", "source_block": "in_exec", "source_pin": "Out", "target_block": "print_block", "target_pin": "In"},
                {"id": "l2", "type": "exec", "source_block": "print_block", "source_pin": "Out", "target_block": "out_exec", "target_pin": "In"}
            ]
        },
        "boundary_pins": {
            "exec_ins": [
                {"name": "ext_In", "maps_to": {"block_id": "in_exec", "pin": "Out"}}
            ],
            "exec_outs": [
                {"name": "ext_Out", "maps_from": {"block_id": "out_exec", "pin": "In"}}
            ],
            "data_ins": [],
            "data_outs": []
        }
    }

    cluster_exec_def = ClusterDefinitionModel.model_validate(cluster_exec_json)
    register_cluster_block(cluster_exec_def)

    parent_blueprint = {
        "blocks": [
            {"id": "trigger_cluster", "type": "user/cluster/boundary_exec_cluster", "properties": {}},
            {"id": "print_done", "type": "outputs/basic/print", "properties": {"value": "Cluster Executed"}}
        ],
        "links": [
            {"id": "l1", "type": "exec", "source_block": "trigger_cluster", "source_pin": "ext_Out", "target_block": "print_done", "target_pin": "In"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(parent_blueprint)

    await engine.run(start_block_id="trigger_cluster", start_pin_name="ext_In")

    cluster_block = engine.blocks["trigger_cluster"]
    assert cluster_block._sub_engine is not None
    assert cluster_block._sub_engine.blocks["cluster_trigger_cluster_d0_print_block"].last_printed == "Hello from boundary cluster"
    assert engine.blocks["print_done"].last_printed == "Cluster Executed"

