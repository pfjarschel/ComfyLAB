/*
 * Copyright (C) 2026 Paulo Felipe Jarschel
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 */

import React, { useEffect, useState, useRef } from 'react';

interface QuickStartModalProps {
  onClose: () => void;
}

export const QuickStartModal: React.FC<QuickStartModalProps> = ({ onClose }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSection, setActiveSection] = useState('intro');
  const bodyRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const scrollToSection = (id: string) => {
    setActiveSection(id);
    const element = document.getElementById(`qs-section-${id}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const sections = [
    { id: 'intro', title: '1. Introduction & Philosophy', icon: '🚀' },
    { id: 'usage', title: '2. Basic Usage & Workspaces', icon: '⚡' },
    { id: 'pins', title: '3. Execution vs. Data Pins', icon: '🔌' },
    { id: 'execution', title: '4. Execution & Control Flow', icon: '🔄' },
    { id: 'inspector', title: '5. Block Inspector', icon: '🔍' },
    { id: 'canvas-tools', title: '6. Canvas Tools & Modes', icon: '🛠️' },
    { id: 'whiteboard', title: '7. Whiteboard Mode', icon: '🎨' },
    { id: 'persistent', title: '8. Persistent Blocks', icon: '📌' },
    { id: 'disabling', title: '9. Disabling Blocks', icon: '🚫' },
    { id: 'clusters', title: '10. Clusters & Sub-canvases', icon: '📦' },
    { id: 'categories', title: '11. Available Block Categories', icon: '🧩' },
    { id: 'visualization', title: '12. Viewing Data & Plotting', icon: '📊' },
    { id: 'datatypes', title: '13. Lists, Arrays & Dictionaries', icon: '🔢' },
    { id: 'visa', title: '14. VISA Hardware Interface', icon: '📡' },
    { id: 'instruments', title: '15. Instrument Library', icon: '🔬' },
    { id: 'dll-so', title: '16. DLL / SO Native Libraries', icon: '⚙️' },
    { id: 'scripts', title: '17. Script Blocks & Python Venv', icon: '📜' },
    { id: 'publishing', title: '18. Publishing Custom Blocks', icon: '⬆️' },
    { id: 'packages', title: '19. Packages (.cfy)', icon: '🎁' },
    { id: 'advanced', title: '20. Advanced Backend Extension', icon: '💻' },
    { id: 'shortcuts', title: '21. Quick Tips & Shortcuts', icon: '⌨️' },
  ];

  const matchesSearch = (text: string) => {
    if (!searchQuery.trim()) return true;
    return text.toLowerCase().includes(searchQuery.toLowerCase());
  };

  return (
    <div
      className="modal-overlay"
      style={{ zIndex: 10000 }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        className="modal-content glass-panel"
        style={{
          maxWidth: '960px',
          width: '92vw',
          height: '85vh',
          display: 'flex',
          flexDirection: 'column',
          animation: 'scaleUp 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="modal-header"
          style={{
            padding: '16px 24px',
            borderBottom: '1px solid var(--block-border)',
            background: 'var(--input-bg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '1.6rem' }}>📖</span>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-color)' }}>
                ComfyLAB Quick Start Guide
              </h3>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Complete reference & user manual for visual lab automation
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Search Filter Input */}
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                placeholder="Search guide..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  padding: '6px 12px 6px 30px',
                  borderRadius: '20px',
                  border: '1px solid var(--block-border)',
                  background: 'var(--dnd-bg)',
                  color: 'var(--text-color)',
                  fontSize: '0.85rem',
                  width: '180px',
                  outline: 'none',
                }}
              />
              <span
                style={{
                  position: 'absolute',
                  left: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  fontSize: '0.85rem',
                  opacity: 0.6,
                }}
              >
                🔍
              </span>
            </div>

            <button className="modal-close-btn" onClick={onClose} title="Close guide">
              ✕
            </button>
          </div>
        </div>

        {/* Modal Main Content (Split Layout: Nav Sidebar + Main Body) */}
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* Quick Nav Sidebar */}
          <div
            style={{
              width: '240px',
              minWidth: '240px',
              borderRight: '1px solid var(--block-border)',
              background: 'var(--input-bg)',
              padding: '12px 8px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
            }}
          >
            <div
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                padding: '4px 8px 8px 8px',
              }}
            >
              Table of Contents
            </div>
            {sections.map((sec) => {
              const isActive = activeSection === sec.id;
              return (
                <button
                  key={sec.id}
                  onClick={() => scrollToSection(sec.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    border: 'none',
                    background: isActive ? 'var(--accent-color)' : 'transparent',
                    color: isActive ? '#ffffff' : 'var(--text-color)',
                    fontSize: '0.82rem',
                    fontWeight: isActive ? 600 : 400,
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) e.currentTarget.style.background = 'var(--dnd-bg)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <span style={{ fontSize: '0.95rem' }}>{sec.icon}</span>
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {sec.title}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Guide Content Scroll Area */}
          <div
            ref={bodyRef}
            style={{
              flex: 1,
              padding: '24px 32px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '28px',
              lineHeight: 1.6,
              color: 'var(--text-color)',
            }}
          >
            {/* 1. Introduction */}
            {matchesSearch('Introduction Philosophy Server Paradigm') && (
              <section id="qs-section-intro" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">🚀</span>
                  <h4>1. Introduction & Philosophy</h4>
                </div>
                <p>
                  <strong>ComfyLAB</strong> (<em>Comfortable Lab Automation Blocks</em>) is a visual programming environment created specifically for laboratory instrument automation, data acquisition, and scientific measurement workflows.
                </p>
                <p>
                  Instead of writing repetitive boilerplate code for serial ports, VISA instruments, or data loops, ComfyLAB lets you build modular, interactive <strong>Blueprints</strong> by dragging and connecting graphical functional blocks on a digital canvas.
                </p>
                <div className="qs-callout info">
                  <strong>The Server Paradigm:</strong> ComfyLAB operates on a dual architecture split between a responsive user interface and a background execution server. The front-end canvas gives you fluid graphical controls, while the backend execution server handles real-time hardware communication, heavy matrix operations, external script execution, and file persistence.
                </div>
              </section>
            )}

            {/* 2. Basic Usage */}
            {matchesSearch('Basic Usage UI Elements Dragging Blocks Workspaces Philosophy') && (
              <section id="qs-section-usage" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">⚡</span>
                  <h4>2. Basic Usage & Workspaces</h4>
                </div>
                <p>Getting started with ComfyLAB involves a few core interface elements:</p>
                <ul>
                  <li><strong>Sidebar (Block Palette):</strong> Located on the left. Search and drag blocks directly onto the main canvas.</li>
                  <li><strong>Canvas Area:</strong> The main visual editor where you drag, position, and wire blocks together.</li>
                  <li><strong>Block Inspector:</strong> Opens on the right when a block is clicked. Allows inspecting live data pin values, block options, and console output.</li>
                  <li><strong>Top Toolbar:</strong> Controls for running (▶️), pausing (⏸️), and stopping (🛑) blueprints, as well as managing blueprints (`New`, `Save`, `Load`), changing global settings (⚙️), and switching color themes.</li>
                  <li><strong>Tab Bar & Breadcrumbs:</strong> Switch between open blueprint tabs or navigate deep cluster hierarchies.</li>
                </ul>

                <h5 className="qs-subsection-title">2.1 Workspaces Philosophy</h5>
                <p>
                  ComfyLAB uses a <strong>Workspace folder</strong> as the central home for your project. Everything associated with your experiment lives inside the active workspace directory:
                </p>
                <div className="qs-grid-2">
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">📂 Saved Blueprints</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      JSON blueprint files containing canvas layouts and block connections.
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">🧩 Custom Script Blocks (`blocks/`)</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      User-created script blocks and published custom library blocks.
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">📁 Uploaded Files (`uploads/`)</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Data files, calibration tables, CSVs, or images uploaded to the workspace.
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">⚙️ Temporary Files (`.temp/`)</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Temporary outputs generated during package previews and execution.
                    </p>
                  </div>
                </div>
                <div className="qs-callout tip" style={{ marginTop: '12px' }}>
                  <strong>💡 Python Environments:</strong> Virtual Python environment configurations are managed in your local application directory (<code>.comfylab</code>), keeping workspace folders lightweight and easy to transfer between computers.
                </div>
              </section>
            )}

            {/* 3. Pins & Wires */}
            {matchesSearch('Execution Data Pins Wires Edges Flow Values Colors') && (
              <section id="qs-section-pins" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">🔌</span>
                  <h4>3. Execution vs. Data Pins (Wires)</h4>
                </div>
                <p>
                  Block connections in ComfyLAB are strictly divided into two distinct categories: <strong>Execution Pins</strong> and <strong>Data Pins</strong>.
                </p>
                <div className="qs-grid-2" style={{ marginTop: '12px' }}>
                  <div className="qs-subcard highlight-exec">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, marginBottom: '6px', color: 'var(--text-color)' }}>
                      <span style={{ color: '#a78bfa', fontSize: '1.1rem' }}>▶️</span> Execution Pins (Flow)
                    </div>
                    <p style={{ margin: 0, fontSize: '0.85rem' }}>
                      Represented as <strong>arrow handles</strong> and connected via <strong>violet animated lines (<code>#a78bfa</code>)</strong>.
                    </p>
                    <p style={{ margin: '8px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Execution wires dictate <strong>when</strong> blocks run. Execution travels sequentially step-by-step along these wires during blueprint runs.
                    </p>
                  </div>
                  <div className="qs-subcard highlight-data">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, marginBottom: '6px', color: 'var(--text-color)' }}>
                      <span style={{ color: '#3b82f6', fontSize: '1.1rem' }}>●</span> Data Pins (Values)
                    </div>
                    <p style={{ margin: 0, fontSize: '0.85rem' }}>
                      Represented as <strong>circular colored pins</strong> and connected via <strong>solid wires</strong>.
                    </p>
                    <p style={{ margin: '8px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Data wires carry <strong>values</strong> (numbers, text, arrays, dictionaries, VISA hardware handles) automatically when computed.
                    </p>
                  </div>
                </div>

                <h5 className="qs-subsection-title" style={{ marginTop: '16px' }}>Color Guide for Data Pins</h5>
                <div className="qs-grid-3">
                  <div className="qs-subcard" style={{ borderLeft: '4px solid #f97316' }}>
                    <strong style={{ color: '#f97316' }}>Number (Orange):</strong> Numeric values (int, float)
                  </div>
                  <div className="qs-subcard" style={{ borderLeft: '4px solid #22c55e' }}>
                    <strong style={{ color: '#22c55e' }}>Boolean (Green):</strong> True / False flags
                  </div>
                  <div className="qs-subcard" style={{ borderLeft: '4px solid #ec4899' }}>
                    <strong style={{ color: '#ec4899' }}>String / Text (Pink):</strong> Text strings
                  </div>
                  <div className="qs-subcard" style={{ borderLeft: '4px solid #e5a50a' }}>
                    <strong style={{ color: '#e5a50a' }}>Array (Yellow):</strong> NumPy 1D/2D numerical vectors
                  </div>
                  <div className="qs-subcard" style={{ borderLeft: '4px solid #06b6d4' }}>
                    <strong style={{ color: '#06b6d4' }}>List (Cyan):</strong> Ordered item collections
                  </div>
                  <div className="qs-subcard" style={{ borderLeft: '4px solid #795548' }}>
                    <strong style={{ color: '#795548' }}>Dictionary (Brown):</strong> Key-value parameter maps
                  </div>
                </div>
              </section>
            )}

            {/* 4. Execution Logic */}
            {matchesSearch('Execution Logic Control Flow Loops Branching If Else While For') && (
              <section id="qs-section-execution" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">🔄</span>
                  <h4>4. Execution Logic & Control Flow</h4>
                </div>
                <p>
                  When you click <strong>Run Blueprint</strong> (▶️), execution begins at initial entry blocks (blocks with no incoming execution connections) and follows execution wires downstream.
                </p>
                <h5 className="qs-subsection-title">Independent Block Groups</h5>
                <p>
                  If your canvas contains multiple separate groups of connected blocks that are not wired to each other, ComfyLAB automatically treats them as <strong>independent execution chains</strong>. They run independently, making it easy to create parallel acquisition loops or decoupled measurement routines.
                </p>
                <h5 className="qs-subsection-title">Control Flow Blocks</h5>
                <ul>
                  <li><strong>For Loop:</strong> Repeats a sub-execution loop a fixed number of times, outputting the current iteration index.</li>
                  <li><strong>While Loop:</strong> Continually executes a sub-loop as long as its Boolean condition pin evaluates to <code>True</code>.</li>
                  <li><strong>If / Else Branch:</strong> Routes execution to either the True output or False output pin based on an input Boolean condition.</li>
                  <li><strong>Delay / Sleep:</strong> Pauses execution flow for a user-specified duration in milliseconds or seconds.</li>
                </ul>
              </section>
            )}

            {/* 5. Block Inspector */}
            {matchesSearch('Block Inspector Parameters Inputs Logs Summary') && (
              <section id="qs-section-inspector" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">🔍</span>
                  <h4>5. How to Better Understand a Block (The Block Inspector)</h4>
                </div>
                <p>
                  Selecting any block on the canvas opens the <strong>Block Inspector</strong> panel on the right sidebar. The inspector is your primary tool for monitoring pin states and debugging:
                </p>
                <div className="qs-grid-2">
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">⚙️ Pin Configuration</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Inspect input and output pins, data types, and connection mappings. Parameters are set directly on the block widgets on the canvas.
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">📊 Live Data Inspection</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      View the latest calculated values at input and output data pins in real time.
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">📜 Brief Description</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Read a concise summary of the block's functionality and purpose.
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">📋 Console & Error Logs</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Inspect print statements, warnings, and error messages generated during execution.
                    </p>
                  </div>
                </div>
              </section>
            )}

            {/* 6. Canvas Tools */}
            {matchesSearch('Canvas Tools Navigation Zoom Pan Layout Minimap Selection Modes 1 2 3 4') && (
              <section id="qs-section-canvas-tools" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">🛠️</span>
                  <h4>6. Canvas Tools & Interactive Modes</h4>
                </div>
                <p>Navigate and interact with your visual blueprints using canvas tools and keyboard shortcuts:</p>
                
                <div className="qs-grid-2">
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">1 - Select Tool (Hotkey: <code>1</code>)</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Standard selection mode. Drag to box-select multiple blocks, reposition nodes, or click pins to draw wires.
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">2 - Pan Canvas Tool (Hotkey: <code>2</code>)</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Pan mode for navigating large canvas diagrams easily without accidentally moving blocks.
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">3 - Cut Wire Tool (Hotkey: <code>3</code>)</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Slice tool to quickly cut and remove connections by dragging a line across wires.
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">4 - Draw / Annotation Tool (Hotkey: <code>4</code>)</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Toggles Whiteboard drawing mode to draw ink lines, notes, and shapes over the blueprint.
                    </p>
                  </div>
                </div>

                <h5 className="qs-subsection-title" style={{ marginTop: '16px' }}>Additional Navigation Features</h5>
                <ul>
                  <li><strong>Zoom & Pan:</strong> Scroll mouse wheel to zoom in/out, or hold <code>Space</code> + drag background to pan.</li>
                  <li><strong>Minimap:</strong> Located in the bottom-right corner for fast overview navigation.</li>
                  <li><strong>Auto-Layout:</strong> Automatically organizes messy blocks into clean, structured pipelines.</li>
                </ul>
              </section>
            )}

            {/* 7. Whiteboard Mode */}
            {matchesSearch('Whiteboard Mode Annotations Drawings Notes Text Shapes Canvas Overlay Hide') && (
              <section id="qs-section-whiteboard" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">🎨</span>
                  <h4>7. Whiteboard Mode & Annotations</h4>
                </div>
                <p>
                  ComfyLAB includes a dedicated <strong>Whiteboard Mode</strong> layer designed for documentation, note-taking, and presentation:
                </p>
                <ul>
                  <li><strong>Toggle Overlay:</strong> Press <code>4</code> or click the Whiteboard button on the canvas toolbar to enter Whiteboard mode.</li>
                  <li><strong>Annotation Tools:</strong> Add sticky notes, rich text labels, rectangles, circles, arrows, and freehand ink sketches anywhere over your blocks.</li>
                  <li><strong>Hide Whiteboard Annotations:</strong> Toggle the Whiteboard hide button to temporarily hide drawings and annotations so you can view your block canvas cleanly.</li>
                  <li><strong>Saved with Blueprint:</strong> All whiteboard annotations are automatically saved and loaded alongside your blueprint files.</li>
                </ul>
              </section>
            )}

            {/* 8. Persistent Blocks */}
            {matchesSearch('Persistent Blocks Connection State Memory Retention Hardware Handles') && (
              <section id="qs-section-persistent" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">📌</span>
                  <h4>8. Persistent Blocks</h4>
                </div>
                <p>
                  Normally, block states are reset each time a blueprint run starts. However, certain hardware or stateful operations need to stay open across multiple consecutive runs.
                </p>
                <div className="qs-callout info">
                  <strong>Why Use Persistent Blocks?</strong> Marking a block as <strong>Persistent</strong> (via right-click or in the Block Inspector) preserves its internal state and active resource handles between executions. This is essential for:
                  <ul style={{ margin: '6px 0 0 0', paddingLeft: '20px' }}>
                    <li><strong>VISA Instrument Connections:</strong> Keeps physical instrument communication sessions open so devices don't have to re-initialize on every run.</li>
                    <li><strong>Serial Ports & Cameras:</strong> Maintains active streaming connections.</li>
                    <li><strong>Accumulators & Counters:</strong> Retains running averages or total counts across executions.</li>
                  </ul>
                </div>
              </section>
            )}

            {/* 9. Disabling Blocks */}
            {matchesSearch('Disabling Blocks Bypass Mute Test Troubleshooting') && (
              <section id="qs-section-disabling" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">🚫</span>
                  <h4>9. Disabling Blocks</h4>
                </div>
                <p>
                  You can disable any block without deleting it or rewiring your canvas:
                </p>
                <ul>
                  <li>Right-click a block and select <strong>Disable Block</strong> (or toggle in the Block Inspector).</li>
                  <li>Disabled blocks appear dimmed on the canvas.</li>
                  <li>During execution, disabled blocks are completely bypassed—execution flow skips over them, and data values pass through unchanged where possible.</li>
                  <li>This is ideal for temporarily disabling hardware write operations during testing or isolating sub-sections of a complex workflow.</li>
                </ul>
              </section>
            )}

            {/* 10. Clusters */}
            {matchesSearch('Clusters Sub-canvases Grouping Sub-routines Breadcrumbs Ports') && (
              <section id="qs-section-clusters" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">📦</span>
                  <h4>10. Clusters (Sub-canvases)</h4>
                </div>
                <p>
                  As blueprints grow, they can become crowded. <strong>Clusters</strong> allow you to group multiple blocks into a single modular block with custom input and output ports:
                </p>
                <ol>
                  <li>Select the group of blocks you wish to collapse.</li>
                  <li>Click <strong>Group into Cluster</strong> in the top toolbar or right-click context menu.</li>
                  <li>Give your cluster a title. ComfyLAB creates a neat cluster block with defined input and output pins matching the external wires.</li>
                  <li><strong>Drill Down:</strong> Double-click the cluster block to open its isolated sub-canvas. Use the top <strong>Breadcrumb Bar</strong> to step back up to the main blueprint canvas.</li>
                </ol>
              </section>
            )}

            {/* 11. Overview of Available Blocks */}
            {matchesSearch('Overview Available Blocks Categories Palette Library') && (
              <section id="qs-section-categories" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">🧩</span>
                  <h4>11. Comprehensive Overview of Block Categories</h4>
                </div>
                <p>ComfyLAB includes a rich palette of built-in blocks categorized by function:</p>
                <div className="qs-grid-2">
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">🔄 Control Flow</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      For Loop, While Loop, If/Else, Delay, Stop execution.
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">🔢 Math & Logic</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Basic arithmetic, trigonometry, Formula evaluation, Comparisons, AND/OR/NOT logic.
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">📝 Data & Strings</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      String formatters, regex search, text splitters, List & Dictionary builders/getters.
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">📊 Arrays & Signal Processing</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Array creation, slicing, FFT power spectrum, peak detection, statistics (mean, std, min, max).
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">💾 File I/O</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Read/Write CSV, JSON, and Parquet data files, image loader and saver.
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">📡 VISA & Hardware</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      VISA Open, Read, Write, Query, SCPI commands, Serial Port communication.
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">🔬 Instrument Drivers</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Pre-built blocks for Oscilloscopes, Multimeters, Power Supplies, Function Generators.
                    </p>
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">📈 Display & UI</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Real-time Plotters, Image Viewers, Gauges, Digital Displays, Table Views.
                    </p>
                  </div>
                </div>
              </section>
            )}

            {/* 12. Viewing Data */}
            {matchesSearch('Viewing Data Plotting Displaying Images Plotter Table CSV Parquet') && (
              <section id="qs-section-visualization" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">📊</span>
                  <h4>12. Viewing Data: Plotting, Saving, and Displays</h4>
                </div>
                <p>ComfyLAB provides rich visual display widgets directly embedded inside blocks:</p>
                <ul>
                  <li><strong>Interactive Plotter Block:</strong> Renders 1D array signals or multi-channel XY data as live interactive charts. Supports zoom, pan, cursor inspection, and exporting high-resolution images or CSV raw data.</li>
                  <li><strong>Image Viewer Block:</strong> Displays 2D matrix arrays, camera frames, heatmaps, and image files directly on the canvas.</li>
                  <li><strong>Table Viewer Block:</strong> Renders multi-column numerical or text tabular data in a clean grid format.</li>
                  <li><strong>File Exporters:</strong> Automatically write measured waveforms and data structures to CSV, JSON, or Parquet files as your experiment runs.</li>
                </ul>
              </section>
            )}

            {/* 13. Data Types */}
            {matchesSearch('List Array Dict Differences Data Types Vectors') && (
              <section id="qs-section-datatypes" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">🔢</span>
                  <h4>13. Understanding Data Types: Lists vs. Arrays vs. Dictionaries</h4>
                </div>
                <p>To use data processing blocks effectively, keep these three main collection types in mind:</p>
                <div className="qs-grid-3">
                  <div className="qs-subcard" style={{ borderLeft: '4px solid #06b6d4' }}>
                    <div className="qs-subcard-title" style={{ color: '#06b6d4' }}>List</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Ordered sequence of items of any type. Useful for general collections or lists of string responses.
                    </p>
                  </div>
                  <div className="qs-subcard" style={{ borderLeft: '4px solid #e5a50a' }}>
                    <div className="qs-subcard-title" style={{ color: '#e5a50a' }}>Array (NumPy)</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      High-performance numerical vector or matrix. Used for signal processing, waveforms, FFTs, and plotting.
                    </p>
                  </div>
                  <div className="qs-subcard" style={{ borderLeft: '4px solid #795548' }}>
                    <div className="qs-subcard-title" style={{ color: '#795548' }}>Dictionary</div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Key-value pairs (e.g. <code>&#123;"voltage": 5.0, "status": "OK"&#125;</code>). Perfect for structured settings & metadata.
                    </p>
                  </div>
                </div>
              </section>
            )}

            {/* 14. VISA */}
            {matchesSearch('VISA Virtual Instrument Software Architecture GPIB USB TCPIP Serial') && (
              <section id="qs-section-visa" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">📡</span>
                  <h4>14. VISA (Virtual Instrument Software Architecture)</h4>
                </div>
                <p>
                  ComfyLAB integrates seamlessly with standard VISA hardware libraries (such as NI-VISA, Keysight VISA, or PyVISA) to communicate with physical test equipment.
                </p>
                <h5 className="qs-subsection-title">Supported Resource Formats</h5>
                <ul>
                  <li><code>TCPIP0::192.168.1.100::INSTR</code> (LXI / Ethernet network instruments)</li>
                  <li><code>GPIB0::14::INSTR</code> (GPIB bus instruments)</li>
                  <li><code>USB0::0x0957::0x0407::MY1234567::INSTR</code> (USBTMC instruments)</li>
                  <li><code>ASRL1::INSTR</code> or <code>COM3</code> (Serial RS-232 / RS-485 connections)</li>
                </ul>
                <div className="qs-callout tip">
                  <strong>💡 Hardware Settings:</strong> In Global Settings (⚙️), you can select your VISA backend (National Instruments, PyVISA-py, Keysight), set default timeouts (ms), and configure write/read termination characters (`\n` or `\r\n`).
                </div>
              </section>
            )}

            {/* 15. Instrument Library */}
            {matchesSearch('Instrument Library Driver SCPI Oscilloscope Multimeter Power Supply') && (
              <section id="qs-section-instruments" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">🔬</span>
                  <h4>15. Instrument Library</h4>
                </div>
                <p>
                  In addition to raw VISA SCPI command blocks, ComfyLAB includes a dedicated <strong>Instrument Driver Library</strong> with pre-configured blocks for popular commercial instruments:
                </p>
                <ul>
                  <li>Oscilloscopes (waveform acquisition, channel setup, trigger controls)</li>
                  <li>Digital Multimeters (DMM voltage, current, resistance readings)</li>
                  <li>DC Power Supplies (voltage/current limit setting, output enable/disable)</li>
                  <li>Function / Arbitrary Waveform Generators (frequency, amplitude, waveform type)</li>
                </ul>
              </section>
            )}

            {/* 16. DLL / SO */}
            {matchesSearch('DLL SO Native Libraries Shared Libraries C C++ Signature Editor') && (
              <section id="qs-section-dll-so" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">⚙️</span>
                  <h4>16. Native Libraries (DLL / SO)</h4>
                </div>
                <p>
                  If you have proprietary C/C++ vendor drivers or compiled library files (<code>.dll</code> on Windows, <code>.so</code> on Linux), ComfyLAB allows direct invocation without writing Python wrappers:
                </p>
                <ol>
                  <li>Add a <strong>Library Call Block</strong> to your canvas.</li>
                  <li>Select your library file path and target function name.</li>
                  <li>Open the <strong>Signature Editor</strong> to define function argument types (e.g. <code>int32</code>, <code>double</code>, <code>pointer</code>, <code>string</code>) and return values.</li>
                  <li>ComfyLAB automatically generates matching input and output data pins on the block!</li>
                </ol>
              </section>
            )}

            {/* 17. Script Blocks */}
            {matchesSearch('Script Blocks Languages Python JavaScript Requirements Virtual Environment Venv') && (
              <section id="qs-section-scripts" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">📜</span>
                  <h4>17. Script Blocks & Python Virtual Environments</h4>
                </div>
                <p>
                  When built-in blocks aren't enough, you can create custom <strong>Script Blocks</strong> using Python or JavaScript directly inside the app:
                </p>
                <ul>
                  <li><strong>Custom Pins:</strong> Define any number of input and output data pins with custom names and types.</li>
                  <li><strong>Embedded Code Editor:</strong> Edit script logic with full syntax highlighting.</li>
                  <li><strong>External Python Venv:</strong> You can configure ComfyLAB to use an external Python virtual environment (managed in your local <code>.comfylab</code> folder). This allows your script blocks to import third-party packages like <code>scipy</code>, <code>pandas</code>, <code>opencv</code>, or <code>scikit-learn</code> seamlessly!</li>
                </ul>
              </section>
            )}

            {/* 18. Publishing Script Blocks */}
            {matchesSearch('Publishing Script Blocks Custom Palette Reusable Sharing') && (
              <section id="qs-section-publishing" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">⬆️</span>
                  <h4>18. Publishing Custom Script Blocks</h4>
                </div>
                <p>
                  Once you build and test a useful custom script block, you can <strong>Publish</strong> it to your workspace library:
                </p>
                <ol>
                  <li>In the Block Inspector for your script block, click <strong>Publish Block</strong>.</li>
                  <li>Provide a block name, icon, category, and descriptive summary.</li>
                  <li>Your block will immediately appear in the left Sidebar palette under your chosen category!</li>
                  <li>Published blocks can now be dragged onto any canvas in your workspace just like native blocks.</li>
                </ol>
              </section>
            )}

            {/* 19. Packages */}
            {matchesSearch('Packages Creating Distributing Opening Installing Zip cfy') && (
              <section id="qs-section-packages" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">🎁</span>
                  <h4>19. Packages (.cfy)</h4>
                </div>
                <p>
                  ComfyLAB supports self-contained <strong>Packages</strong> (<code>.cfy</code> files) for sharing complete measurement setups, published custom blocks, and data assets with colleagues:
                </p>
                <ul>
                  <li><strong>Creating a Package:</strong> Export your active blueprint along with all custom script blocks, files, and dependencies into a single compressed <code>.cfy</code> package file.</li>
                  <li><strong>Installing a Package:</strong> Double-click or use <code>Upload Package</code> to import a <code>.cfy</code> package into your workspace.</li>
                  <li><strong>Trust & Security:</strong> ComfyLAB automatically verifies packages before installation, prompting you to review contained scripts and assets before loading.</li>
                </ul>
              </section>
            )}

            {/* 20. Advanced Extension */}
            {matchesSearch('Advanced Extending Creating Blocks Scratch Python Backend Code') && (
              <section id="qs-section-advanced" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">💻</span>
                  <h4>20. Advanced: Extending ComfyLAB (Backend Blocks)</h4>
                </div>
                <p>
                  For software developers who want to extend ComfyLAB natively without using canvas script blocks:
                </p>
                <ul>
                  <li>Native blocks are written in Python under the backend structure (<code>backend/blocks/</code>).</li>
                  <li>Use the standard block class inheritance and decorators (e.g. <code>@block</code>) to define pin schemas, execution logic, and metadata.</li>
                  <li>Native blocks automatically register on server startup and offer maximum execution performance and hardware access.</li>
                </ul>
              </section>
            )}

            {/* 21. Quick Tips & Shortcuts */}
            {matchesSearch('Quick Tips Shortcuts Keyboard References Hotkeys 1 2 3 4') && (
              <section id="qs-section-shortcuts" className="qs-card">
                <div className="qs-section-header">
                  <span className="qs-icon">⌨️</span>
                  <h4>21. Quick Tips & Keyboard Shortcuts</h4>
                </div>
                <div className="qs-grid-2">
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">Tools 1-4</div>
                    <code>1</code> Select &nbsp;|&nbsp; <code>2</code> Pan &nbsp;|&nbsp; <code>3</code> Cut Wire &nbsp;|&nbsp; <code>4</code> Draw
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">File Operations</div>
                    <code>Ctrl + S</code> Save &nbsp;|&nbsp; <code>Ctrl + O</code> Open
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">Undo / Redo</div>
                    <code>Ctrl + Z</code> Undo &nbsp;|&nbsp; <code>Ctrl + Y</code> Redo
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">Block Editing</div>
                    <code>Ctrl + C</code> / <code>Ctrl + V</code> Copy / Paste &nbsp;|&nbsp; <code>Delete</code> Delete
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">Canvas Navigation</div>
                    <code>Space + Drag</code> Pan &nbsp;|&nbsp; <code>Mouse Wheel</code> Zoom
                  </div>
                  <div className="qs-subcard">
                    <div className="qs-subcard-title">Cluster Sub-canvases</div>
                    <code>Double Click Cluster</code> Drill down into sub-canvas
                  </div>
                </div>
              </section>
            )}
          </div>
        </div>

        {/* Footer */}
        <div
          className="modal-footer"
          style={{
            padding: '12px 24px',
            borderTop: '1px solid var(--block-border)',
            background: 'var(--input-bg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Need more help? Visit the official <a href="https://github.com/pfjarschel/ComfyLAB" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-color)', textDecoration: 'underline' }}>ComfyLAB GitHub repository</a>.
          </div>
          <button className="button-primary" onClick={onClose} style={{ padding: '8px 20px', borderRadius: '6px' }}>
            Got it! 👍
          </button>
        </div>
      </div>

      {/* Embedded Modern Styling for Quick Start Guide Modal */}
      <style>{`
        .qs-card {
          background: var(--dnd-bg);
          border: 1px solid var(--block-border);
          border-radius: 10px;
          padding: 22px 26px;
          display: flex;
          flex-direction: column;
          gap: 14px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .qs-section-header {
          display: flex;
          align-items: center;
          gap: 10px;
          border-bottom: 1px solid var(--block-border);
          padding-bottom: 12px;
          margin-bottom: 4px;
        }
        .qs-section-header h4 {
          margin: 0;
          font-size: 1.3rem;
          font-weight: 800;
          color: var(--text-color);
          letter-spacing: -0.2px;
        }
        .qs-subsection-title {
          margin: 16px 0 8px 0;
          font-size: 1.05rem;
          font-weight: 700;
          color: var(--text-color);
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .qs-subsection-title::before {
          content: '';
          display: inline-block;
          width: 4px;
          height: 14px;
          background: var(--accent-color);
          border-radius: 2px;
        }
        .qs-icon {
          font-size: 1.4rem;
        }
        .qs-grid-2 {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 14px;
        }
        .qs-grid-3 {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 14px;
        }
        .qs-subcard {
          background: var(--input-bg);
          border: 1px solid var(--block-border);
          border-radius: 8px;
          padding: 14px 16px;
          font-size: 0.88rem;
          color: var(--text-color);
        }
        .qs-subcard-title {
          font-weight: 700;
          font-size: 0.95rem;
          color: var(--text-color);
          margin-bottom: 4px;
        }
        .highlight-exec {
          border-left: 4px solid #a78bfa;
        }
        .highlight-data {
          border-left: 4px solid #3b82f6;
        }
        .qs-callout {
          border-radius: 8px;
          padding: 14px 18px;
          font-size: 0.88rem;
          line-height: 1.5;
        }
        .qs-callout.info {
          background: rgba(59, 130, 246, 0.1);
          border: 1px solid rgba(59, 130, 246, 0.3);
          color: var(--text-color);
        }
        .qs-callout.tip {
          background: rgba(16, 185, 129, 0.1);
          border: 1px solid rgba(16, 185, 129, 0.3);
          color: var(--text-color);
        }
      `}</style>
    </div>
  );
};
