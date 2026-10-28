/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        campo: {
          50:  '#f0f7e6',
          100: '#ddefc4',
          200: '#c5e17a',
          300: '#a8d44a',
          400: '#8bc34a',
          500: '#6da832',
          600: '#4a7c28',
          700: '#3b6320',
          800: '#2d5016',
          900: '#1e3a0e',
          950: '#0f2207',
        },
      },
    },
  },
  plugins: [],
};
