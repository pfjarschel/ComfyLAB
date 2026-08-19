# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Horiba France / Jobin Yvon H20-UVL / VUV Excitation Monochromator System Driver.
Pure Python — no ComfyLAB UI or block dependencies.
"""

import time
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("comfylab.devices.horiba.vuv_excitation")


class HoribaGrating:
    """Represents a diffraction grating in a Horiba monochromator."""
    def __init__(self, grating_id: int = 0, lines: float = 1200.0, blaze: str = "250", description: str = "Standard VUV Grating"):
        self.id = grating_id
        self.lines = lines
        self.blaze = blaze
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "lines": self.lines,
            "blaze": self.blaze,
            "description": self.description
        }

    def __repr__(self) -> str:
        return f"Grating(id={self.id}, lines={self.lines} l/mm, blaze={self.blaze} nm, desc={self.description})"


class HoribaVUVExcitation:
    """
    Driver for Horiba Jobin Yvon H20-UVL and VUV Excitation Monochromators.
    Controls wavelength (nm), grating selection / turret, slit widths (mm), and mirror positions.
    Interfaces via win32com ActiveX/COM objects on Windows, or integrated high-fidelity simulation on Linux/other platforms.
    """

    def __init__(self, mono_id: str = "Mono5", simulate: bool = False, timeout: float = 10.0):
        self.mono_id = mono_id
        self.timeout = timeout
        self.simulate = simulate
        self.is_connected = False
        
        # State variables
        self._current_wavelength: float = 200.0
        self._current_turret: int = 0
        self._gratings: List[HoribaGrating] = [
            HoribaGrating(0, 1200.0, "200", "1200 l/mm VUV Holographic"),
            HoribaGrating(1, 2400.0, "150", "2400 l/mm High Resolution VUV"),
            HoribaGrating(2, 600.0, "300", "600 l/mm Broad Range")
        ]
        self._slit_widths: Dict[int, float] = {i: 0.5 for i in range(6)}  # Slits 0..5 in mm
        self._mirror_positions: Dict[int, int] = {0: 0, 1: 0}  # Mirror 0 (Entrance), Mirror 1 (Exit): 0=Front, 1=Side
        
        # COM objects
        self._config_browser = None
        self._mono_obj = None

    def initialize(self, force_init: bool = False, emulate: bool = False) -> bool:
        """
        Initializes communication with Horiba Monochromator Manager / COM interface.
        If ActiveX is not present or simulate=True, activates simulation mode.
        """
        if self.simulate or emulate:
            logger.info("Initializing Horiba VUV Monochromator in simulation mode.")
            self.is_connected = True
            return True

        try:
            import win32com.client  # type: ignore
            try:
                self._config_browser = win32com.client.Dispatch("JYConfigBrowserComponent.JYConfigBrowerInterface.1")
                self._config_browser.Load()
            except Exception as e:
                logger.warning(f"Could not load Horiba JYConfigBrowser: {e}. Falling back to simulation.")
                self.simulate = True
                self.is_connected = True
                return True

            self._mono_obj = win32com.client.Dispatch("JYMono.Monochromator.1")
            self._mono_obj.Uniqueid = self.mono_id
            self._mono_obj.Load()
            self._mono_obj.OpenCommunications()
            self._mono_obj.Initialize(force_init, emulate)

            t0 = time.time()
            while not self._mono_obj.InitializeComplete and (time.time() - t0 < self.timeout):
                time.sleep(0.1)

            self.is_connected = True
            self.get_gratings()
            return True
        except Exception as e:
            logger.warning(f"ActiveX COM initialization failed: {e}. Switching to simulation mode.")
            self.simulate = True
            self.is_connected = True
            return True

    def get_gratings(self) -> List[HoribaGrating]:
        """Returns list of configured gratings."""
        if not self.simulate and self._mono_obj:
            try:
                curr_dens, densities, blazes, descriptions = self._mono_obj.GetCurrentGratingWithDetails()
                grat_list = []
                for i in range(len(densities)):
                    grat_list.append(HoribaGrating(i, float(densities[i]), str(blazes[i]), str(descriptions[i])))
                if grat_list:
                    self._gratings = grat_list
            except Exception as e:
                logger.warning(f"Error fetching gratings from hardware: {e}")
        return self._gratings

    def get_current_grating_turret(self) -> int:
        """Queries current grating turret index."""
        if not self.simulate and self._mono_obj:
            try:
                self._current_turret = int(self._mono_obj.GetCurrentTurret())
            except Exception as e:
                logger.warning(f"Error querying turret: {e}")
        return self._current_turret

    def set_current_grating_turret(self, turret_index: int) -> None:
        """Moves monochromator to target grating turret index."""
        turret_index = max(0, min(int(turret_index), len(self._gratings) - 1))
        self._current_turret = turret_index

        if not self.simulate and self._mono_obj:
            try:
                self._mono_obj.MovetoTurret(turret_index)
                t0 = time.time()
                while self._mono_obj.IsBusy() and (time.time() - t0 < self.timeout):
                    time.sleep(0.05)
            except Exception as e:
                logger.error(f"Error moving to turret {turret_index}: {e}")

    def get_current_wavelength(self) -> float:
        """Queries current wavelength in nanometers (nm)."""
        if not self.simulate and self._mono_obj:
            try:
                val = float(self._mono_obj.GetCurrentWavelength())
                unit = self._mono_obj.GetDefaultUnits(1)
                # Normalize units to nm
                if unit == 1:
                    val = val * 1e6
                elif unit == 2:
                    val = val * 1e3
                elif unit == 4:
                    val = val / 10.0
                elif unit == 5:
                    val = val / 1e3
                self._current_wavelength = val
            except Exception as e:
                logger.warning(f"Error querying wavelength: {e}")
        return self._current_wavelength

    def set_wavelength(self, wl_nm: float) -> None:
        """Moves monochromator to target wavelength in nanometers (nm)."""
        wl_clamped = max(0.0, float(wl_nm))
        self._current_wavelength = wl_clamped

        if not self.simulate and self._mono_obj:
            try:
                self._mono_obj.MovetoWavelength(wl_clamped)
                t0 = time.time()
                while self._mono_obj.IsBusy() and (time.time() - t0 < self.timeout):
                    time.sleep(0.05)
            except Exception as e:
                logger.error(f"Error moving to wavelength {wl_nm} nm: {e}")

    def get_slit_width(self, slit_index: int = 0) -> float:
        """
        Gets slit width in millimeters (mm).
        Slit indices:
          0: Front Entrance, 1: Side Entrance
          2: Front Exit,     3: Side Exit
          4: First Interm.,  5: Second Interm.
        """
        s_idx = max(0, min(int(slit_index), 5))
        if not self.simulate and self._mono_obj:
            try:
                val = float(self._mono_obj.GetCurrentSlitWidth(s_idx))
                unit = self._mono_obj.GetDefaultUnits(2)
                if unit == 2:
                    val = val / 1e3
                elif unit == 3:
                    val = val / 1e6
                self._slit_widths[s_idx] = val
            except Exception as e:
                logger.warning(f"Error querying slit {s_idx}: {e}")
        return self._slit_widths.get(s_idx, 0.5)

    def set_slit_width(self, slit_index: int = 0, width_mm: float = 0.5) -> None:
        """Sets slit width in millimeters (mm)."""
        s_idx = max(0, min(int(slit_index), 5))
        w_val = max(0.0, min(float(width_mm), 10.0))
        self._slit_widths[s_idx] = w_val

        if not self.simulate and self._mono_obj:
            try:
                self._mono_obj.MovetoSlitPosition(s_idx, w_val)
                t0 = time.time()
                while self._mono_obj.IsBusy() and (time.time() - t0 < self.timeout):
                    time.sleep(0.05)
            except Exception as e:
                logger.error(f"Error setting slit {s_idx} width: {e}")

    def get_mirror_position(self, mirror_index: int = 0) -> int:
        """
        Gets mirror position (0: Front, 1: Side).
        Mirror indices: 0: Entrance Mirror, 1: Exit Mirror.
        """
        m_idx = max(0, min(int(mirror_index), 1))
        if not self.simulate and self._mono_obj:
            try:
                self._mirror_positions[m_idx] = int(self._mono_obj.GetCurrentMirrorPosition(m_idx))
            except Exception as e:
                logger.warning(f"Error querying mirror {m_idx}: {e}")
        return self._mirror_positions.get(m_idx, 0)

    def set_mirror_position(self, mirror_index: int = 0, position: int = 0) -> None:
        """Sets mirror position (0: Front, 1: Side)."""
        m_idx = max(0, min(int(mirror_index), 1))
        pos_val = 1 if int(position) == 1 else 0
        self._mirror_positions[m_idx] = pos_val

        if not self.simulate and self._mono_obj:
            try:
                self._mono_obj.MovetoMirrorPosition(m_idx, pos_val)
                t0 = time.time()
                while self._mono_obj.IsBusy() and (time.time() - t0 < self.timeout):
                    time.sleep(0.05)
            except Exception as e:
                logger.error(f"Error setting mirror {m_idx} position: {e}")

    def close(self) -> None:
        """Closes connection to monochromator."""
        if not self.simulate and self._mono_obj:
            try:
                self._mono_obj.CloseCommunications()
            except Exception:
                pass
        self.is_connected = False
