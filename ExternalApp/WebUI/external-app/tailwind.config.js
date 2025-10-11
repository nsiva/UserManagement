/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        // Custom bright green palette for light theme
        'green-light': {
          50: '#f0fff4',    // Very bright light green background
          100: '#dcfce7',   // Bright light green
          200: '#bbf7d0',   // Medium bright green
          300: '#4ade80',   // Vibrant bright green
          400: '#22c55e',   // Bright primary green
          500: '#16a34a',   // Strong bright green
          600: '#15803d',   // Deep bright green
          700: '#166534',   // Dark green for text
          800: '#14532d',   // Darker green
          900: '#052e16',   // Darkest green
        },
        // Custom dark green palette for dark theme  
        'green-dark': {
          50: '#001a0e',    // Very dark green background
          100: '#003d20',   // Dark green background
          200: '#065f46',   // Medium dark green
          300: '#047857',   // Darker green accent
          400: '#059669',   // Dark emerald
          500: '#10b981',   // Bright emerald for dark theme
          600: '#34d399',   // Light emerald
          700: '#6ee7b7',   // Very light mint
          800: '#a7f3d0',   // Pale mint
          900: '#d1fae5',   // Almost white mint
        },
        // Primary color scheme
        primary: {
          light: '#22c55e',
          dark: '#10b981',
        },
        // Background colors
        bg: {
          light: '#f0fdf4',
          dark: '#064e3b',
        },
        // Text colors
        text: {
          light: '#064e3b',
          dark: '#ffffff',
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'bounce-in': 'bounceIn 0.6s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        bounceIn: {
          '0%': { transform: 'scale(0.3)', opacity: '0' },
          '50%': { transform: 'scale(1.05)' },
          '70%': { transform: 'scale(0.9)' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}