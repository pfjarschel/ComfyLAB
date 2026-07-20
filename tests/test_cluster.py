import pytest
from comfylab.engine.executor import ExecutionEngine
from comfylab.nodes.cluster import register_cluster_node
from comfylab.engine.models import ClusterDefinitionModel

@pytest.mark.asyncio
async def test_cluster_data_pull_execution():
    """
    Test that a cluster node with data inputs and data outputs correctly delegates
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
            "nodes": [
                {"id": "add_node", "type": "math/basic/add", "properties": {}}
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

    # Register the cluster node dynamic class in the engine registry
    cluster_def = ClusterDefinitionModel.model_validate(cluster_json)
    register_cluster_node(cluster_def)

    # Build a parent blueprint using the registered cluster node
    parent_blueprint = {
        "nodes": [
            {"id": "num1", "type": "constants/number", "properties": {"value": 15.0}},
            {"id": "num2", "type": "constants/number", "properties": {"value": 25.0}},
            {"id": "my_cluster_node", "type": "user/cluster/add_cluster", "properties": {}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            # parent num1.Value -> cluster.ext_A
            {"id": "l1", "type": "data", "source_node": "num1", "source_pin": "Value", "target_node": "my_cluster_node", "target_pin": "ext_A"},
            # parent num2.Value -> cluster.ext_B
            {"id": "l2", "type": "data", "source_node": "num2", "source_pin": "Value", "target_node": "my_cluster_node", "target_pin": "ext_B"},
            # cluster.ext_Result -> parent print.Value
            {"id": "l3", "type": "data", "source_node": "my_cluster_node", "source_pin": "ext_Result", "target_node": "print", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(parent_blueprint)

    # Run the execution starting on the print node
    await engine.run(start_node_id="print", start_pin_name="In")

    # Assert the lazy evaluation executed inside the cluster, pulling data from parent and printing 40.0
    print_node = engine.nodes["print"]
    assert print_node.last_printed == 40.0


@pytest.mark.asyncio
async def test_cluster_execution_flow():
    """
    Test that a cluster node with execution pins triggers its internal workflow
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
            "nodes": [
                {"id": "print_node", "type": "outputs/basic/print", "properties": {"value": "Hello from cluster"}}
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

    # Register the cluster print node dynamic class
    cluster_exec_def = ClusterDefinitionModel.model_validate(cluster_exec_json)
    register_cluster_node(cluster_exec_def)

    # Build parent blueprint using the cluster
    parent_blueprint = {
        "nodes": [
            {"id": "trigger_cluster", "type": "user/cluster/print_cluster", "properties": {}},
            {"id": "print_done", "type": "outputs/basic/print", "properties": {"value": "Cluster Executed"}}
        ],
        "links": [
            # parent trigger_cluster.ext_Out -> print_done.In
            {"id": "l1", "type": "exec", "source_node": "trigger_cluster", "source_pin": "ext_Out", "target_node": "print_done", "target_pin": "In"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(parent_blueprint)

    # Trigger cluster node
    await engine.run(start_node_id="trigger_cluster", start_pin_name="ext_In")

    # Assert that print_node inside cluster ran (printing "Hello from cluster")
    cluster_node = engine.nodes["trigger_cluster"]
    assert cluster_node._sub_engine is not None
    assert cluster_node._sub_engine.nodes["cluster_trigger_cluster_d0_print_node"].last_printed == "Hello from cluster"

    # Assert that downstream node ran (printing "Cluster Executed")
    assert engine.nodes["print_done"].last_printed == "Cluster Executed"


@pytest.mark.asyncio
async def test_cluster_boundary_nodes_data_evaluation():
    """
    Test that a cluster node using cluster/boundary/input and cluster/boundary/output boundary nodes
    correctly delegates pulling of data across the cluster boundary.
    """
    cluster_json = {
        "name": "Boundary Nodes Cluster",
        "type_name": "user/cluster/boundary_nodes_cluster",
        "category": "User/Clusters",
        "icon": "➕",
        "display_name": "Boundary Nodes Cluster",
        "description": "Adds two numbers using boundary nodes",
        "internal_blueprint": {
            "nodes": [
                {"id": "in_A", "type": "cluster/boundary/input", "properties": {"Name": "ext_A", "Type": "data", "DataType": "number"}},
                {"id": "in_B", "type": "cluster/boundary/input", "properties": {"Name": "ext_B", "Type": "data", "DataType": "number"}},
                {"id": "add_node", "type": "math/basic/add", "properties": {}},
                {"id": "out_res", "type": "cluster/boundary/output", "properties": {"Name": "ext_Result", "Type": "data"}}
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

    cluster_def = ClusterDefinitionModel.model_validate(cluster_json)
    register_cluster_node(cluster_def)

    parent_blueprint = {
        "nodes": [
            {"id": "num1", "type": "constants/number", "properties": {"value": 12.0}},
            {"id": "num2", "type": "constants/number", "properties": {"value": 18.0}},
            {"id": "my_cluster_node", "type": "user/cluster/boundary_nodes_cluster", "properties": {}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_node": "num1", "source_pin": "Value", "target_node": "my_cluster_node", "target_pin": "ext_A"},
            {"id": "l2", "type": "data", "source_node": "num2", "source_pin": "Value", "target_node": "my_cluster_node", "target_pin": "ext_B"},
            {"id": "l3", "type": "data", "source_node": "my_cluster_node", "source_pin": "ext_Result", "target_node": "print", "target_pin": "Value"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(parent_blueprint)

    await engine.run(start_node_id="print", start_pin_name="In")

    print_node = engine.nodes["print"]
    assert print_node.last_printed == 30.0


@pytest.mark.asyncio
async def test_cluster_boundary_nodes_exec_flow():
    """
    Test that execution and control flow flows correctly into cluster/boundary/input and
    bubbles out of cluster/boundary/output boundary nodes to propagate parent flow.
    """
    cluster_exec_json = {
        "name": "Boundary Exec Cluster",
        "type_name": "user/cluster/boundary_exec_cluster",
        "category": "User/Clusters",
        "icon": "📦",
        "display_name": "Boundary Exec Cluster",
        "description": "Prints using cluster boundary exec nodes",
        "internal_blueprint": {
            "nodes": [
                {"id": "in_exec", "type": "cluster/boundary/input", "properties": {"Name": "ext_In", "Type": "exec"}},
                {"id": "print_node", "type": "outputs/basic/print", "properties": {"value": "Hello from boundary cluster"}},
                {"id": "out_exec", "type": "cluster/boundary/output", "properties": {"Name": "ext_Out", "Type": "exec"}}
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

    cluster_exec_def = ClusterDefinitionModel.model_validate(cluster_exec_json)
    register_cluster_node(cluster_exec_def)

    parent_blueprint = {
        "nodes": [
            {"id": "trigger_cluster", "type": "user/cluster/boundary_exec_cluster", "properties": {}},
            {"id": "print_done", "type": "outputs/basic/print", "properties": {"value": "Cluster Executed"}}
        ],
        "links": [
            {"id": "l1", "type": "exec", "source_node": "trigger_cluster", "source_pin": "ext_Out", "target_node": "print_done", "target_pin": "In"}
        ]
    }

    engine = ExecutionEngine()
    engine.load_blueprint(parent_blueprint)

    await engine.run(start_node_id="trigger_cluster", start_pin_name="ext_In")

    cluster_node = engine.nodes["trigger_cluster"]
    assert cluster_node._sub_engine is not None
    assert cluster_node._sub_engine.nodes["cluster_trigger_cluster_d0_print_node"].last_printed == "Hello from boundary cluster"
    assert engine.nodes["print_done"].last_printed == "Cluster Executed"

