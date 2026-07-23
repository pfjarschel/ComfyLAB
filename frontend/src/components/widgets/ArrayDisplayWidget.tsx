import React, { useState, useEffect } from 'react';
import { ResizablePlotContainer } from '../common/ResizablePlotContainer';

interface ArrayDisplayWidgetProps {
  blockId: string;
}

export const ArrayDisplayWidget: React.FC<ArrayDisplayWidgetProps> = ({ blockId }) => {
  const [imageData, setImageData] = useState<string | null>(null);

  useEffect(() => {
    const handleTelemetry = (e: Event) => {
      const customEvent = e as CustomEvent;
      const telemetry = customEvent.detail;
      if (telemetry?.results?.image_data) {
        setImageData(telemetry.results.image_data);
      }
    };

    const eventName = `telemetry-${blockId}`;
    window.addEventListener(eventName, handleTelemetry);
    return () => window.removeEventListener(eventName, handleTelemetry);
  }, [blockId]);

  if (!imageData) {
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
            color: 'var(--text-muted)',
            fontSize: '0.85rem'
          }}>
            No Array Data
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
            src={imageData} 
            alt="Array Display" 
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
