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

import sys
import os
from pathlib import Path

# ComfyLAB Core Package Version
def _get_version():
    try:
        from importlib.metadata import version, PackageNotFoundError
        return version("comfylab")
    except (PackageNotFoundError, ImportError):
        pass
    for p in [Path(__file__).resolve().parent.parent / "VERSION", Path(__file__).resolve().parent / "VERSION"]:
        if p.exists():
            return p.read_text().strip()
    return "0.0.0"

__version__ = _get_version()

# Allow standalone executables to load external modules from comfylab/ next to sys.executable
if getattr(sys, 'frozen', False):
    ext_comfylab_dir = os.path.join(os.path.dirname(sys.executable), "comfylab")
    if os.path.exists(ext_comfylab_dir) and ext_comfylab_dir not in __path__:
        __path__.append(ext_comfylab_dir)
