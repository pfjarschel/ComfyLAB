import React, { useEffect, useRef } from 'react';

interface BeepWidgetProps {
  blockId: string;
}

const BeepWidget: React.FC<BeepWidgetProps> = ({ blockId }) => {
  const audioCtxRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    // Listen for telemetry events on window
    const handleTelemetry = (e: CustomEvent<any>) => {
      const payload = e.detail?.results;
      if (payload && payload.action === 'play_beep') {
        playTone(
          payload.type || 'sine',
          payload.frequency || 440,
          payload.duration || 200,
          payload.volume || 1.0
        );
      }
    };

    const eventName = `telemetry-${blockId}`;
    window.addEventListener(eventName, handleTelemetry as EventListener);
    return () => {
      window.removeEventListener(eventName, handleTelemetry as EventListener);
      if (audioCtxRef.current) {
        audioCtxRef.current.close();
      }
    };
  }, [blockId]);

  const playTone = (type: string, freq: number, dur: number, vol: number) => {
    try {
      if (!audioCtxRef.current || audioCtxRef.current.state === 'closed') {
        audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      
      const ctx = audioCtxRef.current;
      
      if (ctx.state === 'suspended') {
        ctx.resume();
      }

      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();

      oscillator.type = type as OscillatorType;
      oscillator.frequency.value = freq;

      gainNode.gain.setValueAtTime(0, ctx.currentTime);
      gainNode.gain.linearRampToValueAtTime(vol, ctx.currentTime + 0.02);
      gainNode.gain.linearRampToValueAtTime(0, ctx.currentTime + (dur / 1000));

      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);

      oscillator.start(ctx.currentTime);
      oscillator.stop(ctx.currentTime + (dur / 1000) + 0.05);
    } catch (err) {
      console.warn("Failed to play beep sound", err);
    }
  };

  return null; 
};

export default BeepWidget;
