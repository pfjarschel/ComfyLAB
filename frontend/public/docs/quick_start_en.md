# ComfyLAB: Quick Start Guide & Comprehensive Overview
*Comfortable Lab Automation Blocks — User Manual, Software Overview & Hands-On Tutorial Reference*

---

## 1. Introduction & Philosophy

### 1.1 What is ComfyLAB?
**ComfyLAB** (**Comf**ortable **L**ab **A**utomation **B**locks) is an open-source, visual programming platform engineered specifically for scientific experiment automation, test & measurement, data acquisition (DAQ), and real-time visualization.

In modern research laboratories, automated measurement setups often require interfacing with diverse hardware (oscilloscopes, power supplies, multimeters, function generators, custom sensors) via various protocols (VISA, SCPI, Serial RS-232/RS-485, Ethernet, native C/C++ DLLs). Writing raw script-based automation in traditional languages frequently results in verbose, repetitive boilerplate code for loop management, thread safety, exception handling, data parsing, and GUI rendering.

ComfyLAB resolves this by providing a clean, modular graphical interface where users drag functional **Blocks** onto a digital canvas, connect them with visual **Wires**, and organize results into an instant, interactive **Dashboard**.

---

### 1.2 Dual Architecture: Web UI + Python Server Engine
ComfyLAB operates on a decoupled client-server model:
<div style="page-break-before: always; break-before: page;"></div>

```
┌──────────────────────────────────────────────────────────┐
│                      FRONT-END UI                        │
│ - Web Canvas (React + XY Flow)                           │
│ - Drag-and-Drop Block Placement & Wiring                 │
│ - Dedicated Operator Dashboard Cockpit (Hotkey: D)       │
│ - 2D & 3D Interactive Plotting & Data Displays           │
│ - Whiteboard Overlay & Freehand Annotations              │
└────────────────────────────┬─────────────────────────────┘
                             │ WebSocket / HTTP API
┌────────────────────────────▼─────────────────────────────┐
│                 BACKEND EXECUTION SERVER                 │
│ - Python Core Engine + API (FastAPI)                     │
│ - Push/Pull Hybrid State Machine Executor                │
│ - Physical VISA Hardware & Serial Lock Manager           │
│ - Built-in Virtual Instruments Server (SCPI Simulation)  │
│ - NumPy/SciPy Signal Processing & FFT Math               │
│ - Multi-Language Scripting & Native DLL / SO Invocation  │
└──────────────────────────────────────────────────────────┘
```

* **Front-End Canvas & Dashboard**: Runs in modern web browsers (or single-file Desktop app builds). Provides fluid graphical manipulation, auto-layout tools, interactive graph zoom/pan, a digital whiteboard layer, and a dedicated **Operator Dashboard** that displays pinned cards, controls, and monitors in a streamlined control-room layout.
* **Backend Server**: Powered by Python and FastAPI. Handles real-time hardware locks, VISA/SCPI queries, heavy matrix calculations, multi-threaded execution, file persistence, Python virtual environment management, and an automated background simulation server for **Virtual Instruments**.

---

### 1.3 Built-in Safety & Security

* **Instrument Protection & Safety Teardown**: Physical laboratory hardware (lasers, high-voltage power supplies, RF signal sources) requires strict safety management. If a measurement run encounters an error, is manually stopped, or experiences a connection loss, ComfyLAB automatically executes safe shutdown hooks to turn off active outputs and restore instruments to safe states.
* **Blueprint Security Verification**: When opening blueprints from external sources, ComfyLAB runs security checks to prevent unauthorized script execution, giving users full control and prompt verification before running custom code.
* **Secure Remote Access**: ComfyLAB supports secure remote operation over networks using token authentication, allowing researchers to safely monitor and control experiments running on lab computers from remote workstations.
* **In-App Version & Update Checker**: Built-in release manager in the *About* dialog automatically checks for updates on PyPI / GitHub, displaying release notes and allowing one-click upgrades.

<div style="page-break-before: always; break-before: page;"></div>

---

## 2. Capabilities & Flexibility: What Can (and Cannot) Be Done

ComfyLAB was built from the ground up to offer extreme flexibility without restricting advanced users to fixed GUI templates.

### 2.1 What Can Be Done with ComfyLAB

