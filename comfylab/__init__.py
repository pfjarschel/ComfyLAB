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

# ComfyLAB Core Package
__version__ = "0.1.0"

# Allow standalone executables to load external modules from comfylab/ next to sys.executable
if getattr(sys, 'frozen', False):
    ext_comfylab_dir = os.path.join(os.path.dirname(sys.executable), "comfylab")
    if os.path.exists(ext_comfylab_dir) and ext_comfylab_dir not in __path__:
        __path__.append(ext_comfylab_dir)

