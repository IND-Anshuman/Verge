/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0e1116',
        panel: { DEFAULT: '#161b22', '2': '#1c232d' },
        line: '#2a323d',
        ink: { DEFAULT: '#e6edf3', dim: '#8b949e' },
        accent: '#e8a33d',
        imminent: '#f06363',
        near: '#e8a33d',
        watch: '#4fa3c7',
        unknown: '#6b7682',
        ok: '#4ec98a',
      },
      fontFamily: {
        sans: ['ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        mono: ['ui-monospace', 'SF Mono', 'Menlo', 'monospace'],
      },
      fontSize: {
        micro: ['10px', { lineHeight: '1.4' }],
        xs: ['11px', { lineHeight: '1.45' }],
        sm: ['12px', { lineHeight: '1.45' }],
        base: ['13px', { lineHeight: '1.45' }],
        md: ['14px', { lineHeight: '1.45' }],
        lg: ['16px', { lineHeight: '1.4' }],
        xl: ['18px', { lineHeight: '1.35' }],
        '2xl': ['20px', { lineHeight: '1.3' }],
      },
      spacing: {
        '0.5': '2px', '1': '4px', '1.5': '6px', '2': '8px', '2.5': '10px',
        '3': '12px', '3.5': '14px', '4': '16px', '5': '20px', '6': '24px', '8': '32px',
      },
      borderRadius: {
        sm: '4px', DEFAULT: '6px', md: '8px', lg: '12px',
      },
      transitionDuration: {
        fast: '150ms', DEFAULT: '200ms', slow: '300ms',
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
}