| Feature Area | Capabilities & Extensibility |
| :--- | :--- |
| **Physical Hardware Control** | Full support for **VISA** (GPIB, USB TMC, Ethernet/LXI, RS-232/RS-485 Serial) and **SCPI** standard command sets. Built-in driver blocks for popular commercial oscilloscopes, multimeters, power supplies, function generators, and Horiba spectrometers. |
| **Built-in Virtual Instruments** | Complete software-simulated laboratory instruments right out of the box! Includes a **Virtual Oscilloscope** (`virt_osc`) and **Virtual Signal Generator** (`virt_siggen`) connected to a simulated **RC Circuit** with realistic frequency response—enabling complete offline testing and education without any physical hardware. |
| **Operator Experiment Dashboard** | Dedicated **Dashboard View** (hotkey `D`). Pin any block, control parameter, or visualization widget to a sleek operator cockpit. Reorder and resize cards to create clean, presentation-ready control stations for experiment runs. |
| **Execution Progress & Timing** | Visual execution tracking with **Countdown Wait** (live digital clock, draining progress bar, and skip button), standalone **Progress Bar** widgets (0–100%), mission-control **ETR Displays** (Estimated Time Remaining), and smart loop blocks. |
| **Comprehensive Scientific Plots** | Real-time interactive 2D and 3D plotting: **XY / Line Plot** (single/multi-trace, log/linear), **Dual-Y Plot** (two distinct Y scales), **Bar Plot**, **Box Plot** (statistical distribution & outliers), **Histogram Plot**, **3D Surface & Scatter Plot**, **Polar Plot**, **Waterfall Spectral Plot**, and 2D Matrix Heatmaps. |
| **Native Library Invocation** | Directly call custom C/C++ compiled shared libraries (`.dll` on Windows, `.so` on Linux/macOS) using an interactive **Signature Editor** without writing Ctypes Python wrapper code. |
| **Multi-Language Custom Scripting** | Create inline **Script Blocks** in 9 programming languages: Python, Rust, JavaScript, TypeScript, Julia, R, Lua, Octave, and Wolfram. Access the `COMFYLAB_WORKSPACE` environment variable to read/write project files effortlessly. |
| **Python Ecosystem Access** | Connect custom script blocks to local Python virtual environments (`.venv`), providing full access to `scipy`, `numpy`, `pandas`, `opencv`, `scikit-learn`, `matplotlib`, and custom PyPI packages. |
| **Block Publishing & Package Bundles** | Publish custom script blocks directly to your sidebar palette or package entire workflows (with blueprints, scripts, and uploaded assets) into redistributable `.cfy` compressed package files. |
| **Advanced Signal Processing & Math** | High-performance NumPy array operations, FFT power spectrum analysis, curve fitting (Gaussian, Exponential, Polynomial, Custom non-linear), filtering (lowpass, highpass, bandpass), detrending, and peak detection. |
| **Modular Sub-Canvases (Clusters)** | Group complex sub-graphs into custom **Cluster Blocks** with dynamic input and output pins to maintain clean hierarchical blueprint diagrams. |
| **Whiteboard Canvas Overlay** | Add sticky notes, rich text, shapes, arrows, and freehand ink sketches directly on top of block canvas diagrams for presentation and documentation. Use shapes to visually group blocks together inside boundary rectangles. |

---

### 2.2 Realistic Limitations: What Cannot (or Should Not) Be Done

While ComfyLAB handles almost any scientific measurement, automation, and data processing task, it is helpful to recognize its domain boundary:

* **Hard Real-Time Microsecond Determinism**: ComfyLAB runs on standard OS kernels (Windows/Linux/macOS) via Python/FastAPI backends. It is designed for millisecond-level to sub-second automation loops, sensor sampling, and instrument control. It is **not** intended for bare-metal FPGA hardware logic or hard real-time sub-microsecond control loops (e.g., fast motor drive PWM switching at 100 kHz). For such tasks, hardware FPGAs or dedicated microcontroller RTOS boards should handle low-level timing, while ComfyLAB communicates with them over serial/USB for high-level control, buffering, and plotting.

> **Summary**: Outside of microsecond hardware FPGA determinism, **virtually any scientific measurement, lab automation, data logging, signal analysis, or plotting workflow can be built in ComfyLAB**.

<div style="page-break-before: always; break-before: page;"></div>

