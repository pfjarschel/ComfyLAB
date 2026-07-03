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

export interface NodeSchema {
  name: string;
  icon: string;
  execIns: string[];
  execOuts: string[];
  dataIns: { 
    name: string; 
    label: string; 
    defaultVal?: any; 
    type?: string; 
    widget?: string; 
    min?: number; 
    max?: number; 
    step?: number; 
    options?: string[]; 
    optional?: boolean;
  }[];
  dataOuts: { name: string; label: string; type?: string }[];
  original_code?: string;
  isPassthrough?: boolean;
}

export const getPinColor = (type: string | undefined): string => {
  switch (type) {
    case 'number':
      return '#f97316'; // Orange (LabVIEW numeric)
    case 'boolean':
      return '#22c55e'; // Green (LabVIEW boolean)
    case 'text':
    case 'string':
      return '#ec4899'; // Pink (LabVIEW string)
    case 'list':
    case 'array':
      return '#06b6d4'; // Cyan (LabVIEW arrays/waveform)
    case 'any':
    default:
      return '#64748b'; // Neutral slate gray for generic/unspecified types
  }
};

export const NODE_LAYOUTS: Record<string, NodeSchema> = {
  'constants/number': {
    name: 'Number',
    icon: '#️⃣',
    execIns: [],
    execOuts: [],
    dataIns: [],
    dataOuts: [{ name: 'Value', label: 'Value', type: 'number' }]
  },
  'math/arithmetic/add': {
    name: 'Add',
    icon: '➕',
    execIns: [],
    execOuts: [],
    dataIns: [
      { name: 'A', label: 'A', defaultVal: 0.0, type: 'number' },
      { name: 'B', label: 'B', defaultVal: 0.0, type: 'number' }
    ],
    dataOuts: [{ name: 'Result', label: 'Result', type: 'number' }]
  },
  'logic/compare': {
    name: 'Compare',
    icon: '⚖️',
    execIns: [],
    execOuts: [],
    dataIns: [
      { name: 'A', label: 'A', defaultVal: 0.0, type: 'number' },
      { name: 'B', label: 'B', defaultVal: 0.0, type: 'number' }
    ],
    dataOuts: [{ name: 'Result', label: 'Result', type: 'boolean' }]
  },
  'outputs/basic/print': {
    name: 'Print',
    icon: '🖨️',
    execIns: ['In'],
    execOuts: ['Out'],
    dataIns: [{ name: 'Value', label: 'Value', defaultVal: '', type: 'text' }],
    dataOuts: []
  },
  'control_flow/basic/if_else': {
    name: 'If/Else',
    icon: '🔀',
    execIns: ['In'],
    execOuts: ['True', 'False'],
    dataIns: [{ name: 'Condition', label: 'Condition', defaultVal: false, type: 'boolean' }],
    dataOuts: []
  },
  'control_flow/loops/for_loop': {
    name: 'For Loop',
    icon: '🔁',
    execIns: ['Start'],
    execOuts: ['LoopBody', 'Done'],
    dataIns: [{ name: 'Count', label: 'Count', defaultVal: 10, type: 'number' }],
    dataOuts: [{ name: 'Index', label: 'Index', type: 'number' }]
  },
  'hardware/virtual_laser': {
    name: 'Virtual Laser',
    icon: '🏮',
    execIns: ['Set'],
    execOuts: ['Out'],
    dataIns: [
      { name: 'Power', label: 'Power (dBm)', defaultVal: 0.0, type: 'number' },
      { name: 'Emission', label: 'Emission', defaultVal: false, type: 'boolean' }
    ],
    dataOuts: []
  },
  'hardware/virtual_sensor': {
    name: 'Power Sensor',
    icon: '📊',
    execIns: ['Measure'],
    execOuts: ['Out'],
    dataIns: [],
    dataOuts: [{ name: 'Reading', label: 'Reading', type: 'number' }]
  },
  'hardware/virtual_generator': {
    name: 'RF Generator',
    icon: '⚡',
    execIns: [],
    execOuts: [],
    dataIns: [],
    dataOuts: [{ name: 'Signal', label: 'Signal', type: 'list' }]
  },
  'hardware/virtual_oscilloscope': {
    name: 'Oscilloscope',
    icon: '📺',
    execIns: ['Trigger'],
    execOuts: ['Out'],
    dataIns: [{ name: 'Signal', label: 'Signal', type: 'list' }],
    dataOuts: [{ name: 'Waveform', label: 'Waveform', type: 'list' }]
  },
  'math/signal_processing/fft': {
    name: 'FFT Spectrum',
    icon: '📈',
    execIns: ['Analyze'],
    execOuts: ['Out'],
    dataIns: [{ name: 'Signal', label: 'Signal', type: 'list' }, { name: 'X', label: 'X', type: 'list', optional: true }],
    dataOuts: [{ name: 'Spectrum', label: 'Spectrum', type: 'list' }, { name: 'Frequencies', label: 'Frequencies', type: 'list' }]
  },
  'constants/boolean': {
    name: 'Boolean Toggle',
    icon: '🔘',
    execIns: [],
    execOuts: [],
    dataIns: [],
    dataOuts: [{ name: 'Value', label: 'Value', type: 'boolean' }]
  },
  'control_flow/loops/while_loop': {
    name: 'While Loop',
    icon: '🔁',
    execIns: ['Start'],
    execOuts: ['LoopBody', 'Done'],
    dataIns: [{ name: 'Condition', label: 'Condition', defaultVal: false, type: 'boolean' }],
    dataOuts: []
  },
  'control_flow/timing/measure_time': {
    name: 'Measure Time',
    icon: '⏱️',
    execIns: ['In'],
    execOuts: ['Body', 'Out'],
    dataIns: [],
    dataOuts: [{ name: 'Time', label: 'Time', type: 'number' }]
  },
  'arrays/manipulation/accumulate': {
    name: 'Accumulate',
    icon: '📥',
    execIns: ['Append', 'Reset'],
    execOuts: ['Out'],
    dataIns: [{ name: 'Value', label: 'Value', type: 'any' }],
    dataOuts: [{ name: 'Array', label: 'Array', type: 'list' }]
  },
  'outputs/basic/display': {
    name: 'Display',
    icon: '🖥️',
    execIns: ['In'],
    execOuts: ['Out'],
    dataIns: [{ name: 'Value', label: 'Value', defaultVal: '', type: 'any' }],
    dataOuts: []
  },
  'outputs/plots/plot': {
    name: 'Time Plot',
    icon: '📉',
    execIns: ['Plot'],
    execOuts: ['Out'],
    dataIns: [{ name: 'InputData', label: 'InputData', type: 'any' }],
    dataOuts: []
  },
  'outputs/plots/xy_plot': {
    name: 'XY Plot',
    icon: '📊',
    execIns: ['Plot'],
    execOuts: ['Out'],
    dataIns: [
      { name: 'X', label: 'X', type: 'array' },
      { name: 'Y', label: 'Y', type: 'array' },
      { name: 'XLabel', label: 'X Label', defaultVal: 'X', type: 'string', optional: true },
      { name: 'YLabel', label: 'Y Label', defaultVal: 'Y', type: 'string', optional: true }
    ],
    dataOuts: []
  }
};
