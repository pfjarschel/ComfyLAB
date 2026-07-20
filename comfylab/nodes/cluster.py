# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from comfylab.engine.registry import register_node, NODE_REGISTRY
from comfylab.nodes.base import BaseNode, ExecIn, ExecOut, DataIn, DataOut, ExecutionContext, Pin
from comfylab.engine.models import ClusterDefinitionModel, BoundaryPinsModel
from comfylab.engine.locks import ResourceLockManager

MAX_CLUSTER_DEPTH = 10


class ClusterExecutionContext(ExecutionContext):
    """
    Execution context for nodes running inside a cluster sub-graph.
    Delegates boundary pulls to the parent context and sub-engine pulls internally.
    """
    def __init__(self, parent_context: ExecutionContext, sub_engine: Any,
                 boundary_data_in_map: Dict[str, tuple], boundary_data_out_map: Dict[str, tuple],
                 cluster_node_id: str):
        self.parent_context = parent_context
        self.sub_engine = sub_engine
        self.boundary_data_in_map = boundary_data_in_map
        self.boundary_data_out_map = boundary_data_out_map
        self._cluster_node_id = cluster_node_id
        self.lock_manager = parent_context.lock_manager
        self.engine = sub_engine
        self.run_id = parent_context.run_id
        self._data_cache: Dict[str, Dict[str, Any]] = {}
        self._triggered_exec_out = None

    async def pull(self, node_id: str, input_pin_name: str) -> Any:
        key = (node_id, input_pin_name)
        if key in self.boundary_data_in_map:
            external_pin_name = self.boundary_data_in_map[key]
            return await self.parent_context.pull(self._cluster_node_id, external_pin_name)
        return await self.sub_engine.pull_data(node_id, input_pin_name, self)

    def cache_value(self, node_id: str, pin_name: str, value: Any):
        if node_id not in self._data_cache:
            self._data_cache[node_id] = {}
        self._data_cache[node_id][pin_name] = value

    def get_cached(self, node_id: str, pin_name: str) -> tuple:
        if node_id in self._data_cache and pin_name in self._data_cache[node_id]:
            return True, self._data_cache[node_id][pin_name]
        return False, None

    def clear_cache(self):
        self._data_cache.clear()

    async def send_telemetry(self, node_id: str, data: Any):
        prefixed_id = f"{self._cluster_node_id}/{node_id}"
        if hasattr(self.parent_context, "send_telemetry"):
            await self.parent_context.send_telemetry(prefixed_id, data)


def _prefix_node_ids(blueprint: Dict[str, Any], prefix: str) -> Dict[str, Any]:
    nodes = []
    id_map = {}
    for node in blueprint.get("nodes", []):
        new_id = f"{prefix}_{node['id']}"
        id_map[node["id"]] = new_id
        new_node = dict(node)
        new_node["id"] = new_id
        nodes.append(new_node)

    links = []
    for link in blueprint.get("links", []):
        new_link = dict(link)
        new_link["source_node"] = id_map.get(link["source_node"], link["source_node"])
        new_link["target_node"] = id_map.get(link["target_node"], link["target_node"])
        links.append(new_link)

    return {"nodes": nodes, "links": links}


