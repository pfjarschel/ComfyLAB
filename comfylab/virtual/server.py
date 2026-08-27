# Copyright (C) 2026 Paulo Felipe Jarschel
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Standalone server process running the ComfyLAB Virtual Instruments suite.
Configured as an RC circuit experiment (inspired by SimVISA setup_RC.py):
- Port 51234: Virtual Oscilloscope (Ch1 = SigGen, Ch2 = RC Circuit output)
- Port 51235: Virtual Signal Generator
- Port 51236: Virtual RC Circuit
No GUI / Qt required. Pure Python + NumPy + SciPy.
"""

import sys
import time
import signal
import threading
import logging
from comfylab.virtual.signal_generator import VirtualSignalGenerator
from comfylab.virtual.rc_circuit import VirtualRCCircuit
from comfylab.virtual.oscilloscope import VirtualOscilloscope

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s"
)
logger = logging.getLogger("comfylab.virtual.server")


def main():
    logger.info("Initializing ComfyLAB Virtual Instruments Server...")

    # Create instruments
    sg = VirtualSignalGenerator(port=51235)
    rc = VirtualRCCircuit(port=51236)
    osc = VirtualOscilloscope(port=51234, ch1_source=sg, ch2_source=rc)
    rc.set_input_source(sg)

    # Start network listeners
    osc.start()
    sg.start()
    rc.start()

    logger.info("Virtual Instruments active and listening:")
    logger.info("  - Oscilloscope:       TCPIP0::127.0.0.1::51234::SOCKET (or VIRT::OSC)")
    logger.info("  - Signal Generator:   TCPIP0::127.0.0.1::51235::SOCKET (or VIRT::SIGGEN)")
    logger.info("  - RC Circuit:         TCPIP0::127.0.0.1::51236::SOCKET (or VIRT::RC)")

    stop_event = threading.Event()

    def _signal_handler(sig, frame):
        logger.info("Shutdown signal received. Stopping virtual instruments...")
        stop_event.set()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        while not stop_event.is_set():
            stop_event.wait(timeout=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Closing virtual instrument servers...")
        osc.close()
        sg.close()
        rc.close()
        logger.info("Virtual Instruments server terminated cleanly.")


if __name__ == "__main__":
    main()