---

## 3. Comparison with Alternative Paradigms

Understanding how ComfyLAB compares to traditional lab software tools highlights why it is a compelling choice for both teaching and research.

| Feature / Aspect | Pure Python Scripts (PyVISA, Matplotlib) | National Instruments LabVIEW | MATLAB / Simulink | **ComfyLAB** |
| :--- | :--- | :--- | :--- | :--- |
| **License & Cost** | Free & Open Source | Expensive Commercial Licensing | Expensive Commercial Licensing | **Free & Open Source (GPLv3)** |
| **Programming Paradigm** | Text-based Code | Proprietary G Graphical Code | Text & Graphical Block Diagram | **Visual Web Block Diagrams + Polyglot Code** |
| **Learning Curve** | High (Requires programming proficiency) | Medium (Steep G language conventions) | Medium (Requires syntax & toolboxes) | **Low (Drag-and-drop intuitive canvas)** |
| **GUI & Plotting Setup** | Manual (PyQt, Tkinter, Matplotlib) | Integrated Front Panel | Integrated Figure Windows | **Instant Live Plotting, 3D/Polar/Waterfall & Dashboard** |
| **Offline Simulation** | Requires manual mock libraries | Basic software simulation | Simulink physical modeling | **Built-in Virtual SCPI Oscilloscope, SigGen & Circuit** |
| **File Format & Versioning**| Plain text `.py` (Git-friendly) | Proprietary Binary `.vi` (Difficult Git diffs) | `.m` / Proprietary `.slx` binary | **Clean JSON Blueprints (Git-friendly)** |
| **Custom Code Extension** | Native | Complex C/Python Call Nodes | S-Functions / MATLAB Code | **Inline Polyglot Script Blocks (Python, C/C++, Rust, etc.)** |
| **Architecture** | Single-threaded script / manual threads | Monolithic Desktop Application | Heavy Desktop Environment | **Modern Decoupled Web UI + FastAPI Server** |
| **Hardware Locking** | Manual lock implementation needed | Built-in VISA / DAQmx drivers | VISA / Instrument Control Toolbox | **Automated Asynchronous VISA Lock Manager** |

### Key Takeaways:
1. **Vs. Pure Python**: Python is powerful, but creating user interfaces, real-time interactive plots, hardware state loops, and visual workflows requires hundreds of lines of boilerplate code. ComfyLAB keeps Python's full analytical power while providing an immediate visual UI and experiment dashboard.
2. **Vs. LabVIEW**: LabVIEW is widely used but suffers from expensive commercial licenses, heavy proprietary binary files that break version control, and vendor lock-in. ComfyLAB offers a modern, open-source alternative with JSON-based blueprints, built-in virtual instruments, and seamless web browser integration.
3. **Vs. MATLAB**: MATLAB excels at matrix computations but carries heavy licensing costs. ComfyLAB leverages free, open-source NumPy/SciPy backends under the hood.

<div style="page-break-before: always; break-before: page;"></div>

---

## 4. Interface Layout & Core Concepts

### 4.1 Interface Layout Overview

The ComfyLAB user interface consists of three primary functional zones surrounded by top controls:

```
┌──────────────────────────────────────────────────────────────┐
│ TOP TOOLBAR: [🟰][⚙️] | [▶ Run/⏸ Pause] [🛑 Stop] | [📊 Dash] │
├────────────────┬──────────────────────────────┬──────────────┤
│ SIDEBAR        │ MAIN CANVAS AREA / DASHBOARD │ INSPECTOR    │
│ (Block Palette)│                              │ (Pin Values) │
│                │  ┌───────┐   Exec Wire       │              │
│ Search...      │  │ Entry │▶───┐              │ Inputs       │
│ Control Flow   │  └───────┘    │              │ Live Data    │
│ Math & Logic   │            ┌──▼────────────┐ │ Console Logs │
│ VISA / Virtual │ Data Wire  │ Math Block    │ │              │
│ Instruments    │ ──────────▶└───────────────┘ │              │
│ Visualization  │                              │              │
│                │ [Minimap]        [Tools 1-4] │              │
└────────────────┴──────────────────────────────┴──────────────┘
```

