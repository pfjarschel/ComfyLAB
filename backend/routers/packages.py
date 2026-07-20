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
import zipfile
import shutil
import tempfile
import logging
import inspect
from pathlib import Path
from typing import Dict, Any, List, Tuple
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import comfylab
from backend.workspace import get_workspace_path

logger = logging.getLogger("backend.routers.packages")

router = APIRouter()

class PackageExportPayload(BaseModel):
    filename: str
    blueprint: Dict[str, Any]


class PackageLoadPayload(BaseModel):
    filename: str


class PackageImportPayload(BaseModel):
    package_filename: str
    destination: str  # "workspace" or "user"
    trust_and_sign: bool
    delete_package: bool
    import_permanent: bool = True


def extract_zip_safely(zip_path: Path, extract_dir: Path):
    extract_dir = extract_dir.resolve()
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        for member in zip_ref.infolist():
            # Resolve target path
            target_path = Path(extract_dir / member.filename).resolve()
            # Check for directory traversal
            if not target_path.is_relative_to(extract_dir):
                raise HTTPException(status_code=400, detail=f"Path traversal detected in zip member: {member.filename}")
            # If it's a directory, create it
            if member.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zip_ref.open(member) as source, open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)


def find_blueprint_dependencies(blueprint: dict) -> Tuple[List[Path], List[Path]]:
    """
    Scans a blueprint dict for custom nodes and clusters.
    Returns (custom_node_files: List[Path], cluster_files: List[Path]).
    """
    from comfylab.engine.registry import NODE_REGISTRY
    
    core_dir = Path(comfylab.__file__).parent.resolve()
    
    custom_node_files = set()
    cluster_files = set()
    
    # We want to scan recursively if clusters contain other custom nodes/clusters
    blueprints_to_scan = [blueprint]
    scanned_clusters = set()
    
    while blueprints_to_scan:
        current_bp = blueprints_to_scan.pop(0)
        for node in current_bp.get("nodes", []):
            node_type = node.get("type")
            if node_type == "actionNode" and isinstance(node.get("data"), dict):
                node_type = node.get("data", {}).get("action")
                
            if not node_type or node_type not in NODE_REGISTRY:
                continue
                
            cls = NODE_REGISTRY[node_type]
            
            # Check if it is a cluster
            if hasattr(cls, "_cluster_file_path") and cls._cluster_file_path:
                cluster_path = Path(cls._cluster_file_path).resolve()
                if cluster_path.exists() and cluster_path not in cluster_files:
                    cluster_files.add(cluster_path)
                    
                    # Read the cluster's internal blueprint and scan it too!
                    if node_type not in scanned_clusters:
                        scanned_clusters.add(node_type)
                        try:
                            with open(cluster_path, "r", encoding="utf-8") as f:
                                cluster_data = json.load(f)
                            internal_bp = cluster_data.get("internal_blueprint", {})
                            blueprints_to_scan.append(internal_bp)
                        except Exception as e:
                            logger.error(f"Failed to parse cluster internal blueprint for {node_type}: {e}")
            else:
                # Normal node: check if it's dynamic
                try:
                    abs_path = Path(inspect.getfile(cls)).resolve()
                    is_core = core_dir in abs_path.parents or abs_path == core_dir
                    if not is_core and abs_path.exists() and abs_path not in custom_node_files:
                        custom_node_files.add(abs_path)
                except Exception:
                    pass
                    
    return list(custom_node_files), list(cluster_files)


@router.get("/workspace/packages")
async def list_packages():
    """Lists all .cfy package files in the workspace directory."""
    ws_path = get_workspace_path()
    packages_dir = ws_path / "packages"
    packages_dir.mkdir(parents=True, exist_ok=True)
    
    packages = []
    for f in sorted(packages_dir.glob("*.cfy")):
        packages.append({
            "filename": f.name,
            "path": str(f),
            "size": f.stat().st_size,
            "modified": f.stat().st_mtime
        })
    return {"packages": packages}


