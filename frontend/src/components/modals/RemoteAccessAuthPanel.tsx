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


interface RemoteAccessAuthPanelProps {
  authInput: string;
  authError: string;
  setAuthInput: (value: string) => void;
  onSubmit: () => void;
}

export const RemoteAccessAuthPanel = ({
  authInput,
  authError,
  setAuthInput,
  onSubmit,
}: RemoteAccessAuthPanelProps) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      width: '100vw',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#090d16',
      color: '#e2e8f0',
      fontFamily: "'Outfit', 'Inter', sans-serif"
    }}>
      <div className="glass-panel" style={{
        width: '380px',
        padding: '30px',
        borderRadius: '8px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)'
      }}>
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ margin: '0 0 8px 0', color: '#60a5fa' }}>ComfyLAB Remote Access</h2>
          <p style={{ margin: 0, fontSize: '13px', color: '#94a3b8' }}>
            Secure hardware control environment
          </p>
        </div>
        
        {authError && (
          <div style={{
            padding: '10px',
            borderRadius: '4px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            color: '#f87171',
            fontSize: '13px'
          }}>
            {authError}
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <label style={{ fontSize: '12px', fontWeight: '600', color: '#cbd5e1' }}>
            Enter Server Access Token or User:Password
          </label>
          <input
            type="password"
            placeholder="e.g. right-words or admin:password"
            value={authInput}
            onChange={(e) => setAuthInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') onSubmit();
            }}
            style={{
              padding: '10px',
              borderRadius: '4px',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              background: 'rgba(255, 255, 255, 0.05)',
              color: '#fff',
              fontSize: '14px',
              outline: 'none'
            }}
          />
        </div>

        <button
          className="btn"
          style={{
            padding: '12px',
            background: '#60a5fa',
            color: '#090d16',
            fontWeight: 'bold',
            borderRadius: '4px',
            border: 'none',
            cursor: 'pointer',
            fontSize: '14px'
          }}
          onClick={onSubmit}
        >
          Authenticate Access
        </button>
      </div>
    </div>
  );
};