#### Detailed Interface Description:
* **Top Toolbar**: Controls for running (▶️ / `Ctrl+R`), pausing (⏸️), and stopping (🛑 / `Ctrl+Shift+R`) blueprints, opening the **Experiment Dashboard** (📊 / `D`), creating/saving workspace files (`Ctrl+S`), changing color themes, and configuring global VISA settings and diagnostics.
* **Sidebar (Left)**: Searchable palette containing all available built-in blocks, custom published blocks, virtual instrument blocks, and script nodes categorized by domain.
* **Main Canvas (Center)**: Infinite zoomable and pannable visual workspace where you drag, position, and wire functional blocks together.
* **Block Inspector (Right)**: Contextual detail panel that opens when a block is selected. Displays live pin values, block parameters, brief documentation, notes, and execution console logs.
* **Tab Bar & Breadcrumbs**: Navigate between open blueprint files and drill down into sub-canvas clusters.

<div style="page-break-before: always; break-before: page;"></div>
---

### 4.2 Pins & Wires: Execution Flow vs. Data Values

Connections between blocks in ComfyLAB are strictly divided into two distinct categories:

```
  Exec Out  ▶══════════════════════════════▶ Exec In
            (Violet Line: Controls WHEN blocks run)

  Data Out  ●──────────────────────────────● Data In
            (Solid Line: Transfers VALUES on demand)
```

1. **Execution Pins (Flow)**:
   * Represented by **arrow-shaped handles** and connected via **violet lines (🟪)**.
   * Dictate **sequential timing and control flow** (when steps execute, loops repeat, or branches trigger).

2. **Data Pins (Values)**:
   * Represented by **circular colored pins** and connected via **solid colored lines**.
   * Carry **values** (numbers, text strings, NumPy vectors, dictionaries, hardware handles).
   * Evaluated lazily on demand when an execution block requests input data.

#### Data Pin Color Reference:
* 🟧 **Number (Orange)**: Scalar integer or floating-point numerical values.
* 🟩 **Boolean (Green)**: Logical `True` or `False` flags.
* 🟪 **String (Pink)**: Text strings, formatted characters, or SCPI commands.
* 🟨 **Array (Yellow)**: High-performance 1D or 2D NumPy numerical arrays/vectors.
* 🟦 **List (Cyan)**: Ordered collections of elements.
* 🟫 **Dictionary (Brown)**: Key-value parameter mappings.

---

### 4.3 Execution Logic & Independent Chains
* **Execution Trigger**: Clicking **Run Blueprint** (▶️ or `Ctrl+R`) starts execution at entry blocks (blocks with no incoming execution connections) and follows execution wires downstream.
* **Independent Execution Chains**: If the canvas contains separate, unconnected block groups, ComfyLAB automatically treats them as parallel execution chains, allowing independent acquisition loops to run concurrently.
* **Control Flow & Timing Blocks**:
  * **For Loop**: Executes a sub-loop for a specified iteration count, outputting current index, completion percentage (`%`), and estimated time remaining (`ETR`).
  * **For Each Loop**: Iterates through each item in a list or array, providing item, index, percentage, and ETR outputs.
  * **While Loop**: Continually executes a sub-loop while a Boolean condition pin remains `True`.
  * **If / Else Branch**: Routes execution flow to either a `True` or `False` output path based on a condition.
  * **Delay / Sleep**: Pauses execution flow for a specified duration (ms or seconds).
  * **Countdown Wait**: Pauses execution for a specified duration with an active live countdown clock, draining progress bar, and interactive **Skip Wait** button.
  * **Progress Bar**: Standalone visual display widget for tracking live completion percentage (0–100%).
  * **ETR Display**: Mission-control digital readout for estimating and rendering remaining run durations (`HH:MM:SS` or `MM:SS`).
  * **Execution Timer (Measure Time)**: Measures exact wall-clock elapsed time between trigger pulses.

---

### 4.4 Advanced Features

* **Experiment Dashboard & Pinned Cards (📊 / `D`)**: The Dashboard provides a clean, distraction-free "operator cockpit" for running experiments, presenting results, or conducting student lab sessions without the visual complexity of block diagrams and wires.
  * **Pinning Blocks**: Any block or pin can be pinned to the Dashboard. Right-click a block and select **Pin to Dashboard**, click the pin icon in the Block Inspector header, or use the card pin icon on supported widgets.
  * **Automatic Organization**: Inputs, sliders, and constants are organized into interactive **Control Cards**, while graphs, gauges, indicators, and timers become dedicated **Monitor Cards**.
  * **Layout Customization**: Reorder cards up/down, drag corners to resize plots, toggle card controls, or click the jump icon to instantly navigate back to the corresponding canvas block.
  * **Maximized View**: Maximize the dashboard panel to fill the workspace for a streamlined full-screen lab control station.
