import React, { useState, useEffect } from 'react';

interface ImageDisplayWidgetProps {
  blockId: string;
}

import { getBackendUrls } from '../../App';
import { ResizablePlotContainer } from '../common/ResizablePlotContainer';

export const ImageDisplayWidget: React.FC<ImageDisplayWidgetProps> = ({ blockId }) => {
  const [imagePath, setImagePath] = useState<string | null>(null);
  const BACKEND_URL = getBackendUrls().http;

  useEffect(() => {
    const handleTelemetry = (e: Event) => {
      const customEvent = e as CustomEvent;
      const telemetry = customEvent.detail;
      if (telemetry?.results?.filepath) {
        // Append a timestamp or random string to avoid browser caching issues if the same file gets overwritten
        const url = `${BACKEND_URL}/workspace/files/${telemetry.results.filepath}?t=${new Date().getTime()}`;
        setImagePath(url);
      }
    };

    const eventName = `telemetry-${blockId}`;
    window.addEventListener(eventName, handleTelemetry);
    return () => window.removeEventListener(eventName, handleTelemetry);
  }, [blockId, BACKEND_URL]);

  if (!imagePath) {
    return (
      <ResizablePlotContainer 
        minHeight="150px" 
        background="var(--panel-bg)" 
        padding="0px" 
        borderRadius="4px"
        border="1px dashed var(--block-border)"
      >
        {(width, height) => (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: width ? `${width}px` : '100%',
            height: height ? `${height}px` : '100%',
            color: 'var(--text-muted)'
          }}>
            No Image
          </div>
        )}
      </ResizablePlotContainer>
    );
  }

  return (
    <ResizablePlotContainer 
      minHeight="150px" 
      background="var(--panel-bg)" 
      padding="0px" 
      borderRadius="4px"
      border="1px solid var(--block-border)"
    >
      {(width, height) => (
        <div style={{
          width: width ? `${width}px` : '100%',
          height: height ? `${height}px` : '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden'
        }}>
          <img 
            src={imagePath} 
            alt="Block Display" 
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
              objectFit: 'contain'
            }}
          />
        </div>
      )}
    </ResizablePlotContainer>
  );
};