def parse_cluster_boundary_pins(internal_blueprint: Dict[str, Any], default_boundary_pins: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scans the internal blueprint of a cluster for boundary input/output nodes
    and constructs the boundary pin mapping dict. If none are found, returns the default.
    """
    has_boundary_nodes = any(
        node.get("type") in ("cluster/boundary/input", "cluster/boundary/output")
        for node in internal_blueprint.get("nodes", [])
    )
    if not has_boundary_nodes:
        return default_boundary_pins

    exec_ins = []
    exec_outs = []
    data_ins = []
    data_outs = []
    
    for node in internal_blueprint.get("nodes", []):
        node_id = node.get("id")
        node_type = node.get("type")
        props = node.get("properties", {})
        
        def get_prop(name, default):
            val = props.get(name, default)
            if isinstance(val, dict) and "value" in val:
                return val["value"]
            return val
        
        if node_type == "cluster/boundary/input":
            name = get_prop("Name", "InputPin")
            pin_type = get_prop("Type", "data")
            data_type = get_prop("DataType", "any")
            if pin_type == "exec":
                exec_ins.append({
                    "name": name,
                    "maps_to": {
                        "node_id": node_id,
                        "pin": "Out"
                    }
                })
            else:
                data_ins.append({
                    "name": name,
                    "type": data_type,
                    "default": None,
                    "widget": None,
                    "optional": False,
                    "maps_to": {
                        "node_id": node_id,
                        "pin": "Value"
                    }
                })
        elif node_type == "cluster/boundary/output":
            name = get_prop("Name", "OutputPin")
            pin_type = get_prop("Type", "data")
            if pin_type == "exec":
                exec_outs.append({
                    "name": name,
                    "maps_from": {
                        "node_id": node_id,
                        "pin": "In"
                    }
                })
            else:
                data_outs.append({
                    "name": name,
                    "type": "any",
                    "maps_from": {
                        "node_id": node_id,
                        "pin": "Value"
                    }
                })
                
    return {
        "exec_ins": exec_ins,
        "exec_outs": exec_outs,
        "data_ins": data_ins,
        "data_outs": data_outs
    }


def register_cluster_node(cluster_def: ClusterDefinitionModel, file_path: str = ""):
    type_name = cluster_def.type_name
    boundary = cluster_def.boundary_pins
    internal_blueprint = cluster_def.internal_blueprint.model_dump()

    inputs_def: List[Pin] = []
    outputs_def: List[Pin] = []

    for ein in boundary.exec_ins:
        inputs_def.append(ExecIn(ein.name))
    for eout in boundary.exec_outs:
        outputs_def.append(ExecOut(eout.name))

    type_map = {"number": float, "boolean": bool, "text": str, "string": str, "list": list, "any": None}
    for din in boundary.data_ins:
        hint = type_map.get(din.type)
        inputs_def.append(DataIn(
            din.name, type_hint=hint, default=din.default,
            widget=din.widget, min_val=din.min_val, max_val=din.max_val,
            step=din.step, options=din.options, optional=din.optional
        ))
    for dout in boundary.data_outs:
        hint = type_map.get(dout.type)
        outputs_def.append(DataOut(dout.name, type_hint=hint))

    class DynamicClusterNode(BaseNode):
        category = cluster_def.category
        icon = cluster_def.icon
        display_name = cluster_def.display_name
        description = cluster_def.description
        _cluster_file_path = file_path

        def __init__(self, node_id: str, properties: Optional[Dict[str, Any]] = None):
            super().__init__(node_id, properties)
            self._cluster_def = cluster_def
            self._sub_engine = None
            self._computed_outputs: Dict[str, Any] = {}
            self._depth = self.properties.get("_cluster_depth", 0)
            self.inputs = {pin.name: pin for pin in self.__class__.inputs_def}
            self.outputs = {pin.name: pin for pin in self.__class__.outputs_def}

        def _build_boundary_maps(self):
            bdi_map: Dict[tuple, str] = {}
            for din in boundary.data_ins:
                bdi_map[(din.maps_to.node_id, din.maps_to.pin)] = din.name
            bdo_map: Dict[str, tuple] = {}
            for dout in boundary.data_outs:
                bdo_map[dout.name] = (dout.maps_from.node_id, dout.maps_from.pin)
            return bdi_map, bdo_map

        def _get_entry_point(self):
            if boundary.exec_ins:
                ein = boundary.exec_ins[0]
                return ein.maps_to.node_id, ein.maps_to.pin
            return None, None

        async def execute(self, context: ExecutionContext, trigger_pin: str) -> Optional[str]:
            if self._depth > MAX_CLUSTER_DEPTH:
                raise RuntimeError(f"Cluster nesting depth exceeded ({self._depth} > {MAX_CLUSTER_DEPTH})")

            self._ensure_sub_engine()
            sub_engine = self._sub_engine
            prefix = f"cluster_{self.id}_d{self._depth}"

            bdi_map, bdo_map = self._build_boundary_maps()
            prefixed_bdi_map = {}
            for (node_id, pin), ext_name in bdi_map.items():
                prefixed_bdi_map[(f"{prefix}_{node_id}", pin)] = ext_name

            cluster_ctx = ClusterExecutionContext(
                context, sub_engine, prefixed_bdi_map, bdo_map, self.id
            )

            # Support triggering the specific entry point matching trigger_pin
            start_node_id, start_pin_name = None, None
            for ein in boundary.exec_ins:
                if ein.name == trigger_pin:
                    start_node_id = ein.maps_to.node_id
                    start_pin_name = ein.maps_to.pin
                    break
            
            # Fallback to the first exec_in if trigger_pin is not found but exec_ins exist
            if not start_node_id and boundary.exec_ins:
                start_node_id = boundary.exec_ins[0].maps_to.node_id
                start_pin_name = boundary.exec_ins[0].maps_to.pin

            if start_node_id:
                start_node_id = f"{prefix}_{start_node_id}"

            sub_engine.telemetry_callback = context.engine.telemetry_callback

            # Run the sub-engine manually using our ClusterExecutionContext (not its own plain context)
            run_error = None
            try:
                sub_engine.state = "RUNNING"
                sub_engine.executed_nodes_order.clear()

                import os as _os
                original_cwd = _os.getcwd()
                try:
                    if start_node_id and start_pin_name:
                        task = asyncio.create_task(sub_engine.trigger_exec(start_node_id, start_pin_name, cluster_ctx))
                        sub_engine._active_tasks.add(task)
                        task.add_done_callback(sub_engine._active_tasks.discard)
                        await task
                    else:
                        entry_points = sub_engine._find_entry_points()
                        if entry_points:
                            tasks = []
                            for nid, pname in entry_points:
                                task = asyncio.create_task(sub_engine.trigger_exec(nid, pname, cluster_ctx))
                                sub_engine._active_tasks.add(task)
                                task.add_done_callback(sub_engine._active_tasks.discard)
                                tasks.append(task)
                            await asyncio.gather(*tasks)

                    if sub_engine.state == "RUNNING":
                        sub_engine.state = "IDLE"
                except asyncio.CancelledError:
                    sub_engine.state = "ABORTED"
                except Exception as e:
                    sub_engine.state = "ABORTED"
                    run_error = e
                finally:
                    if sub_engine._active_tasks:
                        for task in list(sub_engine._active_tasks):
                            if not task.done():
                                task.cancel()
                        await asyncio.gather(*sub_engine._active_tasks, return_exceptions=True)
                        sub_engine._active_tasks.clear()
                    _os.chdir(original_cwd)

                # Collect boundary outputs — sub_engine stays alive, no teardown here
                self._computed_outputs = {}
                for dout in boundary.data_outs:
                    mapped_node_id = f"{prefix}_{dout.maps_from.node_id}"
                    mapped_pin = dout.maps_from.pin
                    node = sub_engine.nodes.get(mapped_node_id)
                    if node:
                        val = await node.pull_data(cluster_ctx, mapped_pin)
                        self._computed_outputs[dout.name] = val

                if run_error and context.engine.state != "ABORTED":
                    raise run_error
            finally:
                pass  # Do NOT teardown — sub_engine lives until ClusterNode.teardown() is called

            triggered_out = getattr(cluster_ctx, "_triggered_exec_out", None)
            if triggered_out is not None:
                return triggered_out
            if boundary.exec_outs:
                return boundary.exec_outs[0].name
            return None

        async def pull_data(self, context: ExecutionContext, pin_name: str) -> Any:
            if pin_name in self._computed_outputs:
                return self._computed_outputs[pin_name]

            for dout in boundary.data_outs:
                if dout.name == pin_name:
                    self._ensure_sub_engine()
                    prefix = f"cluster_{self.id}_d{self._depth}"
                    mapped_node_id = f"{prefix}_{dout.maps_from.node_id}"
                    mapped_pin = dout.maps_from.pin

                    bdi_map, bdo_map = self._build_boundary_maps()
                    prefixed_bdi_map = {}
                    for (nid, p), ext_name in bdi_map.items():
                        prefixed_bdi_map[(f"{prefix}_{nid}", p)] = ext_name

                    cluster_ctx = ClusterExecutionContext(
                        context, self._sub_engine, prefixed_bdi_map, bdo_map, self.id
                    )

                    node = self._sub_engine.nodes.get(mapped_node_id)
                    if node:
                        val = await node.pull_data(cluster_ctx, mapped_pin)
                        self._computed_outputs[pin_name] = val
                        return val
                    return None

            return None

        def _ensure_sub_engine(self):
            if self._sub_engine is not None:
                return
            from comfylab.engine.executor import ExecutionEngine
            sub_engine = ExecutionEngine()
            prefix = f"cluster_{self.id}_d{self._depth}"
            prefixed_blueprint = _prefix_node_ids(internal_blueprint, prefix)
            sub_engine.load_blueprint(prefixed_blueprint)
            self._sub_engine = sub_engine

        async def teardown(self):
            if self._sub_engine:
                try:
                    await self._sub_engine._teardown_all()
                except Exception:
                    pass
            await super().teardown()

    DynamicClusterNode.inputs_def = inputs_def
    DynamicClusterNode.outputs_def = outputs_def
    DynamicClusterNode.__name__ = type_name.replace("/", "_").replace("-", "_")
    DynamicClusterNode.__qualname__ = DynamicClusterNode.__name__

    _CLUSTER_TYPE_PREFIXES = ("user/cluster/", "workspace/cluster/")
    _BOUNDARY_TYPES = ("cluster/input", "cluster/output", "cluster/boundary/input", "cluster/boundary/output")
    missing_regular = []
    for bn in internal_blueprint.get("nodes", []):
        nt = bn.get("type")
        if not nt:
            continue
        if nt in NODE_REGISTRY:
            continue
        if nt.startswith(_CLUSTER_TYPE_PREFIXES) or nt in _BOUNDARY_TYPES:
            continue
        missing_regular.append(nt)

    import logging
    _cluster_logger = logging.getLogger("comfylab.nodes.cluster")

    if missing_regular:
        DynamicClusterNode.broken = True
        DynamicClusterNode.broken_reason = (
            "Cluster references unregistered node types: " + ", ".join(sorted(set(missing_regular)))
        )
        _cluster_logger.error(
            "Cluster '%s' is broken (missing inner node types: %s). Source: %s",
            type_name, missing_regular, file_path or "<unknown>"
        )
    else:
        DynamicClusterNode.broken = False
        DynamicClusterNode.broken_reason = ""

    existing = NODE_REGISTRY.get(type_name)
    if missing_regular and existing is not None and not getattr(existing, "broken", False):
        _cluster_logger.warning(
            "Skipping registration of broken cluster '%s' from '%s'; keeping existing working registration.",
            type_name, file_path or "<unknown>"
        )
        return DynamicClusterNode

    register_node(type_name)(DynamicClusterNode)
    return DynamicClusterNode


def load_cluster_from_file(filepath: str):
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Cluster file not found: {filepath}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Security/Signature check
    import comfylab
    core_dir = Path(comfylab.__file__).parent.resolve()
    abs_path = path.resolve()
    is_core = core_dir in abs_path.parents or abs_path == core_dir
    
    unauthorized = False
    creator = "system"
    if not is_core:
        from comfylab.engine.security import verify_json, get_config
        creator, is_valid = verify_json(data)
        
        config = get_config()
        trusted_origins = config.get("trusted_origins", [])
        local_identity = config.get("creator_identity", "")
        
        is_trusted = is_valid and (creator == local_identity or creator in trusted_origins)
        if not is_trusted:
            unauthorized = True

    cluster_def = ClusterDefinitionModel.model_validate(data)
    cls = register_cluster_node(cluster_def, str(path))
    cls.unauthorized = unauthorized
    cls.creator_identity = creator
    return cluster_def



def load_clusters_from_directory(directory_path: str) -> int:
    dir_path = Path(directory_path).resolve()
    if not dir_path.exists() or not dir_path.is_dir():
        return 0

    count = 0
    for root, dirs, files in os.walk(str(dir_path)):
        if ".temp" in dirs:
            dirs.remove(".temp")
        for file in files:
            if file.endswith(".cluster.json"):
                full_path = Path(root) / file
                try:
                    load_cluster_from_file(str(full_path))
                    count += 1
                except Exception as e:
                    import logging
                    logger = logging.getLogger("comfylab.nodes.cluster")
                    logger.error(f"Failed to load cluster from {full_path}: {e}")
    return count


def generate_cluster_json(blueprint_nodes: list, blueprint_links: list,
                        boundary_pins: dict, display_name: str,
                        type_name: str, category: str = "User/Clusters",
                        icon: str = "📦", description: str = "") -> dict:
    return {
        "name": display_name,
        "type_name": type_name,
        "category": category,
        "icon": icon,
        "display_name": display_name,
        "description": description,
        "internal_blueprint": {
            "nodes": blueprint_nodes,
            "links": blueprint_links
        },
        "boundary_pins": boundary_pins
    }
