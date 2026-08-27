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

import React from 'react';
import { getBlockTitle, getPinLabel } from '../../utils/blockI18n';
import { NumericTextInput } from '../common/NumericTextInput';

// Import monitor and display widgets
import { DisplayScreenWidget } from './DisplayScreenWidget';
import { TimePlotWidget } from './TimePlotWidget';
import { XYPlotWidget } from './XYPlotWidget';
import { HeatmapPlotWidget } from './HeatmapPlotWidget';
import { HistogramPlotWidget } from './HistogramPlotWidget';
import { DualYPlotWidget } from './DualYPlotWidget';
import { PolarPlotWidget } from './PolarPlotWidget';
import { BarPlotWidget } from './BarPlotWidget';
import { BoxPlotWidget } from './BoxPlotWidget';
import { Plot3DWidget } from './Plot3DWidget';
import { WaterfallPlotWidget } from './WaterfallPlotWidget';
import { TableViewWidget } from './TableViewWidget';
import { ImageDisplayWidget } from './ImageDisplayWidget';
import { ArrayDisplayWidget } from './ArrayDisplayWidget';

export interface DashboardItem {
  id: string;
  blockId: string;
  type: 'block' | 'pin';
  pinName?: string;
  order?: number;
}

export interface DashboardControlPinItem {
  itemId: string;
  pinName: string;
}

export interface DashboardControlGroup {
  id: string;
  blockId: string;
  pins: DashboardControlPinItem[];
  isConstantBlock?: boolean;
}

interface DashboardControlCardProps {
  group: DashboardControlGroup;
  block: any;
  layout?: any;
  onJumpToBlock: (blockId: string) => void;
  onRemovePin: (itemId: string) => void;
  onRemoveBlock: (blockId: string) => void;
  onMoveUp?: () => void;
  onMoveDown?: () => void;
  onBlockDataChange: (blockId: string, key: string, value: any) => void;
}

/**
 * Grouped Control Card: displays all pinned controls for a single block
 */
