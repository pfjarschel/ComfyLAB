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

import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.workspace import get_workspace_path, set_workspace_path
from comfylab.engine.config import get_config, update_config, get_global_user_nodes_dir, get_global_user_clusters_dir
from comfylab.engine.security import (
    get_creator_identity,
    verify_json,
    verify_python_file,
    sign_python_file,
    sign_json
)

router = APIRouter()

class WorkspacePayload(BaseModel):
    path: str


class BlueprintSavePayload(BaseModel):
    filename: str
    blueprint: Dict[str, Any]


class TrustOriginPayload(BaseModel):
    origin_uuid: str


class AuthorizeNodePayload(BaseModel):
    filepath: str = ""
    all: bool = False


@router.get("/workspace")
async def get_workspace():
    """Returns the current workspace directory path."""
    ws_path = get_workspace_path()
    return {"path": str(ws_path)}


@router.post("/workspace")
async def update_workspace(payload: WorkspacePayload):
    """Sets the workspace directory path. Creates the directory if it doesn't exist."""
    try:
        ws_path = set_workspace_path(payload.path)
        update_config({"last_workspace": str(ws_path)})
        return {"path": str(ws_path)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to set workspace: {str(e)}")


@router.post("/workspace/blueprints")
async def save_blueprint_to_workspace(payload: BlueprintSavePayload):
    """Saves a blueprint JSON file to the workspace directory."""
    ws_path = get_workspace_path()
    blueprints_dir = ws_path / "blueprints"
    blueprints_dir.mkdir(parents=True, exist_ok=True)

    filename = payload.filename
    if not filename.endswith(".json"):
        filename += ".json"

    file_path = blueprints_dir / filename
    
    # Inject current machine's creator_identity into blueprint
    current_identity = get_creator_identity()
    blueprint = payload.blueprint.copy()
    blueprint["origin_uuid"] = current_identity

    file_path.write_text(json.dumps(blueprint, indent=2), encoding="utf-8")
    return {"path": str(file_path), "filename": filename}


@router.get("/workspace/blueprints")
async def list_workspace_blueprints():
    """Lists all blueprint JSON files in the workspace directory."""
    ws_path = get_workspace_path()
    blueprints_dir = ws_path / "blueprints"

    if not blueprints_dir.exists():
        return {"blueprints": []}

    blueprints = []
    for f in sorted(blueprints_dir.glob("*.json")):
        blueprints.append({
            "filename": f.name,
            "path": str(f),
            "size": f.stat().st_size,
            "modified": f.stat().st_mtime
        })
    return {"blueprints": blueprints}


@router.delete("/workspace/blueprints/{filename:path}")
async def delete_blueprint_from_workspace(filename: str):
    """Deletes a specific blueprint JSON file from the workspace directory."""
    ws_path = get_workspace_path()
    blueprints_dir = ws_path / "blueprints"

    if not filename.endswith(".json"):
        filename += ".json"

    file_path = blueprints_dir / filename

    if file_path.exists():
        try:
            file_path.unlink()
            return {"status": "success"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete blueprint: {str(e)}")
    else:
        raise HTTPException(status_code=404, detail="Blueprint not found")


@router.post("/workspace/blueprints/open-explorer")
async def open_blueprints_explorer():
    """Opens the blueprints directory in the system's file explorer."""
    ws_path = get_workspace_path()
    blueprints_dir = ws_path / "blueprints"
    blueprints_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        if platform.system() == "Windows":
            os.startfile(str(blueprints_dir))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(blueprints_dir)])
        else:
            subprocess.Popen(["xdg-open", str(blueprints_dir)])
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open explorer: {str(e)}")


import shutil

