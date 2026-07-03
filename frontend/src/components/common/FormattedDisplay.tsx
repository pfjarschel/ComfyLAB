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

import { useState, useEffect, useRef } from 'react';

const formatDisplayNumber = (value: number, maxChars: number): string => {
  if (!isFinite(value)) return String(value);
  if (value === 0) return '0';

  const abs = Math.abs(value);

  if (abs >= 1e7 || (abs < 1e-4 && abs > 0)) {
    for (let sig = Math.min(8, maxChars - 5); sig >= 1; sig--) {
      const s = value.toExponential(sig);
      if (s.length <= maxChars) return s;
    }
    return value.toExponential(0);
  }

  for (let d = Math.min(10, maxChars - 2); d >= 0; d--) {
    let s = value.toFixed(d);
    s = s.replace(/\.0+$/, '').replace(/(\.\d*?)0+$/, '$1');
    if (s.length <= maxChars) return s;
  }

  return value.toExponential(Math.min(3, maxChars - 6));
};

export const FormattedDisplay = ({ value }: { value: unknown }) => {
  const ref = useRef<HTMLDivElement>(null);
  const [maxChars, setMaxChars] = useState(14);

  useEffect(() => {
    const el = ref.current?.parentElement;
    if (!el) return;
    const measure = () => {
      setMaxChars(Math.max(4, Math.floor(el.clientWidth / 12.5) - 1));
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div ref={ref} style={{ display: 'inline-block' }}>
      {value === undefined || value === null ? (
        <span>---</span>
      ) : typeof value === 'number' ? (
        <span>{formatDisplayNumber(value, maxChars)}</span>
      ) : (
        <span>{String(value)}</span>
      )}
    </div>
  );
};