* **Persistent Blocks (📌)**: By default, block states reset between execution runs. Marking a block as **Persistent** preserves its internal state and hardware handles (e.g., active VISA connections, open serial ports, or running averages) across multiple blueprint runs.
* **Disabling Blocks (🚫)**: Right-clicking a block to disable it dims the block on canvas. Disabled blocks are bypassed during execution, passing data through cleanly without running code—ideal for testing workflows without physical hardware.
* **Clusters (Sub-canvases 📦)**: Group complex block arrangements into a single custom block. Double-clicking a cluster block opens an isolated sub-canvas, with top breadcrumbs for navigation.
* **Whiteboard Mode (🎨)**: Click the tool icon or press hotkey `4` to toggle drawing mode, allowing freehand ink notes, text boxes, and shapes to be added directly over the canvas.

<div style="page-break-before: always; break-before: page;"></div>

---

## 5. Summary of Built-in Block Categories

| Category | Description & Common Blocks |
| :--- | :--- |
| 🔄 **Control Flow & Timing** | For Loop, For Each Loop, While Loop, If/Else Branch, Delay/Sleep, Countdown Wait, Execution Timer / Measure Time, Stop Execution. |
| 🔢 **Math & Logic** | Addition, Subtraction, Multiplication, Division, Formula Evaluator, Sine/Cosine, Trigonometry, Exponential, Logarithm, Comparisons (`>`, `<`, `==`), AND, OR, NOT logic. |
| 📝 **Data & Strings** | String Concatenate, Text Format, Regex Search, String Splitter, List Builder, List Indexer, Dictionary Builder, Key-Value Getter. |
| 📊 **Arrays & Signal** | Array Create, Range/Linspace, Array Slicing, FFT Power Spectrum, Lowpass/Bandpass Filters, Detrend, Statistics (Mean, Std, Min, Max), Peak Detector, Curve Fitting (Gaussian, Exponential, Polynomial, Custom non-linear). |
| 💾 **File I/O** | Read/Write CSV files, JSON I/O, Parquet storage, Text File Read/Write, Image Loader/Saver. |
| 📡 **VISA & Hardware** | VISA Resource Open, SCPI Write, SCPI Read, SCPI Query, VISA Close, Serial Port Open/Read/Write, VISA Resource Manager auto-discovery. |
| 🖥️ **Virtual Instruments** | **VirtOsc** (Connect, Timebase, Channel 1 & 2 Setup, Trigger, State, Acquire Waveform), **VirtSigGen** (Connect, Waveform Setup: Sine/Square/Triangle, Chirp Sweep, Output Level), Simulated RC Circuit. |
| 🔬 **Instrument Drivers** | Oscilloscopes (Tektronix, Keysight, Agilent), Digital Multimeters (HP/Agilent 34401A, Generic DMM), DC Power Supplies (Keysight, Keithley), Function Generators, Horiba Spectrometers, CAEN digitizers, Thorlabs motion/power. |
| 📈 **Display, Plots & UI** | **XY / Line Plot** (single/multi-trace, log/linear), **Dual-Y Plot**, **Bar Plot**, **Box Plot**, **Histogram Plot**, **3D Surface & Scatter Plot**, **Polar Plot**, **Waterfall Spectral Plot**, 2D Matrix Heatmap, Table Viewer, Gauge, Status/LED, **Progress Bar**, **ETR Display**, **Countdown Clock**. |
| ⚙️ **Native & Scripting** | Native Library (DLL/SO) Invocation with Signature Editor, Polyglot Script Node (Python, JS/TS, Julia, Rust, Lua, Octave, R, Wolfram) with `COMFYLAB_WORKSPACE` environment variable support. |

<div style="page-break-before: always; break-before: page;"></div>

---

## 6. Hands-On Starter Tutorials

