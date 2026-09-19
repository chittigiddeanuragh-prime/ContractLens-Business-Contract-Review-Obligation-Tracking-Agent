/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      colors: {
        dark: {
          bg: '#081621',
          panel: '#0e2636',
          panelHover: '#133044',
          border: '#183a4f',
          subtext: '#8ba5b5',
          heading: '#ffffff',
        },
        status: {
          critical: '#ef4444',
          criticalBg: '#451a1a',
          atRisk: '#f59e0b',
          atRiskBg: '#453014',
          good: '#10b981',
          goodBg: '#133e2b',
          info: '#0ea5e9',
          infoBg: '#0f3a4e',
        }
      },
    },
  },
  plugins: [],
}
