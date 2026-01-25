/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        conservative: '#dc2626', // Red
        liberal: '#2563eb', // Blue
      },
    },
  },
  plugins: [],
}
