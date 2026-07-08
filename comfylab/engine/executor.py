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
import os
import uuid
import logging
import math
from typing import Dict, List, Any, Optional, Callable, Union

from comfylab.engine.models import BlueprintModel
from comfylab.engine.registry import get_node_class
from comfylab.engine.locks import ResourceLockManager
from comfylab.nodes.base import BaseNode, ExecutionContext, ExecIn, DataIn, ExecOut
from backend.workspace import get_workspace_path
from comfylab.engine.logging import run_id_var, set_node_context, reset_node_context

logger = logging.getLogger("comfylab.engine.executor")

PERSISTENT_IGNORED_KEYS = {"isPersistent", "autoClearPersistent"}

async def _detect_persistent_changes(node: BaseNode, context: ExecutionContext) -> tuple[bool, Dict[str, Any]]:
    """
    Checks if a persistent node's parameters or input pin data have changed since the last execution.
    Returns (has_changes, current_inputs).
    Properties are checked first (cheap, no I/O) and short-circuit before any upstream pull.
    """
    properties_changed = False
    for k, v in node.properties.items():
        if k not in PERSISTENT_IGNORED_KEYS and getattr(node, "_last_properties", {}).get(k) != v:
            properties_changed = True
            break
    for k in getattr(node, "_last_properties", {}):
        if k not in PERSISTENT_IGNORED_KEYS and k not in node.properties:
            properties_changed = True
            break

    if properties_changed:
        return True, {}

    current_inputs = {}
    for name, pin in node.inputs.items():
        if isinstance(pin, DataIn):
            current_inputs[name] = await context.pull(node.id, name)

    inputs_changed = False
    last_inputs = getattr(node, "_last_inputs", {})
    for k, v in current_inputs.items():
        if last_inputs.get(k) != v:
            inputs_changed = True
            break
    for k in last_inputs:
        if k not in current_inputs:
            inputs_changed = True
            break

    return inputs_changed, current_inputs

