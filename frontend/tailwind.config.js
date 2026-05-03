/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0F19', // Deep navy/black
        surface: '#1A2333',    // Slightly lighter for cards
        primary: '#3B82F6',    // Blue
        secondary: '#8B5CF6',  // Purple
        accent: '#10B981',     // Green
      },
    },
  },
  plugins: [],
}
