/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: '#0d0f14',
          secondary: '#131820',
          tertiary: '#1a2030',
        },
        surface: {
          DEFAULT: '#1e2530',
          hover: '#252d3a',
          active: '#2c3545',
        },
        border: {
          DEFAULT: '#2a3347',
          subtle: '#1f2937',
          strong: '#3d4f6e',
        },
        primary: {
          DEFAULT: '#22d3ee',
          dim: '#0e7490',
          hover: '#38bdf8',
        },
        accent: {
          green: '#10b981',
          greenDim: '#065f46',
          amber: '#f59e0b',
          red: '#ef4444',
          purple: '#8b5cf6',
        },
        text: {
          primary: '#e2e8f0',
          secondary: '#94a3b8',
          muted: '#64748b',
          inverse: '#0d0f14',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
