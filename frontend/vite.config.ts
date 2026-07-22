import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

let version = '0.0.0'
try {
  version = fs.readFileSync(path.resolve(__dirname, '../VERSION'), 'utf-8').trim()
} catch (e) {
  // Ignore
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    'import.meta.env.VITE_APP_VERSION': JSON.stringify(version),
  }
})