Use these short, step-by-step exercises to get comfortable with ComfyLAB before or during your tutorial session.

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 1: Math Pipeline & Live Inspection
**Goal**: Create two numbers, multiply them, apply a mathematical formula, and inspect the result in the Block Inspector.

```
┌──────────────┐
│ Number (5.0) ├──┐   ┌───────────┐   ┌─────────────┐
│ Output Data  │  ├──▶│ Multiply  ├──▶│ Formula     ├──► Output
└──────────────┘  │   └───────────┘   │ "x^2 + 10"  │
┌──────────────┐  │                   └─────────────┘
│ Number (3.0) ├──┘
│ Output Data  │
└──────────────┘
```

#### Step-by-Step Instructions:
1. Open ComfyLAB and create a new workspace/blueprint.
2. In the left **Sidebar**, search for `Number` and drag **two** Number blocks onto the canvas.
3. Set the value of the first Number block to `5.0` and the second to `3.0`.
4. Drag a **Multiply** block (from *Math & Logic*) onto the canvas.
5. Connect the data output pin of Number 1 to Input A of the Multiply block, and Number 2 to Input B.
6. Drag a **Formula** block onto the canvas. Set its equation string parameter to `x^2 + 10`.
7. Connect the output pin of the Multiply block (`15.0`) to input `x` of the Formula block.
8. Click **Run Blueprint** (▶️ or `Ctrl+R`) on the top toolbar.
9. Click the **Formula** block to open the **Block Inspector** on the right sidebar.
10. **Verification**: In the Block Inspector, check the live output pin value. It should evaluate to `(15)^2 + 10 = 235.0`.

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 2: Synthetic Signal Generation & Live Plotting
**Goal**: Generate a noisy sine wave array, calculate its FFT power spectrum, and render it on an interactive plotter.

```
┌────────────────────┐     ┌────────────────────┐
│ Linspace (0 to 10s)├────▶│ Sine Wave Generator├─┐
└────────────────────┘     └────────────────────┘ │
                                                  ▼
┌────────────────────┐     ┌────────────────────┐ │
│ Interactive Chart  │◀────┤ Signal + Noise     │◀┘
└────────────────────┘     └─────────┬──────────┘
                                     │
                                     ▼
                           ┌────────────────────┐
                           │ FFT Power Spectrum │
                           └────────────────────┘
```

#### Step-by-Step Instructions:
1. Search for `Linspace` in the Sidebar. Set `Start = 0`, `Stop = 10`, `Points = 1000` to create a time vector array.
2. Search for `Sine` (under *Math & Logic* or *Arrays*). Connect the Linspace output to the time input of the Sine block. Set frequency parameter to `5.0 Hz`.
3. Add a **Random Noise** block and an **Add** block to corrupt the sine wave with white noise (`Signal + Noise`).
4. Drag an **Interactive Plotter** block onto the canvas.
5. Connect the time array to the **X Pin** of the Plotter and the noisy signal array to the **Y Pin**.
6. (Optional) Connect the noisy signal to an **FFT Spectrum** block, and wire the FFT output to a second trace on the Plotter.
7. Click **Run Blueprint** (▶️).
8. **Verification**: The Plotter widget on your canvas will immediately display the live noisy sine wave. Use your mouse wheel over the graph to zoom in/out and drag to pan across axes!

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 3: Automated Parameter Sweep & CSV Logging
**Goal**: Use a `For Loop` to simulate sweeping a power supply voltage, calculate power consumption, display the live curve, and log data to a CSV file.

```
┌─────────────────────┐    ┌────────────────────┐
│ For Loop (0 to 50)  │▶──▶│ CSV File Writer    │
└──────────┬──────────┘    └────────────────────┘
           │ (Index)
           ▼
┌─────────────────────┐
│ Voltage = Index*0.1 │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Current = V / R     ├─► Live Plotter
└─────────────────────┘
```