@router.delete("/workspace/packages/{filename:path}")
async def delete_package(filename: str):
    """Deletes a specific package .cfy file from the workspace directory."""
    ws_path = get_workspace_path()
    packages_dir = ws_path / "packages"

    if not filename.endswith(".cfy"):
        filename += ".cfy"

    file_path = packages_dir / filename

    if file_path.exists():
        try:
            file_path.unlink()
            return {"status": "success"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete package: {str(e)}")
    else:
        raise HTTPException(status_code=404, detail="Package not found")


@router.post("/workspace/packages")
async def export_package(payload: PackageExportPayload):
    """Bundles a blueprint and its custom node/cluster dependencies into a .cfy package."""
    ws_path = get_workspace_path()
    packages_dir = ws_path / "packages"
    packages_dir.mkdir(parents=True, exist_ok=True)
    
    filename = payload.filename
    if not filename.endswith(".cfy"):
        filename += ".cfy"
        
    package_path = packages_dir / filename
    
    # 1. Scan for dependencies
    custom_nodes, clusters = find_blueprint_dependencies(payload.blueprint)
    
    # 2. Automatically sign them using local host key before bundling
    from comfylab.engine.security import sign_python_file, sign_json
    
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Save signed blueprint
        signed_bp = sign_json(payload.blueprint)
        bp_file = temp_dir / "blueprint.json"
        bp_file.write_text(json.dumps(signed_bp, indent=2), encoding="utf-8")
        
        # Save signed custom nodes
        nodes_temp_dir = temp_dir / "nodes"
        if custom_nodes:
            nodes_temp_dir.mkdir()
            for node_path in custom_nodes:
                target_node_path = nodes_temp_dir / node_path.name
                shutil.copy2(node_path, target_node_path)
                sign_python_file(target_node_path)
                
        # Save signed clusters
        clusters_temp_dir = temp_dir / "clusters"
        if clusters:
            clusters_temp_dir.mkdir()
            for cluster_path in clusters:
                with open(cluster_path, "r", encoding="utf-8") as f:
                    cluster_data = json.load(f)
                signed_cluster = sign_json(cluster_data)
                target_cluster_path = clusters_temp_dir / cluster_path.name
                target_cluster_path.write_text(json.dumps(signed_cluster, indent=2), encoding="utf-8")
                
        # 3. Create zip archive
        with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
            zip_ref.write(bp_file, "blueprint.json")
            if custom_nodes:
                for f in nodes_temp_dir.iterdir():
                    zip_ref.write(f, f"nodes/{f.name}")
            if clusters:
                for f in clusters_temp_dir.iterdir():
                    zip_ref.write(f, f"clusters/{f.name}")
                    
        return {"path": str(package_path), "filename": filename}
    finally:
        shutil.rmtree(temp_dir)


@router.post("/workspace/packages/load")
async def load_package_preview(payload: PackageLoadPayload):
    """Safely extracts a package temporarily to inspect contents and check signatures."""
    ws_path = get_workspace_path()
    package_path = ws_path / "packages" / payload.filename
    if not package_path.exists():
        raise HTTPException(status_code=404, detail=f"Package '{payload.filename}' not found.")
        
    temp_dir = Path(tempfile.mkdtemp())
    try:
        extract_zip_safely(package_path, temp_dir)
        
        bp_path = temp_dir / "blueprint.json"
        if not bp_path.exists():
            raise HTTPException(status_code=400, detail="Invalid package: blueprint.json is missing.")
            
        with open(bp_path, "r", encoding="utf-8") as f:
            blueprint = json.load(f)
            
        # Verify custom nodes signatures
        from comfylab.engine.security import verify_python_file, verify_json, get_config
        config = get_config()
        trusted_origins = config.get("trusted_origins", [])
        local_identity = config.get("creator_identity", "")
        
        nodes_list = []
        nodes_dir = temp_dir / "nodes"
        if nodes_dir.exists() and nodes_dir.is_dir():
            for f in nodes_dir.glob("*.py"):
                creator, is_valid = verify_python_file(f)
                is_trusted = is_valid and (creator == local_identity or creator in trusted_origins)
                nodes_list.append({
                    "filename": f.name,
                    "creator_identity": creator,
                    "is_valid": is_valid,
                    "is_trusted": is_trusted
                })
                
        # Verify clusters signatures
        clusters_list = []
        clusters_dir = temp_dir / "clusters"
        if clusters_dir.exists() and clusters_dir.is_dir():
            for f in clusters_dir.glob("*.cluster.json"):
                with open(f, "r", encoding="utf-8") as file:
                    cluster_data = json.load(file)
                creator, is_valid = verify_json(cluster_data)
                is_trusted = is_valid and (creator == local_identity or creator in trusted_origins)
                clusters_list.append({
                    "filename": f.name,
                    "creator_identity": creator,
                    "is_valid": is_valid,
                    "is_trusted": is_trusted
                })
                
        # Verify overall blueprint signature if present
        bp_creator, bp_valid = verify_json(blueprint)
        bp_trusted = bp_valid and (bp_creator == local_identity or bp_creator in trusted_origins)
        
        return {
            "blueprint": blueprint,
            "blueprint_status": {
                "creator_identity": bp_creator,
                "is_valid": bp_valid,
                "is_trusted": bp_trusted
            },
            "nodes": nodes_list,
            "clusters": clusters_list
        }
    finally:
        shutil.rmtree(temp_dir)


@router.post("/workspace/packages/import")
async def import_package(payload: PackageImportPayload):
    """Imports package contents into either workspace or local user folders."""
    ws_path = get_workspace_path()
    package_path = ws_path / "packages" / payload.package_filename
    if not package_path.exists():
        raise HTTPException(status_code=404, detail=f"Package '{payload.package_filename}' not found.")
        
    if not payload.import_permanent:
        target_bp_dir = ws_path / "blueprints" / ".temp"
        target_nodes_dir = ws_path / "nodes" / ".temp"
        target_clusters_dir = ws_path / "clusters" / ".temp"
        
        # Clean up any previous temp extraction to avoid leftovers
        for d in [target_bp_dir, target_nodes_dir, target_clusters_dir]:
            if d.exists():
                shutil.rmtree(d)
    else:
        if payload.destination == "workspace":
            target_bp_dir = ws_path / "blueprints"
            target_nodes_dir = ws_path / "nodes"
            target_clusters_dir = ws_path / "clusters"
        elif payload.destination == "user":
            from comfylab.engine.config import get_global_user_nodes_dir, get_global_user_clusters_dir
            target_bp_dir = ws_path / "blueprints"
            target_nodes_dir = get_global_user_nodes_dir()
            target_clusters_dir = get_global_user_clusters_dir()
        else:
            raise HTTPException(status_code=400, detail=f"Invalid destination: {payload.destination}")
        
    target_bp_dir.mkdir(parents=True, exist_ok=True)
    target_nodes_dir.mkdir(parents=True, exist_ok=True)
    target_clusters_dir.mkdir(parents=True, exist_ok=True)
    
    temp_dir = Path(tempfile.mkdtemp())
    try:
        extract_zip_safely(package_path, temp_dir)
        
        from comfylab.engine.security import sign_python_file, sign_json
        
        # 1. Blueprint JSON file
        bp_src = temp_dir / "blueprint.json"
        if bp_src.exists():
            bp_dest_filename = payload.package_filename.rsplit(".", 1)[0] + ".json"
            bp_dest = target_bp_dir / bp_dest_filename
            
            with open(bp_src, "r", encoding="utf-8") as f:
                bp_data = json.load(f)
            if payload.trust_and_sign:
                bp_data = sign_json(bp_data)
                
            bp_dest.write_text(json.dumps(bp_data, indent=2), encoding="utf-8")
            
        # 2. Nodes
        nodes_dir = temp_dir / "nodes"
        if nodes_dir.exists() and nodes_dir.is_dir():
            for f in nodes_dir.glob("*.py"):
                dest_file = target_nodes_dir / f.name
                shutil.copy2(f, dest_file)
                if payload.trust_and_sign:
                    sign_python_file(dest_file)
                    
        # 3. Clusters
        clusters_dir = temp_dir / "clusters"
        if clusters_dir.exists() and clusters_dir.is_dir():
            for f in clusters_dir.glob("*.cluster.json"):
                dest_file = target_clusters_dir / f.name
                if payload.trust_and_sign:
                    with open(f, "r", encoding="utf-8") as file:
                        cluster_data = json.load(file)
                    signed_cluster = sign_json(cluster_data)
                    dest_file.write_text(json.dumps(signed_cluster, indent=2), encoding="utf-8")
                else:
                    shutil.copy2(f, dest_file)
                    
        # 4. Optional package deletion
        if payload.import_permanent and payload.delete_package:
            try:
                package_path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete package file: {e}")
                
        # Trigger hot-reload
        from comfylab.nodes.loader import reload_registry, load_nodes_from_directory
        from comfylab.nodes.cluster import load_clusters_from_directory
        reload_registry()
        
        if not payload.import_permanent:
            # Explicitly load temporary nodes and clusters which are otherwise excluded!
            load_nodes_from_directory(str(target_nodes_dir))
            load_clusters_from_directory(str(target_clusters_dir))
        
        return {"success": True}
    finally:
        shutil.rmtree(temp_dir)


@router.post("/workspace/packages/clear_temp")
async def clear_temporary_package_files():
    """Purges all .temp subdirectories under workspace blueprints, nodes, and clusters and triggers a registry reload."""
    ws_path = get_workspace_path()
    try:
        for subdir in ["blueprints", "nodes", "clusters"]:
            temp_dir = ws_path / subdir / ".temp"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        tmp_dir = ws_path / ".tmp"
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        from comfylab.nodes.loader import reload_registry
        reload_registry()
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to clear temporary package files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear temporary files: {str(e)}")