@router.post("/workspace/uploads")
async def upload_file(
    file: UploadFile = File(...),
    subdir: str = Form(""),
    filename: str = Form("")
):
    ws_path = get_workspace_path()
    uploads_dir = ws_path / "uploads"
    
    # Clean subdir path
    subdir = subdir.strip("/")
    if subdir:
        target_dir = (uploads_dir / subdir).resolve()
        if not target_dir.is_relative_to(uploads_dir):
            raise HTTPException(status_code=400, detail="Invalid sub-directory path.")
    else:
        target_dir = uploads_dir
        
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine filename
    final_filename = filename.strip() if filename.strip() else file.filename
    if not final_filename:
        final_filename = "unnamed_file"
        
    # Prevent path traversal in filename
    if "/" in final_filename or "\\" in final_filename:
        raise HTTPException(status_code=400, detail="Filename cannot contain path separators.")
        
    target_path = target_dir / final_filename
    
    # Handle duplicates by appending (x)
    if target_path.exists():
        base_name = target_path.stem
        ext = target_path.suffix
        counter = 1
        while True:
            new_name = f"{base_name}({counter}){ext}"
            new_path = target_dir / new_name
            if not new_path.exists():
                target_path = new_path
                final_filename = new_name
                break
            counter += 1
            
    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Calculate relative path from workspace root
        rel_path = target_path.relative_to(ws_path)
        return {"status": "success", "filepath": str(rel_path).replace("\\", "/"), "filename": final_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


@router.get("/workspace/files/{filepath:path}")
async def get_workspace_file(filepath: str):
    ws_path = get_workspace_path()
    target_path = (ws_path / filepath).resolve()
    
    if not target_path.is_relative_to(ws_path):
        raise HTTPException(status_code=403, detail="Access denied.")
        
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
        
    return FileResponse(str(target_path))


@router.get("/workspace/blueprints/{filename:path}")
async def load_blueprint_from_workspace(filename: str):
    """Loads a specific blueprint JSON file from the workspace directory."""
    ws_path = get_workspace_path()
    blueprints_dir = ws_path / "blueprints"

    if not filename.endswith(".json"):
        filename += ".json"

    file_path = blueprints_dir / filename

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        
        # Verify origin using signature or fallback identity
        current_identity = get_creator_identity()
        config = get_config()
        trusted_origins = config.get("trusted_origins", [])
            
        creator, is_valid = verify_json(data)
        if is_valid:
            origin_uuid = creator
        else:
            origin_uuid = data.get("creator_identity") or data.get("origin_uuid", "")
            
        # Ensure origin_uuid is populated in response for the UI warning dialog
        data["origin_uuid"] = origin_uuid
        
        is_trusted = is_valid and (origin_uuid == current_identity or origin_uuid in trusted_origins)
        # If it was saved with old unsigned metadata but matches our local machine or trusted list, trust it
        if not is_trusted and not is_valid:
            is_trusted = bool(origin_uuid and (origin_uuid == current_identity or origin_uuid in trusted_origins))
            
        if not is_trusted:
            data["origin_trusted"] = False
            if not origin_uuid:
                data["origin_warning"] = (
                    "This blueprint has no creator metadata (unknown source). "
                    "It may contain custom scripts. Do you trust this blueprint and want to load it?"
                )
            else:
                data["origin_warning"] = (
                    f"This blueprint was created by developer: {origin_uuid}. "
                    "It may contain custom scripts. Do you trust this developer and want to load it?"
                )
        else:
            data["origin_trusted"] = True
            
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read blueprint: {str(e)}")


@router.post("/workspace/blueprints/trust-origin")
async def trust_origin(payload: TrustOriginPayload):
    """Adds a creator identity to the trusted_origins settings list."""
    config = get_config()
    trusted = config.get("trusted_origins", [])
    if payload.origin_uuid not in trusted:
        trusted.append(payload.origin_uuid)
        update_config({"trusted_origins": trusted})
        
        # Trigger dynamic reload so that previously unauthorized nodes/clusters from this origin are authorized immediately
        from comfylab.nodes.loader import reload_registry
        reload_registry()
        
    return {"status": "success", "trusted_origins": trusted}


@router.get("/workspace/nodes/unauthorized")
async def list_unauthorized_nodes():
    """Lists all user node and cluster files that are currently unsigned or untrusted."""
    config = get_config()
    trusted_origins = config.get("trusted_origins", [])
    local_identity = config.get("creator_identity", "")
    
    unauthorized_files = []
    ws_path = get_workspace_path()
    
    paths_to_scan = [
        (ws_path / "nodes", "*.py", "python"),
        (ws_path / "clusters", "*.cluster.json", "cluster"),
        (get_global_user_nodes_dir(), "*.py", "python"),
        (get_global_user_clusters_dir(), "*.cluster.json", "cluster")
    ]
    
    for dir_path, pattern, file_type in paths_to_scan:
        if dir_path.exists() and dir_path.is_dir():
            for f in dir_path.glob(pattern):
                if file_type == "python":
                    creator, is_valid = verify_python_file(f)
                    is_trusted = is_valid and (creator == local_identity or creator in trusted_origins)
                    if not is_trusted:
                        unauthorized_files.append({
                            "filepath": str(f),
                            "filename": f.name,
                            "type": "node",
                            "creator_identity": creator,
                            "is_valid": is_valid
                        })
                else:
                    try:
                        with open(f, "r", encoding="utf-8") as file:
                            cluster_data = json.load(file)
                        creator, is_valid = verify_json(cluster_data)
                        is_trusted = is_valid and (creator == local_identity or creator in trusted_origins)
                        if not is_trusted:
                            unauthorized_files.append({
                                "filepath": str(f),
                                "filename": f.name,
                                "type": "cluster",
                                "creator_identity": creator,
                                "is_valid": is_valid
                            })
                    except Exception:
                        unauthorized_files.append({
                            "filepath": str(f),
                            "filename": f.name,
                            "type": "cluster",
                            "creator_identity": "",
                            "is_valid": False
                        })
                        
    return {"unauthorized": unauthorized_files}


@router.post("/workspace/nodes/authorize")
async def authorize_nodes(payload: AuthorizeNodePayload):
    """Signs custom nodes or clusters with the host's private key to authorize them."""
    ws_path = get_workspace_path()
    allowed_roots = [
        ws_path / "nodes",
        ws_path / "clusters",
        get_global_user_nodes_dir(),
        get_global_user_clusters_dir()
    ]
    
    def authorize_single_file(f_path: Path):
        resolved = f_path.resolve()
        is_allowed = False
        for root in allowed_roots:
            if root.resolve() in resolved.parents or resolved == root.resolve():
                is_allowed = True
                break
        if not is_allowed:
            raise HTTPException(status_code=403, detail="Access denied: File must be inside workspace or user nodes/clusters folders.")
            
        if resolved.name.endswith(".py"):
            sign_python_file(resolved)
        elif resolved.name.endswith(".cluster.json"):
            with open(resolved, "r", encoding="utf-8") as f:
                data = json.load(f)
            signed_data = sign_json(data)
            resolved.write_text(json.dumps(signed_data, indent=2), encoding="utf-8")
            
    if payload.all:
        unauth_res = await list_unauthorized_nodes()
        for item in unauth_res["unauthorized"]:
            authorize_single_file(Path(item["filepath"]))
    else:
        if not payload.filepath:
            raise HTTPException(status_code=400, detail="Missing filepath.")
        authorize_single_file(Path(payload.filepath))
        
    from comfylab.nodes.loader import reload_registry
    reload_registry()
    
    return {"success": True}
