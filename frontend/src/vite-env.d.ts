/// <reference types="vite/client" />

declare module 'react-plotly.js' {
  import * as React from 'react';
  const Plot: React.ComponentType<any>;
  export default Plot;
}