#### Step-by-Step Instructions:
1. Drag a **For Loop** block onto the canvas. 
2. Set the `For Loop` iterations count to `50`. Notice that the block also provides live `%` (percentage) and `ETR` output pins!
3. Inside the loop execution path, multiply the `Iteration Index` pin by `0.1` using a **Multiply** block to generate a voltage sweep from `0.0 V` to `5.0 V`.
4. Divide the voltage by a constant resistance (`R = 100 Ohms`) using a **Divide** block to calculate current `I`.
5. Connect both Voltage and Current values to a **CSV Writer** block. Set the filename option to `sweep_results.csv`.
6. Wire the output execution pin of the CSV block back to the loop step input to complete the iteration.
7. Click **Run Blueprint** (▶️).
8. **Verification**: Watch the loop run step-by-step with animated violet execution lines. After execution completes, open your active workspace folder—you will find `sweep_results.csv` populated with all 50 data rows!

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 4: Writing & Publishing a Custom Python Script Block
**Goal**: Create a custom Python script block that filters out values below a threshold, test it, and publish it to the left sidebar palette.

```
┌──────────────────────────────────────────────────┐
│ Custom Script Block (Python)                     │
│ Inputs:  data_in (Array), threshold (Number)     │
│ Outputs: filtered_data (Array), count (Number)   │
├──────────────────────────────────────────────────┤
│ arr = np.array(inputs['data_in'])                │
│ result = arr[arr > inputs['threshold']]          │
│ outputs['filtered_data'] = result.tolist()       │
│ outputs['count'] = len(result)                   │
└──────────────────────────────────────────────────┘
```

#### Step-by-Step Instructions:
1. Drag a **Script Block** (from *Scripting & Native*) onto the canvas. Select **Python** as the language.
2. In the **Block Inspector**, click **Edit Pins**:
   * Add Input Pin: `data_in` (Type: Array)
   * Add Input Pin: `threshold` (Type: Number)
   * Add Output Pin: `filtered_data` (Type: Array)
   * Add Output Pin: `count_passed` (Type: Number)
3. Double-click the Script Block to open the built-in code editor.
4. Enter the Python code snippet shown above. (Notice that `os.environ["COMFYLAB_WORKSPACE"]` is also available if your script needs local files!).
5. Connect a sample array to `data_in` and set `threshold = 2.5`.
6. Click **Run Blueprint** (▶️) and inspect `filtered_data` and `count_passed` in the Block Inspector.
7. Once verified, click **Publish Block** in the Block Inspector. Name it `Threshold Filter`, choose an icon, and assign it to the `Arrays` category.
8. **Verification**: Look at your left **Sidebar** palette. Your newly created `Threshold Filter` block is now permanently available to drag onto any canvas in your workspace!

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 5: VISA Hardware Interfacing (SCPI Identification Query)
**Goal**: Connect to a physical or simulated instrument over VISA, send an SCPI `*IDN?` query, and display the instrument model response.

```
┌───────────┐     ┌───────────┐     ┌───────────┐
│ VISA Open │▶───▶│ SCPI Query│▶───▶│ VISA Close│
│ Resource  ├────▶│ "*IDN?"   ├────▶│ Handle    │
└───────────┘     └─────┬─────┘     └───────────┘
                        │ Response String
                        ▼
                  [Block Inspector]
```

#### Step-by-Step Instructions:
1. Drag a **VISA Open** block onto the canvas. Set the Resource String parameter to your instrument address (e.g. `TCPIP0::192.168.1.100::INSTR`, `GPIB0::14::INSTR`, or `COM3`).
2. Drag a **SCPI Query** block. Connect the `ExecOut` of VISA Open to `ExecIn` of SCPI Query.
3. Connect the `VISA Handle` output pin (cyan handle pin) from VISA Open to the `VISA Handle` input of SCPI Query.
4. Set the command string parameter in SCPI Query to `*IDN?
`.
5. Drag a **VISA Close** block and wire the execution line and VISA handle to it to ensure clean resource release.
6. Click **Run Blueprint** (▶️).
7. **Verification**: Click the **SCPI Query** block and look at the Block Inspector. The output string pin will display the manufacturer identification string (e.g., `HEWLETT-PACKARD,34401A,0,11-5-2` or `KEYSIGHT TECHNOLOGIES,DSOX2002A,...`).
8. **Tip**: You can also take advantage of the VISA Resource Manager block to discover connected instruments automatically!

<div style="page-break-before: always; break-before: page;"></div>

---

