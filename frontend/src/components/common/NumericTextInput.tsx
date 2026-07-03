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

import React, { useState, useEffect } from 'react';

export const NumericTextInput = ({
  value,
  onChange,
  min,
  max,
  readOnly,
  className,
  style,
}: {
  value: number | undefined;
  onChange: (val: number) => void;
  min?: number;
  max?: number;
  readOnly?: boolean;
  className?: string;
  style?: React.CSSProperties;
}) => {
  const [localText, setLocalText] = useState(String(value ?? 0));
  const [isFocused, setIsFocused] = useState(false);

  useEffect(() => {
    if (!isFocused) {
      setLocalText(String(value ?? 0));
    }
  }, [value, isFocused]);

  const clamp = (v: number): number => {
    if (min !== undefined && v < min) return min;
    if (max !== undefined && v > max) return max;
    return v;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    setLocalText(raw);
    const parsed = parseFloat(raw);
    if (!isNaN(parsed)) {
      onChange(clamp(parsed));
    }
  };

  const handleFocus = () => {
    setIsFocused(true);
    setLocalText(String(value ?? 0));
  };

  const handleBlur = () => {
    setIsFocused(false);
    const parsed = parseFloat(localText);
    if (isNaN(parsed)) {
      setLocalText(String(value ?? 0));
    } else {
      const clamped = clamp(parsed);
      setLocalText(String(clamped));
      onChange(clamped);
    }
  };

  return (
    <input
      type="text"
      inputMode="decimal"
      value={localText}
      onChange={handleChange}
      onFocus={handleFocus}
      onBlur={handleBlur}
      readOnly={readOnly}
      className={className}
      style={style}
    />
  );
};