class ExecutionEngine:
    """
    Main executor for ComfyLAB graphs.
    Coordinates graph loading, state transitions, execution token flow (push wires),
    lazy data evaluation (pull wires), node execution watchdogs, and safe global teardown.
    """
    def __init__(self):
        self.state: str = "IDLE"  # IDLE, RUNNING, PAUSED, ABORTED
        self.lock_manager = ResourceLockManager()
        self.nodes: Dict[str, BaseNode] = {}
        self.persistent_nodes: Dict[str, BaseNode] = {}
        # maps (target_node_id, target_pin_name) -> (source_node_id, source_pin_name)
        self.data_links: Dict[tuple[str, str], tuple[str, str]] = {}
        # maps (source_node_id, source_pin_name) -> (target_node_id, target_pin_name)
        self.exec_links: Dict[tuple[str, str], tuple[str, str]] = {}
        # Tracks nodes in the order they started executing to perform reverse teardown
        self.executed_nodes_order: List[str] = []
        # Telemetry callback: async def (run_id, message_dict)
        self.telemetry_callback: Optional[Callable[[str, Dict[str, Any]], Any]] = None
        self._resume_event = asyncio.Event()
        self._resume_event.set()
        self.current_run_id: Optional[str] = None
        self.current_raw_canvas: Optional[Dict[str, Any]] = None
        self._active_tasks = set()
        self._teardown_lock = asyncio.Lock()
        self._teardown_complete = False


    def load_blueprint(self, blueprint_data: Union[Dict[str, Any], BlueprintModel]):
        """
        Validates the blueprint JSON schema, instantiates the required nodes
        from the registry, and maps both data and execution links.
        Accepts a raw dict (validated here) or a pre-validated BlueprintModel (used directly).
        """
        if isinstance(blueprint_data, BlueprintModel):
            blueprint = blueprint_data
        else:
            blueprint = BlueprintModel.model_validate(blueprint_data)

        # 1. Clean up self.persistent_nodes that are not in the new blueprint (i.e. deleted from canvas)
        blueprint_node_ids = {node_model.id for node_model in blueprint.nodes}
        nodes_to_teardown = []
        for p_id in list(self.persistent_nodes.keys()):
            if p_id not in blueprint_node_ids:
                node = self.persistent_nodes.pop(p_id)
                nodes_to_teardown.append(node)

        self.nodes.clear()
        self.data_links.clear()
        self.exec_links.clear()
        self.executed_nodes_order.clear()

        # Instantiate nodes
        for node_model in blueprint.nodes:
            cls = get_node_class(node_model.type)
            if getattr(cls, "unauthorized", False):
                raise ValueError(f"Cannot execute unauthorized custom node '{node_model.type}'. The code is unsigned or untrusted.")
            
            node_id = node_model.id
            is_persistent = node_model.properties.get("isPersistent", False)
            auto_clear = node_model.properties.get("autoClearPersistent", True)  # Checked by default!

            # Check if this node is already cached as persistent
            if is_persistent and node_id in self.persistent_nodes:
                cached_node = self.persistent_nodes[node_id]

                # Check if parameters changed (ignoring isPersistent and autoClearPersistent)
                properties_changed = False
                ignored_keys = {"isPersistent", "autoClearPersistent"}
                for k, v in node_model.properties.items():
                    if k not in ignored_keys and cached_node.properties.get(k) != v:
                        properties_changed = True
                        break
                # Also check if any old property was deleted
                for k in cached_node.properties:
                    if k not in ignored_keys and k not in node_model.properties:
                        properties_changed = True
                        break

                if properties_changed and auto_clear:
                    logger.info(f"Auto-clearing persistent node '{node_id}' due to parameter changes.")
                    nodes_to_teardown.append(cached_node)
                    self.persistent_nodes.pop(node_id)
                    # Create new instance
                    node_instance = cls(node_id, node_model.properties)
                    self.nodes[node_id] = node_instance
                    self.persistent_nodes[node_id] = node_instance
                else:
                    # Reuse cached instance and update properties
                    cached_node.properties = node_model.properties
                    self.nodes[node_id] = cached_node
            else:
                # If it was persistent before but toggled off, tear it down
                if node_id in self.persistent_nodes:
                    node = self.persistent_nodes.pop(node_id)
                    nodes_to_teardown.append(node)

                # Create a new instance
                node_instance = cls(node_id, node_model.properties)
                self.nodes[node_id] = node_instance
                if is_persistent:
                    self.persistent_nodes[node_id] = node_instance

        # Run teardown in background/sync for deleted/cleared nodes
        for node in nodes_to_teardown:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(node.teardown())
            except RuntimeError:
                try:
                    asyncio.run(node.teardown())
                except Exception as run_err:
                    logger.error(f"Teardown failed in sync context: {run_err}")

        # Map links
        for link in blueprint.links:
            if link.type == "data":
                self.data_links[(link.target_node, link.target_pin)] = (link.source_node, link.source_pin)
            elif link.type == "exec":
                self.exec_links[(link.source_node, link.source_pin)] = (link.target_node, link.target_pin)

    async def run(self, start_node_id: Optional[str] = None, start_pin_name: Optional[str] = None, run_id: Optional[str] = None):
        """
        Executes the currently loaded graph.
        If start_node_id and start_pin_name are provided, execution triggers there.
        Otherwise, triggers all entry nodes (nodes with execution inputs but no incoming execution links).
        """
        if self.state == "RUNNING" or self.state == "PAUSED":
            raise RuntimeError("Engine is already running or paused.")

        self.state = "RUNNING"
        self._resume_event.set()
        self.executed_nodes_order.clear()
        self._teardown_complete = False
        run_id = run_id or str(uuid.uuid4())
        self.current_run_id = run_id


        # Set run context variable
        run_token = run_id_var.set(run_id)
        logger.info(f"Execution run {run_id} started")

        context = ExecutionContext(self, run_id, self.lock_manager)

        original_cwd = os.getcwd()
        # Set the working directory to the workspace for this execution session.
        # This allows file-based nodes and script nodes to resolve relative paths
        # from the workspace root.
        os.chdir(str(get_workspace_path()))

        try:
            if start_node_id and start_pin_name:
                task = asyncio.create_task(self.trigger_exec(start_node_id, start_pin_name, context))
                self._active_tasks.add(task)
                task.add_done_callback(self._active_tasks.discard)
                await task
            else:
                entry_points = self._find_entry_points()
                if entry_points:
                    tasks = []
                    for node_id, pin_name in entry_points:
                        task = asyncio.create_task(self.trigger_exec(node_id, pin_name, context))
                        self._active_tasks.add(task)
                        task.add_done_callback(self._active_tasks.discard)
                        tasks.append(task)
                    await asyncio.gather(*tasks)

            if self.state == "RUNNING":
                self.state = "IDLE"
                logger.info(f"Execution run {run_id} completed successfully")
        except asyncio.CancelledError:
            self.state = "ABORTED"
            logger.warning(f"Execution run {run_id} was cancelled/aborted")
        except Exception as e:
            self.state = "ABORTED"
            logger.error(f"Execution run {run_id} failed with error: {e}")
            raise e
        finally:
            if self._active_tasks:
                for task in list(self._active_tasks):
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*self._active_tasks, return_exceptions=True)
                self._active_tasks.clear()
            os.chdir(original_cwd)
            await self._teardown_all()
            self.current_run_id = None
            self.current_raw_canvas = None
            run_id_var.reset(run_token)

    def _find_entry_points(self) -> List[tuple[str, str]]:
        """Finds all ExecIn pins that do not have incoming execution links."""
        exec_targets = set(self.exec_links.values())
        entry_points = []
        for node_id, node in self.nodes.items():
            for pin_name, pin in node.inputs.items():
                if isinstance(pin, ExecIn):
                    if (node_id, pin_name) not in exec_targets:
                        entry_points.append((node_id, pin_name))
        return entry_points

    async def trigger_exec(self, node_id: str, pin_name: str, context: ExecutionContext):
        """
        Triggers execution starting at a node input or output pin.
        If pin_name is an output pin (in exec_links), resolves it to target input pin first.
        Propagates execution token sequentially along execution wires.
        """
        current_node_id = node_id
        current_pin_name = pin_name

        if (node_id, pin_name) in self.exec_links:
            current_node_id, current_pin_name = self.exec_links[(node_id, pin_name)]

        while current_node_id is not None:
            if self.state == "ABORTED":
                break

            if self.state == "PAUSED":
                await self._resume_event.wait()

            if self.state == "ABORTED":
                break

            node = self.nodes.get(current_node_id)
            if not node:
                break

            # Track execution order for safe reverse teardown
            if current_node_id not in self.executed_nodes_order:
                self.executed_nodes_order.append(current_node_id)

            # Broadcast node start running status
            await self._broadcast_status(context.run_id, current_node_id, "running")

            # Set node context variables (ID, Name, File)
            node_tokens = set_node_context(node)
            logger.debug(f"Executing node '{current_node_id}'")
            try:
                # Node execution watchdog / timeout
                timeout = node.properties.get("timeout", None)
                try:
                    async def execute_node():
                        if node.properties.get("disabled", False):
                            logger.info(f"Node '{node.id}' is disabled. Passing execution token ahead.")
                            for name, pin in node.outputs.items():
                                if isinstance(pin, ExecOut):
                                    return name
                            return None

                        is_persistent = node.properties.get("isPersistent", False)
                        if is_persistent and getattr(node, "_has_executed", False):
                            has_changes, current_inputs = await _detect_persistent_changes(node, context)
                            if not has_changes:
                                logger.info(f"Skipping execution for persistent node '{node.id}' - no changes detected.")
                                if hasattr(node, "_last_outputs"):
                                    node._outputs = dict(node._last_outputs)
                                return getattr(node, "_last_next_pin", None)
                                
                            if node.properties.get("autoClearPersistent", True):
                                logger.info(f"Persistent node '{node.id}' inputs or parameters changed. Auto-clearing state before execution.")
                                try:
                                    await node.teardown()
                                except Exception as teardown_err:
                                    logger.error(f"Teardown failed during auto-clear: {teardown_err}")
                                if hasattr(node, "clear_data"):
                                    await node.clear_data()

                        next_pin = await node.execute(context, current_pin_name)

                        if is_persistent:
                            current_inputs = {}
                            for name, pin in node.inputs.items():
                                if isinstance(pin, DataIn):
                                    current_inputs[name] = await context.pull(node.id, name)
                            node._last_inputs = current_inputs
                            node._last_properties = {k: v for k, v in node.properties.items() if k not in PERSISTENT_IGNORED_KEYS}
                            node._last_outputs = dict(node._outputs) if hasattr(node, "_outputs") else {}
                            node._last_next_pin = next_pin
                            node._has_executed = True

                        return next_pin

                    if timeout is not None:
                        next_pin = await asyncio.wait_for(
                            execute_node(), 
                            timeout=float(timeout)
                        )
                    else:
                        next_pin = await execute_node()
                    
                    # Broadcast node success status
                    await self._broadcast_status(context.run_id, current_node_id, "success")
                    logger.debug(f"Finished executing node '{current_node_id}' with next pin '{next_pin}'")
                except Exception as e:
                    # Broadcast node error status
                    await self._broadcast_status(context.run_id, current_node_id, "error", message=str(e))
                    logger.error(f"Node '{current_node_id}' execution failed: {e}")
                    if isinstance(e, asyncio.TimeoutError):
                        raise TimeoutError(f"Node '{current_node_id}' exceeded execution timeout of {timeout}s.")
                    raise e
            finally:
                reset_node_context(node_tokens)

            # Clear data cache after each execution step so subsequent nodes get fresh calculations
            context.clear_cache()

            if not next_pin:
                break

            # Find next target pin in execution links
            link_key = (current_node_id, next_pin)
            if link_key in self.exec_links:
                current_node_id, current_pin_name = self.exec_links[link_key]
            else:
                break

    async def pull_data(self, target_node_id: str, target_pin_name: str, context: ExecutionContext) -> Any:
        """
        Evaluates data dependencies recursively (lazy pull evaluation).
        Retrieves cached values if already computed in the current step, or pulls from connected source.
        """
        link_key = (target_node_id, target_pin_name)
        target_node = self.nodes.get(target_node_id)
        if not target_node:
            raise ValueError(f"Target node '{target_node_id}' not found in graph.")
        pin = target_node.inputs.get(target_pin_name)

        val = None
        if link_key in self.data_links:
            source_node_id, source_pin_name = self.data_links[link_key]

            # Check cache
            cached, cached_val = context.get_cached(source_node_id, source_pin_name)
            if cached:
                val = cached_val
            else:
                source_node = self.nodes.get(source_node_id)
                if not source_node:
                    raise ValueError(f"Source node '{source_node_id}' not found in graph.")

                # Check if we can skip pulling (memoization)
                is_persistent = source_node.properties.get("isPersistent", False)
                skip_pull = False
                ignored_keys = {"isPersistent", "autoClearPersistent"}
                
                if is_persistent and getattr(source_node, "_has_pulled", False):
                    has_changes, current_inputs = await _detect_persistent_changes(source_node, context)
                    if not has_changes:
                        logger.info(f"Skipping pull_data for persistent node '{source_node.id}' - no changes detected.")
                        if hasattr(source_node, "_last_outputs") and source_pin_name in source_node._last_outputs:
                            val = source_node._last_outputs[source_pin_name]
                            skip_pull = True
                            
                    if has_changes and source_node.properties.get("autoClearPersistent", True):
                        logger.info(f"Persistent node '{source_node.id}' inputs or parameters changed. Auto-clearing state before pull.")
                        try:
                            await source_node.teardown()
                        except Exception as teardown_err:
                            logger.error(f"Teardown failed during auto-clear: {teardown_err}")
                        if hasattr(source_node, "clear_data"):
                            await source_node.clear_data()

                if not skip_pull:
                    is_disabled = source_node.properties.get("disabled", False)
                    if is_disabled:
                        logger.info(f"Node '{source_node_id}' is disabled. Attempting to pass-through data or return default.")
                        out_pin = source_node.outputs.get(source_pin_name)
                        in_pin = None
                        if out_pin:
                            for _, pin in source_node.inputs.items():
                                if isinstance(pin, DataIn) and pin.type_hint == out_pin.type_hint:
                                    in_pin = pin
                                    break
                        if in_pin:
                            val = await context.pull(source_node.id, in_pin.name)
                        else:
                            if out_pin:
                                th = out_pin.type_hint
                                if th in (float, int, "number"):
                                    val = 0
                                elif th in (bool, "boolean", "bool"):
                                    val = False
                                elif th in (str, "string"):
                                    val = ""
                                elif th in (list, "list", "array"):
                                    val = []
                                elif th in (dict, "dict", "object"):
                                    val = {}
                                else:
                                    val = None
                            else:
                                val = None
                    else:
                        # Set source node context variables during pulling
                        node_tokens = set_node_context(source_node)
                        logger.debug(f"Pulling data from node '{source_node_id}' output pin '{source_pin_name}'")
                        try:
                            # Pull data with optional watchdog timeout
                            timeout = source_node.properties.get("timeout", None)
                            try:
                                if timeout is not None:
                                    val = await asyncio.wait_for(
                                        source_node.pull_data(context, source_pin_name), 
                                        timeout=float(timeout)
                                    )
                                else:
                                    val = await source_node.pull_data(context, source_pin_name)
                            except asyncio.TimeoutError:
                                raise TimeoutError(f"Node '{source_node_id}' exceeded pull_data timeout of {timeout}s.")
                        finally:
                            reset_node_context(node_tokens)

                    # If persistent, cache current state
                    if is_persistent:
                        current_inputs = {}
                        for name, pin in source_node.inputs.items():
                            if isinstance(pin, DataIn):
                                current_inputs[name] = await context.pull(source_node.id, name)
                        source_node._last_inputs = current_inputs
                        source_node._last_properties = {k: v for k, v in source_node.properties.items() if k not in PERSISTENT_IGNORED_KEYS}
                        if not hasattr(source_node, "_last_outputs"):
                            source_node._last_outputs = {}
                        source_node._last_outputs[source_pin_name] = val
                        source_node._has_pulled = True

                context.cache_value(source_node_id, source_pin_name, val)
                await self.send_pin_values(
                    context.run_id, 
                    source_node_id, 
                    {source_pin_name: summarize_value(val)}
                )
        else:
            # Return property value if defined in blueprint, otherwise fallback to pin default value
            if isinstance(pin, DataIn):
                val = target_node.properties.get(target_pin_name)
                if val is None:
                    val = target_node.properties.get(target_pin_name.lower())
                if val is None:
                    val = pin.default

        # Safety range validation & clamping for DataIn pins
        if isinstance(pin, DataIn) and val is not None:
            if pin.min_val is not None or pin.max_val is not None:
                try:
                    numeric_val = float(val)
                    if pin.min_val is not None and numeric_val < pin.min_val:
                        logger.warning(f"Clamping value {numeric_val} for input pin '{target_pin_name}' on node '{target_node_id}' to min_val {pin.min_val}")
                        val = pin.min_val
                    elif pin.max_val is not None and numeric_val > pin.max_val:
                        logger.warning(f"Clamping value {numeric_val} for input pin '{target_pin_name}' on node '{target_node_id}' to max_val {pin.max_val}")
                        val = pin.max_val
                except (ValueError, TypeError):
                    pass

        return val

    async def abort(self):
        """Emergency stop. Forces engine into ABORTED state and triggers full teardown."""
        if self.state == "ABORTED":
            return
        self.state = "ABORTED"
        self._resume_event.set()  # Release any waiting task
        if self._active_tasks:
            for task in list(self._active_tasks):
                if not task.done():
                    task.cancel()
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
            self._active_tasks.clear()
        await self._teardown_all()

    async def pause(self):
        """Pauses the execution loop."""
        if self.state == "RUNNING":
            self.state = "PAUSED"
            self._resume_event.clear()
            if self.current_run_id:
                await self._broadcast_run_status(self.current_run_id, "paused")

    async def resume(self):
        """Resumes the execution loop."""
        if self.state == "PAUSED":
            self.state = "RUNNING"
            self._resume_event.set()
            if self.current_run_id:
                await self._broadcast_run_status(self.current_run_id, "running")

    async def _broadcast_run_status(self, run_id: str, status: str, error: Optional[str] = None):
        if self.telemetry_callback:
            msg = {
                "type": "run_status",
                "status": status
            }
            if error is not None:
                msg["error"] = error
            try:
                await self.telemetry_callback(run_id, msg)
            except Exception as e:
                logger.error(f"Failed to send run status telemetry: {e}")

    async def _broadcast_status(self, run_id: str, node_id: str, status: str, message: Optional[str] = None):
        if self.telemetry_callback:
            msg = {
                "type": "status",
                "node_id": node_id,
                "status": status
            }
            if message is not None:
                msg["message"] = message
            try:
                await self.telemetry_callback(run_id, msg)
            except Exception as e:
                logger.error(f"Failed to send status telemetry: {e}")

    async def send_telemetry(self, run_id: str, node_id: str, data: Any):
        if self.telemetry_callback:
            if isinstance(data, bytes):
                # Prefix the bytes with the run_id (36 characters)
                payload = run_id.encode('utf-8') + data
                try:
                    await self.telemetry_callback(run_id, payload)
                except Exception as e:
                    logger.error(f"Failed to send binary telemetry: {e}")
            else:
                msg = {
                    "type": "telemetry",
                    "node_id": node_id,
                    "data": data
                }
                try:
                    await self.telemetry_callback(run_id, msg)
                except Exception as e:
                    logger.error(f"Failed to send telemetry data: {e}")

    async def send_pin_values(self, run_id: str, node_id: str, pin_values: Dict[str, Any]):
        if self.telemetry_callback:
            msg = {
                "type": "pin_values",
                "node_id": node_id,
                "pin_values": pin_values
            }
            try:
                await self.telemetry_callback(run_id, msg)
            except Exception as e:
                logger.error(f"Failed to send pin values telemetry: {e}")

    async def _teardown_all(self):
        """Teardown all instantiated nodes in topological dependency order (downstream first)."""
        async with self._teardown_lock:
            if self._teardown_complete:
                return
            self._teardown_complete = True

            # Build adjacency list of upstream dependencies.
            # Node u depends on v if there is a data link from v to u, or execution link from v to u.
            nodes_to_sort = list(self.nodes.keys())
            upstream_map = {node_id: set() for node_id in nodes_to_sort}

            # Data links: (target_node, target_pin) -> (source_node, source_pin)
            # target reads from source, so target depends on source.
            for (target_id, _), (source_id, _) in self.data_links.items():
                if target_id in upstream_map and source_id in upstream_map:
                    upstream_map[target_id].add(source_id)

            # Exec links: (source_node, source_pin) -> (target_node, target_pin)
            # target executes after source, so target depends on source.
            for (source_id, _), (target_id, _) in self.exec_links.items():
                if target_id in upstream_map and source_id in upstream_map:
                    upstream_map[target_id].add(source_id)

            # Cycle-safe post-order DFS to sort nodes topologically
            visited = set()
            visiting = set()
            ordered_nodes = []

            def dfs(node_id: str):
                if node_id in visiting:
                    return  # Cycle detected, break to prevent infinite recursion
                if node_id in visited:
                    return
                visiting.add(node_id)
                for upstream in upstream_map[node_id]:
                    dfs(upstream)
                visiting.remove(node_id)
                visited.add(node_id)
                ordered_nodes.append(node_id)

            for node_id in nodes_to_sort:
                dfs(node_id)

            # ordered_nodes has upstream nodes first, downstream nodes last.
            # Reverse it so downstream nodes (which depend on upstream nodes) are torn down first.
            teardown_targets = list(reversed(ordered_nodes))

            # Execute teardown hooks
            for node_id in teardown_targets:
                node = self.nodes.get(node_id)
                if node:
                    # Skip teardown for persistent nodes
                    if node.properties.get("isPersistent", False):
                        logger.debug(f"Skipping teardown for persistent node '{node_id}'")
                        continue
                    try:
                        await node.teardown()
                    except Exception as e:
                        # Ensure one failing node teardown doesn't block other node teardowns
                        logger.error(f"Teardown failed for node '{node_id}': {e}")


