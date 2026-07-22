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

import os
import base64
import json
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from comfylab.engine.config import get_comfylab_base_dir, get_config, update_config

logger = logging.getLogger("comfylab.engine.security")

_cached_private_key: Optional[ed25519.Ed25519PrivateKey] = None

# Cache verify_python_file results keyed by (path, mtime, size) -> (creator_identity, is_valid)
_sig_cache: Dict[tuple, Tuple[str, bool]] = {}
_SIG_CACHE_MAX_SIZE = 512


def clear_signature_cache() -> None:
    """Clears the cached file signature verifications. Call before a full reload."""
    _sig_cache.clear()


def evaluate_trust(creator: str, is_valid: bool, config: dict = None) -> bool:
    """
    Decides whether a signed artifact is trusted: the signature must be valid AND
    the creator must be the local machine identity or a configured trusted origin.
    """
    if not is_valid or not creator:
        return False
    if config is None:
        config = get_config()
    local_identity = config.get("creator_identity", "")
    trusted_origins = config.get("trusted_origins", [])
    return creator == local_identity or creator in trusted_origins


def _sig_cache_set(key: tuple, value: Tuple[str, bool]) -> None:
    """Adds an entry to the signature cache, evicting oldest entries if it grows too large."""
    if len(_sig_cache) >= _SIG_CACHE_MAX_SIZE:
        # Evict ~25% oldest entries (dicts preserve insertion order)
        for old_key in list(_sig_cache.keys())[: _SIG_CACHE_MAX_SIZE // 4]:
            del _sig_cache[old_key]
    _sig_cache[key] = value

def get_private_key_path() -> Path:
    """Returns the path to the private key pem file."""
    return get_comfylab_base_dir() / "private_key.pem"

def get_private_key() -> ed25519.Ed25519PrivateKey:
    """Loads or generates the host's Ed25519 private key."""
    global _cached_private_key
    if _cached_private_key is not None:
        return _cached_private_key

    key_path = get_private_key_path()
    if not key_path.exists():
        logger.info(f"Generating new Ed25519 private key at {key_path}")
        private_key = ed25519.Ed25519PrivateKey.generate()
        
        # Serialize private key to PEM
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Write to file with owner-only permissions
        key_path.write_bytes(pem)
        os.chmod(key_path, 0o600)
        
        # Derive public key and update config
        public_key = private_key.public_key()
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        creator_identity = pub_bytes.hex()
        update_config({"creator_identity": creator_identity})
    else:
        # Load existing key
        pem = key_path.read_bytes()
        private_key = serialization.load_pem_private_key(pem, password=None)
        if not isinstance(private_key, ed25519.Ed25519PrivateKey):
            raise TypeError("Loaded key is not an Ed25519PrivateKey")
        
        # Update config identity if missing
        config = get_config()
        if not config.get("creator_identity"):
            public_key = private_key.public_key()
            pub_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            update_config({"creator_identity": pub_bytes.hex()})

    _cached_private_key = private_key
    return private_key

def get_creator_identity() -> str:
    """Returns the local host's creator identity (hex-encoded Ed25519 public key)."""
    # Force private key loading/generation
    get_private_key()
    return get_config().get("creator_identity", "")

def sign_data(data: bytes) -> str:
    """Signs bytes using the private key and returns a Base64-encoded signature."""
    private_key = get_private_key()
    sig_bytes = private_key.sign(data)
    return base64.b64encode(sig_bytes).decode("utf-8")

def verify_data(data: bytes, signature_b64: str, public_key_hex: str) -> bool:
    """Verifies a signature against the provided hex public key. Returns True if valid."""
    try:
        pub_bytes = bytes.fromhex(public_key_hex)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
        sig_bytes = base64.b64decode(signature_b64.encode("utf-8"))
        public_key.verify(sig_bytes, data)
        return True
    except Exception as e:
        logger.debug(f"Signature verification failed: {e}")
        return False

def sign_python_file(filepath: Path) -> None:
    """Reads a Python file, strips any existing signature block, signs the code, and appends the signature comments."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
        
    code_lines = filepath.read_text(encoding="utf-8").splitlines()
    
    # Strip signature lines from the bottom
    clean_lines = []
    for line in code_lines:
        if line.startswith("# @creator_identity:") or line.startswith("# @signature:"):
            continue
        clean_lines.append(line)
        
    # Standardize content: join with newlines and strip trailing whitespace
    clean_code = "\n".join(clean_lines).rstrip()
    
    # Sign clean code
    signature = sign_data(clean_code.encode("utf-8"))
    identity = get_creator_identity()
    
    # Write back the code plus the signature block
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(clean_code + "\n\n")
        f.write(f"# @creator_identity: {identity}\n")
        f.write(f"# @signature: {signature}\n")

def verify_python_file(filepath: Path) -> Tuple[str, bool]:
    """
    Verifies a Python file's signature block.
    Returns (creator_identity, is_valid).
    Results are cached by (path, mtime, size) so unchanged files are not re-verified.
    """
    if not filepath.exists():
        return "", False

    try:
        st = filepath.stat()
        cache_key = (str(filepath), st.st_mtime, st.st_size)
    except OSError:
        cache_key = None

    if cache_key is not None and cache_key in _sig_cache:
        return _sig_cache[cache_key]

    code_lines = filepath.read_text(encoding="utf-8").splitlines()

    creator_identity = ""
    signature = ""
    clean_lines = []

    for line in code_lines:
        if line.startswith("# @creator_identity:"):
            creator_identity = line.split(":", 1)[1].strip()
        elif line.startswith("# @signature:"):
            signature = line.split(":", 1)[1].strip()
        else:
            clean_lines.append(line)

    if not creator_identity or not signature:
        result = ("", False)
        if cache_key is not None:
            _sig_cache_set(cache_key, result)
        return result

    clean_code = "\n".join(clean_lines).rstrip()
    is_valid = verify_data(clean_code.encode("utf-8"), signature, creator_identity)
    result = (creator_identity, is_valid)
    if cache_key is not None:
        _sig_cache_set(cache_key, result)
    return result

def sign_json(data: dict) -> dict:
    """Returns a copy of the dictionary with creator_identity and signature injected."""
    # Copy data and remove signature metadata keys to sign the core content
    content = data.copy()
    content.pop("creator_identity", None)
    content.pop("signature", None)
    
    # Canonical JSON string serialization
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":")).encode("utf-8")
    
    signature = sign_data(canonical)
    identity = get_creator_identity()
    
    signed_data = data.copy()
    signed_data["creator_identity"] = identity
    signed_data["signature"] = signature
    return signed_data

def verify_json(data: dict) -> Tuple[str, bool]:
    """Verifies a JSON dict's signature metadata. Returns (creator_identity, is_valid)."""
    identity = data.get("creator_identity")
    signature = data.get("signature")
    
    if not identity or not signature:
        return "", False
        
    # Strip metadata keys to verify the core content
    content = data.copy()
    content.pop("creator_identity", None)
    content.pop("signature", None)
    
    # Canonical JSON string serialization
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":")).encode("utf-8")
    
    is_valid = verify_data(canonical, signature, identity)
    return identity, is_valid
