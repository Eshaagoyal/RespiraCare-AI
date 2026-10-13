/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          light: '#eff6ff', 
          DEFAULT: '#3b82f6', 
          dark: '#1d4ed8', 
        },
        glass: 'rgba(255, 255, 255, 0.7)',
        glassBorder: 'rgba(255, 255, 255, 0.5)',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.07)',
        'soft': '0 10px 40px -10px rgba(0,0,0,0.08)',
      }
    },
  },
  plugins: [],
}