def summarize_value(val: Any) -> str:
    if val is None:
        return "None"
    
    # Handle numpy arrays or other complex types with shape/dtype
    if hasattr(val, "shape") and hasattr(val, "dtype"):
        return f"ndarray{list(val.shape)} {val.dtype}"
        
    if isinstance(val, (int, float)):
        if isinstance(val, float):
            if math.isnan(val) or math.isinf(val):
                return str(val)
            if val == 0:
                return "0.0"
            if abs(val) < 1e-4 or abs(val) > 1e6:
                return f"{val:.4e}"
            return f"{val:.4f}".rstrip('0').rstrip('.')
        return str(val)
    if isinstance(val, bool):
        return "True" if val else "False"
    if isinstance(val, str):
        if len(val) > 40:
            return f'"{val[:37]}..."'
        return f'"{val}"'
    if isinstance(val, (list, tuple)):
        if not val:
            return "[]" if isinstance(val, list) else "()"
        preview = ", ".join(summarize_value(x) for x in val[:3])
        suffix = ", ..." if len(val) > 3 else ""
        return f"List({len(val)}) [{preview}{suffix}]" if isinstance(val, list) else f"Tuple({len(val)}) ({preview}{suffix})"
    if isinstance(val, dict):
        if not val:
            return "{}"
        items = list(val.items())
        preview = ", ".join(f"{k}: {summarize_value(v)}" for k, v in items[:3])
        suffix = ", ..." if len(items) > 3 else ""
        return f"Dict({len(val)}) {{{preview}{suffix}}}"
    
    # Fallback to string representation, limited in size
    s = str(val)
    if len(s) > 50:
        return f"{s[:47]}..."
    return s


