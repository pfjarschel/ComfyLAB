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

import { useState } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';

const BACKEND_URL = 'http://localhost:8000';

interface DetectedPin {
  name: string;
  label: string;
  type: string;
  widget?: string;
  default?: any;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
  optional?: boolean;
  maps_to?: { block_id: string; pin: string };
  maps_from?: { block_id: string; pin: string };
}

interface DetectedBoundary {
  exec_ins: DetectedPin[];
  exec_outs: DetectedPin[];
  data_ins: DetectedPin[];
  data_outs: DetectedPin[];
}

interface CreateClusterModalProps {
  isOpen: boolean;
  detectedBoundary: DetectedBoundary;
  selectedBlockIds: string[];
  internalBlueprint: { blocks: any[]; links: any[] };
  hasActiveWorkspace: boolean;
  onClose: () => void;
  onCreated: (typeName: string, clusterNodeData: any) => void;
}

export const CreateClusterModal = ({
  isOpen,
  detectedBoundary,
  selectedBlockIds,
  internalBlueprint,
  hasActiveWorkspace,
  onClose,
  onCreated
}: CreateClusterModalProps) => {
  const [form, setForm] = useState({
    displayName: '',
    category: 'User/Clusters',
    icon: '📦',
    description: '',
    destination: 'global' as 'global' | 'workspace'
  });
  const [isPublishing, setIsPublishing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handlePublish = async () => {
    if (!form.displayName.trim()) {
      setError('Please enter a display name.');
      return;
    }

    setIsPublishing(true);
    setError(null);

    const boundaryPins: any = {
      exec_ins: [],
      exec_outs: [],
      data_ins: [],
      data_outs: []
    };

    detectedBoundary.exec_ins.forEach(pin => {
      boundaryPins.exec_ins.push({
        name: pin.name,
        maps_to: pin.maps_to
      });
    });

    // If no boundary exec_ins but internal blocks have exec flow, create a synthetic entry
    if (boundaryPins.exec_ins.length === 0 && internalBlueprint.blocks.length > 0) {
      const internalLinks: any[] = internalBlueprint.links || [];
      const execLinks = internalLinks.filter((l: any) => l.type === 'exec');
      if (execLinks.length > 0) {
        const targetsWithExecIn = new Set(execLinks.map((l: any) => `${l.target_block}/${l.target_pin}`));
        // Find the entry block: a block that sources exec links but is not a target of any exec link
        let entryNodeId: string | null = null;
        let entryPin = 'In';
        for (const link of execLinks) {
          if (!targetsWithExecIn.has(`${link.source_block}/`)) {
            // This source block is not a target of any exec link → it's an entry point
            // But we need its ExecIn pin name. Find it from blocks that ARE targets.
            // The source's exec out connects to a target. That target's ExecIn is the internal entry.
            // Wait — the source block IS the entry point. We need to map the cluster's ExecIn
            // to the first exec block's input.
          }
        }
        // Simpler: find a target that is NOT a source of any exec link going further
        // That's the real first exec block. Use it as the internal entry.
        const sources = new Set(execLinks.map((l: any) => l.source_block));
        for (const link of execLinks) {
          if (!sources.has(link.target_block)) {
            // This target receives exec but doesn't forward it further → it might be the first
            // Actually, we want the block that is NOT a target but IS a source → the real entry
          }
        }
        // Most reliable: find a source block that is never a target
        const allTargets = new Set(execLinks.map((l: any) => `${l.target_block}`));
        for (const block of internalBlueprint.blocks) {
          if (sources.has(block.id) && !allTargets.has(block.id)) {
            entryNodeId = block.id;
            break;
          }
        }
        // Fallback to first exec link's target
        if (!entryNodeId && execLinks.length > 0) {
          entryNodeId = execLinks[0].target_block;
          entryPin = execLinks[0].target_pin;
        }
        if (entryNodeId) {
          boundaryPins.exec_ins.push({
            name: 'In',
            maps_to: { block_id: entryNodeId, pin: entryPin }
          });
        }
      }
    }
    detectedBoundary.exec_outs.forEach(pin => {
      boundaryPins.exec_outs.push({
        name: pin.name,
        maps_from: pin.maps_from
      });
    });

    // If no boundary exec_outs but internal blocks have exec flow, create a synthetic exit
    if (boundaryPins.exec_outs.length === 0) {
      const internalLinks: any[] = internalBlueprint.links || [];
      const execLinks = internalLinks.filter((l: any) => l.type === 'exec');
      if (execLinks.length > 0) {
        const sources = new Set(execLinks.map((l: any) => l.source_block));
        // Terminal block: a target that is never a source
        let exitNodeId: string | null = null;
        let exitPin = 'Out';
        for (const link of execLinks) {
          if (!sources.has(link.target_block)) {
            exitNodeId = link.target_block;
            break;
          }
        }
        // Fallback: last exec link's source
        if (!exitNodeId) {
          exitNodeId = execLinks[execLinks.length - 1].source_block;
        }
        if (exitNodeId) {
          boundaryPins.exec_outs.push({
            name: 'Out',
            maps_from: { block_id: exitNodeId, pin: exitPin }
          });
        }
      }
    }
    detectedBoundary.data_ins.forEach(pin => {
      boundaryPins.data_ins.push({
        name: pin.name,
        type: pin.type,
        widget: pin.widget,
        default: pin.default,
        min_val: pin.min,
        max_val: pin.max,
        step: pin.step,
        options: pin.options,
        optional: pin.optional || false,
        maps_to: pin.maps_to
      });
    });
    detectedBoundary.data_outs.forEach(pin => {
      boundaryPins.data_outs.push({
        name: pin.name,
        type: pin.type,
        maps_from: pin.maps_from
      });
    });

    // Calculate bounding box of the blocks inside internalBlueprint
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    internalBlueprint.blocks.forEach((n: any) => {
      minX = Math.min(minX, n.position?.x ?? 0);
      minY = Math.min(minY, n.position?.y ?? 0);
      maxX = Math.max(maxX, (n.position?.x ?? 0) + (n.style?.width ?? 210));
      maxY = Math.max(maxY, (n.position?.y ?? 0) + (n.style?.minHeight ?? 160));
    });
    if (minX === Infinity) {
      minX = 0; minY = 0; maxX = 300; maxY = 300;
    }

    const finalNodes = [...internalBlueprint.blocks];
    const finalLinks = [...internalBlueprint.links];

    // Inject cluster/boundary/input blocks
    boundaryPins.exec_ins.forEach((ein: any, idx: number) => {
      const inputNodeId = `input_${ein.name}`;
      finalNodes.push({
        id: inputNodeId,
        type: 'cluster/boundary/input',
        position: { x: minX - 250, y: minY + idx * 120 },
        properties: {
          Name: ein.name,
          Type: 'exec',
          DataType: 'any'
        }
      });
      finalLinks.push({
        id: `link_${inputNodeId}_Out`,
        type: 'exec',
        source_block: inputNodeId,
        source_pin: 'Out',
        target_block: ein.maps_to.block_id,
        target_pin: ein.maps_to.pin
      });
      // Re-map boundary pin to point to the input block itself!
      ein.maps_to = { block_id: inputNodeId, pin: 'Out' };
    });

    boundaryPins.data_ins.forEach((din: any, idx: number) => {
      const inputNodeId = `input_${din.name}`;
      finalNodes.push({
        id: inputNodeId,
        type: 'cluster/boundary/input',
        position: { x: minX - 250, y: minY + (boundaryPins.exec_ins.length + idx) * 120 },
        properties: {
          Name: din.name,
          Type: 'data',
          DataType: din.type || 'any'
        }
      });
      finalLinks.push({
        id: `link_${inputNodeId}_Value`,
        type: 'data',
        source_block: inputNodeId,
        source_pin: 'Value',
        target_block: din.maps_to.block_id,
        target_pin: din.maps_to.pin
      });
      // Re-map boundary pin to point to the input block itself!
      din.maps_to = { block_id: inputNodeId, pin: 'Value' };
    });

    // Inject cluster/boundary/output blocks
    boundaryPins.exec_outs.forEach((eout: any, idx: number) => {
      const outputNodeId = `output_${eout.name}`;
      finalNodes.push({
        id: outputNodeId,
        type: 'cluster/boundary/output',
        position: { x: maxX + 100, y: minY + idx * 120 },
        properties: {
          Name: eout.name,
          Type: 'exec'
        }
      });
      finalLinks.push({
        id: `link_${outputNodeId}_In`,
        type: 'exec',
        source_block: eout.maps_from.block_id,
        source_pin: eout.maps_from.pin,
        target_block: outputNodeId,
        target_pin: 'In'
      });
      // Re-map boundary pin to point to the output block itself!
      eout.maps_from = { block_id: outputNodeId, pin: 'In' };
    });

    boundaryPins.data_outs.forEach((dout: any, idx: number) => {
      const outputNodeId = `output_${dout.name}`;
      finalNodes.push({
        id: outputNodeId,
        type: 'cluster/boundary/output',
        position: { x: maxX + 100, y: minY + (boundaryPins.exec_outs.length + idx) * 120 },
        properties: {
          Name: dout.name,
          Type: 'data'
        }
      });
      finalLinks.push({
        id: `link_${outputNodeId}_Value`,
        type: 'data',
        source_block: dout.maps_from.block_id,
        source_pin: dout.maps_from.pin,
        target_block: outputNodeId,
        target_pin: 'Value'
      });
      // Re-map boundary pin to point to the output block itself!
      dout.maps_from = { block_id: outputNodeId, pin: 'Value' };
    });

    try {
      const res = await axios.post(`${BACKEND_URL}/blocks/publish_cluster`, {
        display_name: form.displayName.trim(),
        category: form.category.trim() || 'User/Clusters',
        icon: form.icon.trim() || '📦',
        description: form.description.trim(),
        internal_blueprint: { blocks: finalNodes, links: finalLinks },
        boundary_pins: boundaryPins,
        destination: form.destination
      });

      if (res.data.success) {
        const prefix = form.destination === 'workspace' ? 'workspace/cluster' : 'user/cluster';
        const cleanName = form.displayName.trim().toLowerCase().replace(/[^a-z0-9\s_-]/g, '').replace(/[\s_-]+/g, '_');

        const clusterNodeData: any = {};
        detectedBoundary.data_ins.forEach(pin => {
          let val = pin.default;
          if (val === undefined || val === null) {
            if (pin.type === 'number') val = 0;
            else if (pin.type === 'boolean') val = false;
            else if (pin.type === 'text') val = '';
            else val = null;
          }
          clusterNodeData[pin.name] = val;
        });

        onCreated(`${prefix}/${cleanName}`, clusterNodeData);
        onClose();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to publish cluster.');
    } finally {
      setIsPublishing(false);
    }
  };

  return createPortal(
    <div className="modal-overlay" style={{ zIndex: 1000 }} onClick={onClose}>
      <div className="modal-content glass-panel" style={{ width: '520px', maxHeight: '90vh' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>📦</span> Group into Cluster
          </h3>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '16px 20px', overflowY: 'auto' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {selectedBlockIds.length} block{selectedBlockIds.length !== 1 ? 's' : ''} selected
          </div>

          <div className="input-group">
            <label>Display Name</label>
            <input
              type="text"
              placeholder="e.g. Laser Calibrator"
              value={form.displayName}
              onChange={(e) => setForm({ ...form, displayName: e.target.value })}
              style={{ background: 'var(--input-bg)', border: '1px solid var(--block-border)', color: 'var(--text-color)', padding: '8px', borderRadius: '6px' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <div className="input-group" style={{ flex: 1 }}>
              <label>Icon</label>
              <input
                type="text"
                value={form.icon}
                onChange={(e) => setForm({ ...form, icon: e.target.value })}
                style={{ background: 'var(--input-bg)', border: '1px solid var(--block-border)', color: 'var(--text-color)', padding: '8px', borderRadius: '6px', textAlign: 'center' }}
              />
            </div>
            <div className="input-group" style={{ flex: 2 }}>
              <label>Category</label>
              <input
                type="text"
                placeholder="User/Clusters"
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                style={{ background: 'var(--input-bg)', border: '1px solid var(--block-border)', color: 'var(--text-color)', padding: '8px', borderRadius: '6px' }}
              />
            </div>
          </div>

          <div className="input-group">
            <label>Description</label>
            <textarea
              placeholder="What does this cluster do?"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={2}
              style={{ background: 'var(--input-bg)', border: '1px solid var(--block-border)', color: 'var(--text-color)', padding: '8px', borderRadius: '6px', resize: 'vertical', fontFamily: 'inherit', fontSize: '0.85rem' }}
            />
          </div>

          <div className="input-group">
            <label>Destination</label>
            <select
              value={form.destination}
              onChange={(e) => setForm({ ...form, destination: e.target.value as 'global' | 'workspace' })}
              style={{ background: 'var(--input-bg)', border: '1px solid var(--block-border)', color: 'var(--text-color)', padding: '8px', borderRadius: '6px' }}
            >
              <option value="global">Global Library (~/.comfylab/user_clusters)</option>
              {hasActiveWorkspace && (
                <option value="workspace">Active Workspace (clusters/)</option>
              )}
            </select>
          </div>

          <div style={{ background: 'var(--input-bg)', border: '1px solid var(--block-border)', borderRadius: '6px', padding: '10px', fontSize: '0.75rem' }}>
            <div style={{ fontWeight: 600, marginBottom: '6px', color: 'var(--text-muted)' }}>Detected Boundary Pins</div>
            {detectedBoundary.data_ins.length === 0 && detectedBoundary.data_outs.length === 0 &&
             detectedBoundary.exec_ins.length === 0 && detectedBoundary.exec_outs.length === 0 && (
              <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>No external connections detected.</div>
            )}
            {detectedBoundary.data_ins.map(pin => (
              <div key={`in-${pin.name}`} style={{ color: '#f97316', margin: '2px 0' }}>⬅ Input: {pin.label} ({pin.type})</div>
            ))}
            {detectedBoundary.data_outs.map(pin => (
              <div key={`out-${pin.name}`} style={{ color: '#22c55e', margin: '2px 0' }}>➡ Output: {pin.label} ({pin.type})</div>
            ))}
            {detectedBoundary.exec_ins.map(pin => (
              <div key={`ein-${pin.name}`} style={{ color: '#a78bfa', margin: '2px 0' }}>⬅ Exec In: {pin.label}</div>
            ))}
            {detectedBoundary.exec_outs.map(pin => (
              <div key={`eout-${pin.name}`} style={{ color: '#a78bfa', margin: '2px 0' }}>➡ Exec Out: {pin.label}</div>
            ))}
          </div>

          {error && (
            <div style={{ color: '#ef4444', fontSize: '0.8rem', padding: '6px 10px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '4px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
              {error}
            </div>
          )}
        </div>

        <div className="modal-footer" style={{ display: 'flex', gap: '10px', padding: '12px 20px' }}>
          <button className="button-secondary" onClick={onClose} style={{ flex: 1 }}>Cancel</button>
          <button
            className="button-primary"
            onClick={handlePublish}
            disabled={isPublishing || !form.displayName.trim()}
            style={{ flex: 1.5, background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)' }}
          >
            {isPublishing ? 'Creating...' : '🚀 Create Cluster'}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
};