export const DashboardControlCard: React.FC<DashboardControlCardProps> = ({
  group,
  block,
  layout,
  onJumpToBlock,
  onRemovePin,
  onRemoveBlock,
  onMoveUp,
  onMoveDown,
  onBlockDataChange,
}) => {
  if (!block) return null;

  const data = block.data || {};
  const blockTitle = data.customName || (layout ? getBlockTitle(layout) : data.action || 'Block');
  const icon = layout?.icon || '⚙️';
  const status = data.status || 'idle';
  const statusColor = status === 'running' ? '#38bdf8' : status === 'success' ? '#10b981' : status === 'error' ? '#ef4444' : '#64748b';

  return (
    <div className="dashboard-card nodrag">
      <div className="dashboard-card-header">
        <div className="dashboard-card-info" title={blockTitle}>
          <span style={{ fontSize: '0.95rem' }}>{icon}</span>
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: statusColor,
              boxShadow: status === 'running' ? `0 0 6px ${statusColor}` : 'none',
              flexShrink: 0,
            }}
            title={`Status: ${status}`}
          />
          <span className="dashboard-card-title">{blockTitle}</span>
          {group.pins.length > 1 && (
            <span className="dashboard-badge" style={{ fontSize: '0.65rem', padding: '1px 6px' }}>
              {group.pins.length}
            </span>
          )}
        </div>
        <div className="dashboard-card-actions">
          {onMoveUp && (
            <button className="dashboard-icon-btn" onClick={onMoveUp} title="Move up">
              ▲
            </button>
          )}
          {onMoveDown && (
            <button className="dashboard-icon-btn" onClick={onMoveDown} title="Move down">
              ▼
            </button>
          )}
          <button className="dashboard-icon-btn" onClick={() => onJumpToBlock(block.id)} title="Locate on Canvas">
            🎯
          </button>
          <button className="dashboard-icon-btn" onClick={() => onRemoveBlock(block.id)} title="Remove from Dashboard">
            ✕
          </button>
        </div>
      </div>

      <div className="dashboard-card-body">
        {group.isConstantBlock ? (
          // Constant widget handling
          <div>
            {layout?.ui_behavior?.custom_widget === 'constant_boolean' ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 4px' }}>
                <span style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-color)' }}>
                  State: {data.value ? 'ON' : 'OFF'}
                </span>
                <div
                  className={`toggle-switch ${data.value ? 'active' : ''}`}
                  onClick={() => onBlockDataChange(block.id, 'value', !data.value)}
                  style={{
                    width: '48px',
                    height: '24px',
                    borderRadius: '12px',
                    background: data.value ? '#10b981' : '#334155',
                    position: 'relative',
                    cursor: 'pointer',
                    transition: 'background 0.2s',
                    boxShadow: data.value ? '0 0 10px rgba(16, 185, 129, 0.4)' : 'none',
                  }}
                >
                  <div
                    style={{
                      width: '18px',
                      height: '18px',
                      borderRadius: '50%',
                      background: '#ffffff',
                      position: 'absolute',
                      top: '3px',
                      left: data.value ? '27px' : '3px',
                      transition: 'left 0.2s ease',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.4)',
                    }}
                  />
                </div>
              </div>
            ) : layout?.ui_behavior?.custom_widget === 'constant_string' ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <input
                  type="text"
                  value={data.value ?? ''}
                  onChange={(e) => onBlockDataChange(block.id, 'value', e.target.value)}
                  style={{
                    padding: '6px 10px',
                    fontSize: '0.85rem',
                    background: 'var(--input-bg)',
                    border: '1px solid var(--block-border)',
                    borderRadius: '4px',
                    color: 'var(--text-color)',
                  }}
                />
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <NumericTextInput
                  value={data.value ?? 0}
                  onChange={(v) => onBlockDataChange(block.id, 'value', v)}
                  style={{
                    padding: '6px 10px',
                    fontSize: '1rem',
                    background: 'var(--input-bg)',
                    border: '1px solid var(--block-border)',
                    borderRadius: '4px',
                    color: 'var(--text-color)',
                  }}
                />
              </div>
            )}
          </div>
        ) : (
          <div className="dashboard-controls-list">
            {group.pins.map(({ itemId, pinName }) => {
              const pinSchema = layout?.dataIns?.find((p: any) => p.name === pinName);
              const pinLabel = layout ? getPinLabel(layout, pinName) : (pinSchema?.label || pinName);
              const pinType = pinSchema?.type || 'any';
              const pinWidget = pinSchema?.widget || (pinType === 'boolean' ? 'checkbox' : pinType === 'number' ? 'number' : 'text');
              let pinVal = data[pinName];
              if (pinVal === undefined) {
                pinVal = pinSchema?.defaultVal !== undefined ? pinSchema.defaultVal : (pinType === 'boolean' || pinWidget === 'checkbox' ? false : 0);
              }

              return (
                <div key={pinName} className="dashboard-pin-control-row">
                  <div className="dashboard-pin-control-header">
                    <span className="dashboard-pin-control-label" title={pinLabel}>
                      {pinLabel}
                    </span>
                    <button
                      className="dashboard-pin-remove-btn"
                      onClick={() => onRemovePin(itemId)}
                      title={`Remove ${pinLabel} from Dashboard`}
                    >
                      ✕
                    </button>
                  </div>

                  <div className="dashboard-pin-control-widget">
                    {pinWidget === 'checkbox' || pinType === 'boolean' ? (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '2px 0' }}>
                        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-color)' }}>
                          {pinVal ? 'ON' : 'OFF'}
                        </span>
                        <div
                          className={`toggle-switch ${pinVal ? 'active' : ''}`}
                          onClick={() => onBlockDataChange(block.id, pinName, !pinVal)}
                          style={{
                            width: '42px',
                            height: '22px',
                            borderRadius: '11px',
                            background: pinVal ? '#10b981' : '#334155',
                            position: 'relative',
                            cursor: 'pointer',
                            transition: 'background 0.2s',
                            boxShadow: pinVal ? '0 0 8px rgba(16, 185, 129, 0.4)' : 'none',
                          }}
                        >
                          <div
                            style={{
                              width: '16px',
                              height: '16px',
                              borderRadius: '50%',
                              background: '#ffffff',
                              position: 'absolute',
                              top: '3px',
                              left: pinVal ? '23px' : '3px',
                              transition: 'left 0.2s ease',
                              boxShadow: '0 1px 3px rgba(0,0,0,0.4)',
                            }}
                          />
                        </div>
                      </div>
                    ) : pinWidget === 'slider' ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-color)' }}>
                          <span style={{ color: 'var(--text-muted)' }}>Value:</span>
                          <span style={{ fontWeight: 600 }}>{pinVal}</span>
                        </div>
                        <input
                          type="range"
                          min={pinSchema?.min ?? 0}
                          max={pinSchema?.max ?? 100}
                          step={pinSchema?.step ?? 1}
                          value={pinVal}
                          onChange={(e) => onBlockDataChange(block.id, pinName, parseFloat(e.target.value))}
                          style={{ width: '100%' }}
                        />
                      </div>
                    ) : pinWidget === 'dropdown' ? (
                      <select
                        value={pinVal}
                        onChange={(e) => onBlockDataChange(block.id, pinName, e.target.value)}
                        style={{
                          width: '100%',
                          background: 'var(--input-bg)',
                          color: 'var(--text-color)',
                          border: '1px solid var(--block-border)',
                          padding: '5px 8px',
                          borderRadius: '4px',
                          fontSize: '0.8rem',
                        }}
                      >
                        {(pinSchema?.options || []).map((opt: string) => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    ) : (
                      <NumericTextInput
                        value={pinVal}
                        onChange={(v) => onBlockDataChange(block.id, pinName, v)}
                        min={pinSchema?.min}
                        max={pinSchema?.max}
                        style={{
                          width: '100%',
                          padding: '5px 8px',
                          fontSize: '0.85rem',
                          background: 'var(--input-bg)',
                          border: '1px solid var(--block-border)',
                          borderRadius: '4px',
                          color: 'var(--text-color)',
                        }}
                      />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

interface DashboardMonitorCardProps {
  item: DashboardItem;
  block: any;
  layout?: any;
  onJumpToBlock: (blockId: string) => void;
  onRemove: (itemId: string) => void;
  onMoveUp?: () => void;
  onMoveDown?: () => void;
  onBlockDataChange: (blockId: string, key: string, value: any) => void;
}

/**
 * Monitor Card: displays plots, tables, waveforms, and screens
 */
export const DashboardMonitorCard: React.FC<DashboardMonitorCardProps> = ({
  item,
  block,
  layout,
  onJumpToBlock,
  onRemove,
  onMoveUp,
  onMoveDown,
  onBlockDataChange,
}) => {
  if (!block) return null;

  const data = block.data || {};
  const blockTitle = data.customName || (layout ? getBlockTitle(layout) : data.action || 'Block');
  const icon = layout?.icon || '⚙️';
  const status = data.status || 'idle';
  const statusColor = status === 'running' ? '#38bdf8' : status === 'success' ? '#10b981' : status === 'error' ? '#ef4444' : '#64748b';

  const customWidget = layout?.ui_behavior?.custom_widget;

  const handlePlotLayoutChange = (newLayout: any) => {
    onBlockDataChange(block.id, 'plot_layout', newLayout);
  };

  return (
    <div className="dashboard-card nodrag">
      <div className="dashboard-card-header">
        <div className="dashboard-card-info" title={blockTitle}>
          <span style={{ fontSize: '0.95rem' }}>{icon}</span>
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: statusColor,
              boxShadow: status === 'running' ? `0 0 6px ${statusColor}` : 'none',
              flexShrink: 0,
            }}
            title={`Status: ${status}`}
          />
          <span className="dashboard-card-title">{blockTitle}</span>
        </div>
        <div className="dashboard-card-actions">
          {onMoveUp && (
            <button className="dashboard-icon-btn" onClick={onMoveUp} title="Move up">
              ▲
            </button>
          )}
          {onMoveDown && (
            <button className="dashboard-icon-btn" onClick={onMoveDown} title="Move down">
              ▼
            </button>
          )}
          <button className="dashboard-icon-btn" onClick={() => onJumpToBlock(block.id)} title="Locate on Canvas">
            🎯
          </button>
          <button className="dashboard-icon-btn" onClick={() => onRemove(item.id)} title="Remove from Dashboard">
            ✕
          </button>
        </div>
      </div>

      <div className="dashboard-card-body" style={{ minHeight: '120px' }}>
        {customWidget === 'display_area' && (
          <DisplayScreenWidget
            blockId={block.id}
            initialValue={data.results?.displayValue ?? data.results?.result}
          />
        )}

        {customWidget === 'time_plot' && (
          <div style={{ height: '220px', width: '100%' }}>
            <TimePlotWidget
              blockId={block.id}
              strokeColor="#34d399"
              dataKey="history"
              xLog={data.XLog}
              yLog={data.YLog}
              onChange={handlePlotLayoutChange}
              savedLayout={data.plot_layout}
            />
          </div>
        )}

        {customWidget === 'xy_plot' && (
          <div style={{ height: '220px', width: '100%' }}>
            <XYPlotWidget
              blockId={block.id}
              xLabel={data.results?.x_label}
              yLabel={data.results?.y_label}
              xLog={data.XLog}
              yLog={data.YLog}
              onChange={handlePlotLayoutChange}
              savedLayout={data.plot_layout}
            />
          </div>
        )}

        {customWidget === 'heatmap_plot' && (
          <div style={{ height: '240px', width: '100%' }}>
            <HeatmapPlotWidget
              blockId={block.id}
              xLabel={data.results?.x_label}
              yLabel={data.results?.y_label}
              onChange={handlePlotLayoutChange}
              savedLayout={data.plot_layout}
            />
          </div>
        )}

        {customWidget === 'histogram_plot' && (
          <div style={{ height: '220px', width: '100%' }}>
            <HistogramPlotWidget
              blockId={block.id}
              onChange={handlePlotLayoutChange}
              savedLayout={data.plot_layout}
            />
          </div>
        )}

        {customWidget === 'dual_y_plot' && (
          <div style={{ height: '220px', width: '100%' }}>
            <DualYPlotWidget
              blockId={block.id}
              onChange={handlePlotLayoutChange}
              savedLayout={data.plot_layout}
            />
          </div>
        )}

        {customWidget === 'polar_plot' && (
          <div style={{ height: '220px', width: '100%' }}>
            <PolarPlotWidget
              blockId={block.id}
              onChange={handlePlotLayoutChange}
              savedLayout={data.plot_layout}
            />
          </div>
        )}

        {customWidget === 'bar_plot' && (
          <div style={{ height: '220px', width: '100%' }}>
            <BarPlotWidget
              blockId={block.id}
              onChange={handlePlotLayoutChange}
              savedLayout={data.plot_layout}
            />
          </div>
        )}

        {customWidget === 'box_plot' && (
          <div style={{ height: '220px', width: '100%' }}>
            <BoxPlotWidget
              blockId={block.id}
              onChange={handlePlotLayoutChange}
              savedLayout={data.plot_layout}
            />
          </div>
        )}

        {customWidget === 'plot_3d' && (
          <div style={{ height: '240px', width: '100%' }}>
            <Plot3DWidget
              blockId={block.id}
              onChange={handlePlotLayoutChange}
              savedLayout={data.plot_layout}
            />
          </div>
        )}

        {customWidget === 'waterfall_plot' && (
          <div style={{ height: '240px', width: '100%' }}>
            <WaterfallPlotWidget
              blockId={block.id}
              onChange={handlePlotLayoutChange}
              savedLayout={data.plot_layout}
            />
          </div>
        )}

        {customWidget === 'table_view' && (
          <div style={{ height: '200px', width: '100%' }}>
            <TableViewWidget blockId={block.id} />
          </div>
        )}

        {customWidget === 'image_display' && (
          <div style={{ height: '200px', width: '100%' }}>
            <ImageDisplayWidget blockId={block.id} />
          </div>
        )}

        {customWidget === 'array_display' && (
          <ArrayDisplayWidget blockId={block.id} />
        )}

        {!customWidget && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <DisplayScreenWidget
              blockId={block.id}
              initialValue={data.results?.displayValue ?? data.results?.result}
            />
          </div>
        )}
      </div>
    </div>
  );
};
