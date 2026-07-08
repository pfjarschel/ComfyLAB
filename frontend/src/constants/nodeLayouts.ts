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
  script_language?: string;
  ui_behavior?: Record<string, any>;
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
    case 'ndarray':
    case 'array':
      return '#06b6d4'; // Cyan (LabVIEW arrays/waveform)
    case 'list':
      return '#e5a50a'; // Yellow for standard Lists
    case 'any':
    default:
      return '#64748b'; // Neutral slate gray for generic/unspecified types
  }
};

