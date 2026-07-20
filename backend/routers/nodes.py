import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from comfylab.engine.config import get_global_user_nodes_dir, get_global_user_clusters_dir
from backend.workspace import get_workspace_path
from comfylab.nodes.loader import load_module_from_filepath
from comfylab.nodes.publisher import generate_node_class_code
from comfylab.nodes.cluster import parse_cluster_boundary_pins
from comfylab.engine.registry import get_all_nodes_schema

router = APIRouter()

# ----------------------------------------------------------------------------
# NODE REGISTRY & DISCOVERY
# ----------------------------------------------------------------------------

@router.get("/nodes")
async def get_node_templates():
    """
    Returns the complete serialized metadata schema of all registered ComfyLAB nodes.
    Used by the frontend to dynamically build sidebar nodes and parameter widgets.
    """
    return get_all_nodes_schema()


@router.post("/nodes/reload")
async def reload_node_registry():
    """
    Rescans the filesystem for nodes and returns the updated schema.
    """
    from comfylab.nodes.loader import load_all_nodes
    from comfylab.engine.registry import NODE_REGISTRY, load_all_clusters_deferred, invalidate_schema_cache
    from comfylab.engine.security import clear_signature_cache
    NODE_REGISTRY.clear()
    invalidate_schema_cache()
    clear_signature_cache()
    load_all_nodes()
    load_all_clusters_deferred(force=True)
    return get_all_nodes_schema()

# ----------------------------------------------------------------------------
# NODE PUBLISHING
# ----------------------------------------------------------------------------

class PublishNodePayload(BaseModel):
    display_name: str
    category: str
    icon: str
    description: str
    code: str
    language: str = "python"
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]
    destination: str # "global" or "workspace"


@router.post("/nodes/publish")
async def publish_node(payload: PublishNodePayload):
    # Determine directory
    if payload.destination == "global":
        target_dir = get_global_user_nodes_dir()
    elif payload.destination == "workspace":
        workspace_path = get_workspace_path()
        if not workspace_path:
            raise HTTPException(status_code=400, detail="No active workspace found to publish node to.")
        target_dir = workspace_path / "nodes"
        target_dir.mkdir(parents=True, exist_ok=True)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid destination: {payload.destination}")

    # Generate file name
    clean_name = re.sub(r'[^a-zA-Z0-9\s_-]', '', payload.display_name)
    clean_name = re.sub(r'[\s_-]+', '_', clean_name).strip('_').lower()
    
    if not clean_name:
        raise HTTPException(status_code=400, detail="Invalid node name.")

    prefix = "user" if payload.destination == "global" else "workspace"
    type_name = f"{prefix}/{clean_name}"
    
    # Class name formatting
    words = re.sub(r'[^a-zA-Z0-9\s_-]', '', payload.display_name).replace('_', ' ').replace('-', ' ').split()
    class_name = "".join(w.capitalize() for w in words)
    if not class_name.endswith("Node"):
        class_name += "Node"
        
    filename = f"{clean_name}.py"
    filepath = target_dir / filename

    # Generate Python code
    code_content = generate_node_class_code(
        display_name=payload.display_name,
        class_name=class_name,
        type_name=type_name,
        category=payload.category,
        icon=payload.icon,
        description=payload.description,
        inputs=payload.inputs,
        outputs=payload.outputs,
        original_code=payload.code,
        language=payload.language,
        destination=payload.destination,
        clean_name=clean_name
    )

    # Validate syntax with compile()
    try:
        compile(code_content, f"<publish:{clean_name}>", "exec")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Generated code has syntax errors: {e}")

    # Write file
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write node class file: {e}")

    # Sign file
    try:
        from comfylab.engine.security import sign_python_file
        sign_python_file(filepath)
    except Exception as e:
        if filepath.exists():
            filepath.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to cryptographically sign node class file: {e}")

    # Trigger hot-reload
    try:
        load_module_from_filepath(str(filepath))
    except Exception as e:
        # If it failed to import, clean up written file to avoid breaking next starts
        if filepath.exists():
            filepath.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to import/register published node: {e}")

    return {
        "success": True,
        "type": type_name,
        "file_path": str(filepath)
    }

# ----------------------------------------------------------------------------
# CLUSTER PUBLISHING & UPDATING
# ----------------------------------------------------------------------------

class PublishClusterPayload(BaseModel):
    display_name: str
    category: str
    icon: str
    description: str
    internal_blueprint: Dict[str, Any]
    boundary_pins: Dict[str, Any]
    destination: str  # "global", "workspace", or "temp"
    type_name: Optional[str] = None


