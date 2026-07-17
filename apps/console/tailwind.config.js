/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#F0F1EF',
        panel: { DEFAULT: '#FFFFFF', '2': '#E8E9E4' },
        line: { DEFAULT: '#D5D6D0', '2': '#B4B5AE' },
        ink: { DEFAULT: '#121417', dim: '#5C6068' },
        accent: '#D9480F',
        imminent: '#C92A2A',
        near: '#D9480F',
        watch: '#1864AB',
        unknown: '#868E96',
        ok: '#2B8A3E',
      },
      fontFamily: {
        sans: ['IBM Plex Sans', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        mono: ['IBM Plex Mono', 'ui-monospace', 'SF Mono', 'Menlo', 'monospace'],
      },
      fontSize: {
        // Revised scale (2026-07-18): titles must out-rank body — card titles
        // sit at base (14px), page h1 at lg (18px), display/counterfactual xl.
        micro: ['10px', { lineHeight: '1.4' }],
        xs: ['12px', { lineHeight: '1.45' }],
        sm: ['13px', { lineHeight: '1.45' }],
        base: ['14px', { lineHeight: '1.45' }],
        md: ['15px', { lineHeight: '1.45' }],
        lg: ['18px', { lineHeight: '1.4' }],
        xl: ['22px', { lineHeight: '1.3' }],
        '2xl': ['24px', { lineHeight: '1.25' }],
      },
      spacing: {
        '0.5': '2px', '1': '4px', '1.5': '6px', '2': '8px', '2.5': '10px',
        '3': '12px', '3.5': '14px', '4': '16px', '5': '20px', '6': '24px',
        '7': '28px', '8': '32px', '9': '36px', '10': '40px', '12': '48px',
      },
      borderRadius: {
        sm: '2px', DEFAULT: '4px', md: '6px', lg: '8px',
      },
      transitionDuration: {
        fast: '150ms', DEFAULT: '200ms', slow: '300ms',
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
}
