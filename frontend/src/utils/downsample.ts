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

/**
 * Largest-Triangle-Three-Buckets (LTTB) Downsampling Algorithm.
 * 
 * Downsamples time-series and scatter data in linear O(N) time while strictly
 * preserving visual features, waveform peaks, valleys, and trends.
 * 
 * @param x Array-like series of X coordinates (numbers).
 * @param y Array-like series of Y coordinates (numbers).
 * @param targetPoints Desired number of output points (threshold).
 * @returns Downsampled { x, y } pair.
 */
export function downsampleLTTB(
  x: ArrayLike<number>,
  y: ArrayLike<number>,
  targetPoints: number
): { x: number[]; y: number[] } {
  const dataLen = y.length;

  if (targetPoints >= dataLen || targetPoints <= 0 || dataLen <= 2) {
    const outX = Array.from(x && x.length === dataLen ? x : Array.from({ length: dataLen }, (_, i) => i));
    const outY = Array.from(y);
    return { x: outX, y: outY };
  }

  const sampledX: number[] = new Array(targetPoints);
  const sampledY: number[] = new Array(targetPoints);

  const hasExplicitX = x && x.length === dataLen;
  const getX = (idx: number) => (hasExplicitX ? x[idx] : idx);

  // Bucket size along the range between the first and last points
  const every = (dataLen - 2) / (targetPoints - 2);

  let aIndex = 0; // Point A: initially the first point
  sampledX[0] = getX(aIndex);
  sampledY[0] = y[aIndex];

  let sampledIndex = 1;

  for (let i = 0; i < targetPoints - 2; i++) {
    // Calculate average X and Y of the NEXT bucket (Bucket C)
    let avgX = 0;
    let avgY = 0;
    const avgRangeStart = Math.floor((i + 1) * every) + 1;
    const avgRangeEnd = Math.min(Math.floor((i + 2) * every) + 1, dataLen);
    const avgRangeLength = avgRangeEnd - avgRangeStart;

    if (avgRangeLength > 0) {
      for (let j = avgRangeStart; j < avgRangeEnd; j++) {
        avgX += getX(j);
        avgY += y[j];
      }
      avgX /= avgRangeLength;
      avgY /= avgRangeLength;
    } else {
      avgX = getX(dataLen - 1);
      avgY = y[dataLen - 1];
    }

    // Get the range for the CURRENT bucket (Bucket B)
    const rangeStart = Math.floor(i * every) + 1;
    const rangeEnd = Math.min(Math.floor((i + 1) * every) + 1, dataLen);

    // Point A coordinates
    const pointAx = getX(aIndex);
    const pointAy = y[aIndex];

    let maxArea = -1;
    let maxAreaIndex = rangeStart;

    for (let j = rangeStart; j < rangeEnd; j++) {
      const currentX = getX(j);
      const currentY = y[j];

      // Triangle area: 0.5 * |(Ax - Cx)(yB - Ay) - (Ax - xB)(Cy - Ay)|
      const area = Math.abs(
        (pointAx - avgX) * (currentY - pointAy) -
        (pointAx - currentX) * (avgY - pointAy)
      ) * 0.5;

      if (area > maxArea) {
        maxArea = area;
        maxAreaIndex = j;
      }
    }

    // Next point is the one with the largest area in bucket B
    sampledX[sampledIndex] = getX(maxAreaIndex);
    sampledY[sampledIndex] = y[maxAreaIndex];
    sampledIndex++;

    aIndex = maxAreaIndex; // This point becomes Point A for the next iteration
  }

  // Always include the very last point
  sampledX[targetPoints - 1] = getX(dataLen - 1);
  sampledY[targetPoints - 1] = y[dataLen - 1];

  return { x: sampledX, y: sampledY };
}