### Tutorial 6: Offline Automation with Built-in Virtual Instruments
**Goal**: Connect to ComfyLAB's embedded virtual instruments, configure a simulated signal generator, capture a waveform with the virtual oscilloscope, and monitor the results on the Dashboard without any physical hardware.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ VirtSigGen Conn │▶───▶│ Config Wave     │▶───▶│ VirtOsc Connect │
│ (Virtual TCP)   ├────▶│ Freq: 1 kHz     │     │ (Virtual TCP)   │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Pin to          │◀────┤ XY Plot Widget  │◀────┤ Acquire Trace   │
│ Dashboard (D)   │     │ Time vs Volts   │     │ Channel 1 Data  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

#### Step-by-Step Instructions:
1. From the Sidebar, navigate to **Devices > Virtual**.
2. Drag a **VirtSigGen Connect** block and a **VirtSigGen Config Wave** block. Connect them to generate a 1.0 kHz sine wave at 2.0 Vpp.
3. Drag a **VirtOsc Connect** block and a **VirtOsc Acquire** block. Connect the execution flow and the device handles.
4. Drag an **XY Plot** block. Connect the oscilloscope's time array output to **X** and the voltage trace array to **Y**.
5. Right-click the **XY Plot** block and select **Pin to Dashboard**.
6. Press `D` on your keyboard (or click **Dashboard** in the top toolbar) to open the Operator Dashboard panel.
7. Click **Run Blueprint** (▶️ or `Ctrl+R`).
8. **Verification**: ComfyLAB will automatically spawn the background virtual instrument simulation server. The Operator Dashboard will immediately display the live captured waveform. You can also load the pre-built **Bode Diagram Virtual** workflow from **File Menu > Load Example > Bode_Diagram_Virtual.json** to see a full automated frequency sweep with Bode plots!

<div style="page-break-before: always; break-before: page;"></div>

---

## 7. Cheat Sheet & Keyboard Reference

### Hotkeys & Shortcuts

| Action | Shortcut | Description |
| :--- | :--- | :--- |
| **Toggle Dashboard** | `D` | Toggle the dedicated Operator Dashboard panel open or closed. |
| **Run / Pause / Resume** | `Ctrl + R` | Start blueprint execution, pause if running, or resume if paused. |
| **Stop Execution** | `Ctrl + Shift + R` | Immediately abort execution and trigger instrument safety teardown hooks. |
| **Duplicate Block(s)** | `Ctrl + D` | Duplicate currently selected blocks keeping settings intact. |
| **Select Tool** | `1` | Default mode to select, move blocks, and wire pins. |
| **Pan Tool** | `2` | Pan across the canvas without dragging blocks. |
| **Cut Wire Tool** | `3` | Slice across connected wires to quickly delete them. |
| **Whiteboard Tool** | `4` | Toggle drawing overlay for notes, shapes, and ink annotations. |
| **Pan Canvas** | `Space` + Drag | Hold spacebar and drag background to pan. |
| **Zoom Canvas** | `Mouse Wheel` | Scroll wheel to zoom in or out. |
| **Save Blueprint** | `Ctrl + S` | Save active blueprint layout to workspace JSON (`Ctrl + Shift + S` for Save As). |
| **Open Blueprint** | `Ctrl + O` | Open workspace blueprint dialog. |
| **Undo / Redo** | `Ctrl + Z` / `Ctrl + Y` | Undo or redo recent canvas actions. |
| **Copy / Paste** | `Ctrl + C` / `Ctrl + V` | Copy and paste selected blocks. |
| **Delete Block / Wire** | `Delete` or `Backspace` | Remove selected blocks or wires from canvas. |
| **Sub-canvas Navigation** | `Double Click Cluster` | Drill down into a Cluster sub-canvas. |

<div style="page-break-before: always; break-before: page;"></div>

---

## 8. Summary Checklist for Tutorial Session

Before starting your lab tutorial session, verify that:
* [ ] ComfyLAB is installed and launches successfully (`http://localhost:8000`).
* [ ] Active workspace folder is initialized.
* [ ] NI-VISA / PyVISA backends are detected if physical hardware testing is planned.
* [ ] Built-in Virtual Instruments work offline without any physical hardware (`Bode_Diagram_Virtual.json`).
* [ ] Operator Dashboard (`D`) is tested for presenting live graphs and parameter controls.
* [ ] Example blueprints in `src/comfylab/examples` are accessible for demonstration.

---
*ComfyLAB is released under the GNU General Public License v3.0 (GPLv3). Developed by Paulo Felipe Jarschel, GATE/EIT, IFGW, Unicamp.*
