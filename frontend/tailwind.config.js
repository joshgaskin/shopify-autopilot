/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./pages/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './hooks/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          0: '#0A0A0B',
          1: '#151518',
          2: '#1A1A1A',
          3: '#222225',
        },
        border: {
          DEFAULT: 'rgba(255,255,255,0.08)',
          hover: 'rgba(255,255,255,0.12)',
          active: 'rgba(255,255,255,0.16)',
        },
        text: {
          primary: 'rgba(255,255,255,0.95)',
          secondary: 'rgba(255,255,255,0.72)',
          tertiary: 'rgba(255,255,255,0.48)',
        },
        accent: {
          DEFAULT: '#00FF94',
          dim: 'rgba(0,255,148,0.12)',
          hover: 'rgba(0,255,148,0.18)',
        },
        status: {
          success: '#00FF94',
          warning: '#FFB224',
          error: '#FF4444',
          info: '#3B82F6',
        }
      },
      fontSize: {
        'xs': ['11px', { lineHeight: '16px' }],
        'sm': ['12px', { lineHeight: '16px' }],
        'base': ['13px', { lineHeight: '20px' }],
        'lg': ['14px', { lineHeight: '20px' }],
        'xl': ['16px', { lineHeight: '24px' }],
        '2xl': ['20px', { lineHeight: '28px' }],
        '3xl': ['24px', { lineHeight: '32px' }],
      },
    },
  },
  plugins: [],
}
