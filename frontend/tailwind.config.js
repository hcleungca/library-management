/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'status-available': '#10b981',
        'status-checkedout': '#0284c7',
        'status-overdue': '#ef4444',
        'status-processing': '#f59e0b',
      },
      container: {
        center: true,
        padding: '1rem',
      },
      borderRadius: {
        'lg': '0.5rem',
        'md': '0.375rem',
        'sm': '0.25rem',
      },
    },
  },
  plugins: [],
};

