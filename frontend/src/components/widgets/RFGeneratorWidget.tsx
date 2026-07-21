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

import { NumericTextInput } from '../common/NumericTextInput';

interface RFGeneratorWidgetProps {
  waveType: string | undefined;
  frequency: number | undefined;
  amplitude: number | undefined;
  onChange: (name: string, value: any) => void;
}

export const RFGeneratorWidget = ({
  waveType,
  frequency,
  amplitude,
  onChange,
}: RFGeneratorWidgetProps) => {
  return (
    <>
      <div className="input-group">
        <label>Wave Type</label>
        <select
          value={waveType || 'sine'}
          onChange={(e) => onChange('wave_type', e.target.value)}
          className="nodrag"
        >
          <option value="sine">Sine</option>
          <option value="square">Square</option>
          <option value="triangle">Triangle</option>
        </select>
      </div>
      <div className="input-row">
        <span className="input-row-label">Freq (Hz)</span>
        <NumericTextInput
          value={frequency ?? 10.0}
          onChange={(v) => onChange('frequency', v)}
          min={0.1}
          className="nodrag"
          style={{ flex: 1, marginLeft: '12px', minWidth: '40px', padding: '2px 4px', fontSize: '0.8rem', background: 'var(--input-bg)', border: '1px solid var(--block-border)', borderRadius: '4px', color: 'var(--text-color)' }}
        />
      </div>
      <div className="input-row">
        <span className="input-row-label">Amp</span>
        <NumericTextInput
          value={amplitude ?? 1.0}
          onChange={(v) => onChange('amplitude', v)}
          min={0.0}
          className="nodrag"
          style={{ flex: 1, marginLeft: '12px', minWidth: '40px', padding: '2px 4px', fontSize: '0.8rem', background: 'var(--input-bg)', border: '1px solid var(--block-border)', borderRadius: '4px', color: 'var(--text-color)' }}
        />
      </div>
    </>
  );
};