@router.post("/nodes/publish_cluster")
async def publish_cluster(payload: PublishClusterPayload):
    if payload.destination == "global":
        target_dir = get_global_user_clusters_dir()
        prefix = "user/cluster"
    elif payload.destination == "workspace":
        workspace_path = get_workspace_path()
        if not workspace_path:
            raise HTTPException(status_code=400, detail="No active workspace found to publish cluster to.")
        target_dir = workspace_path / "clusters"
        target_dir.mkdir(parents=True, exist_ok=True)
        prefix = "workspace/cluster"
    elif payload.destination == "temp":
        workspace_path = get_workspace_path()
        if not workspace_path:
            raise HTTPException(status_code=400, detail="No active workspace found to publish cluster to.")
        target_dir = workspace_path / "clusters" / ".temp"
        target_dir.mkdir(parents=True, exist_ok=True)
        if payload.type_name and "/" in payload.type_name:
            prefix = payload.type_name.rsplit("/", 1)[0]
        else:
            prefix = "workspace/cluster"
    else:
        raise HTTPException(status_code=400, detail=f"Invalid destination: {payload.destination}")

    clean_name = re.sub(r'[^a-zA-Z0-9\s_-]', '', payload.display_name)
    clean_name = re.sub(r'[\s_-]+', '_', clean_name).strip('_').lower()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Invalid node name.")

    type_name = f"{prefix}/{clean_name}"
    filename = f"{clean_name}.cluster.json"
    filepath = target_dir / filename

    boundary_pins = parse_cluster_boundary_pins(payload.internal_blueprint, payload.boundary_pins)

    cluster_json = {
        "name": payload.display_name,
        "type_name": type_name,
        "category": payload.category,
        "icon": payload.icon,
        "display_name": payload.display_name,
        "description": payload.description,
        "internal_blueprint": payload.internal_blueprint,
        "boundary_pins": boundary_pins
    }

    from comfylab.engine.models import ClusterDefinitionModel
    try:
        ClusterDefinitionModel.model_validate(cluster_json)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid cluster definition: {e}")

    try:
        from comfylab.engine.security import sign_json
        signed_cluster = sign_json(cluster_json)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(signed_cluster, f, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write cluster file: {e}")

    try:
        from comfylab.nodes.cluster import load_cluster_from_file
        load_cluster_from_file(str(filepath))
    except Exception as e:
        if filepath.exists():
            filepath.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to register published cluster: {e}")

    return {
        "success": True,
        "type": type_name,
        "file_path": str(filepath)
    }


@router.get("/cluster/{type_name:path}")
async def get_cluster_definition(type_name: str):
    from pathlib import Path
    from comfylab.engine.config import get_global_user_clusters_dir
    from backend.workspace import get_workspace_path

    slug = type_name.split("/")[-1] if "/" in type_name else type_name
    candidates = []
    candidates.append(get_global_user_clusters_dir() / f"{slug}.cluster.json")
    ws = get_workspace_path()
    if ws:
        candidates.append(ws / "clusters" / f"{slug}.cluster.json")
        candidates.append(ws / "clusters" / ".temp" / f"{slug}.cluster.json")

    for candidate in candidates:
        if candidate.exists():
            with open(candidate, "r", encoding="utf-8") as f:
                data = json.load(f)
                if ".temp" in candidate.parts:
                    data["_is_temp"] = True
                return data

    raise HTTPException(status_code=404, detail=f"Cluster definition not found for type '{type_name}'")


class UpdateClusterPayload(BaseModel):
    category: str
    icon: str
    description: str

@router.put("/nodes/update_cluster/{type_name:path}")
async def update_cluster(type_name: str, payload: UpdateClusterPayload):
    from pathlib import Path
    from comfylab.engine.config import get_global_user_clusters_dir
    from backend.workspace import get_workspace_path

    slug = type_name.split("/")[-1] if "/" in type_name else type_name
    candidates = []
    candidates.append(get_global_user_clusters_dir() / f"{slug}.cluster.json")
    ws = get_workspace_path()
    if ws:
        candidates.append(ws / "clusters" / f"{slug}.cluster.json")
        candidates.append(ws / "clusters" / ".temp" / f"{slug}.cluster.json")

    filepath = None
    for candidate in candidates:
        if candidate.exists():
            filepath = candidate
            break

    if not filepath:
        raise HTTPException(status_code=404, detail=f"Cluster definition not found for type '{type_name}'")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        data["category"] = payload.category
        data["icon"] = payload.icon
        data["description"] = payload.description

        from comfylab.engine.security import sign_json
        signed_cluster = sign_json(data)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(signed_cluster, f, indent=2)
            
        from comfylab.nodes.cluster import load_cluster_from_file
        from comfylab.engine.registry import invalidate_schema_cache
        load_cluster_from_file(str(filepath))
        invalidate_schema_cache()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update cluster: {e}")

    return {"success": True}
