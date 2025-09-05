/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        'theme': {
          'primary': 'var(--color-primary)',
          'primary-hover': 'var(--color-primary-hover)',
          'primary-text': 'var(--color-primary-text)',
          'secondary': 'var(--color-secondary)',
          'secondary-hover': 'var(--color-secondary-hover)',
          'header-bg': 'var(--color-header-bg)',
          'background': 'var(--color-background)',
          'surface': 'var(--color-surface)',
          'surface-hover': 'var(--color-surface-hover)',
          'text': 'var(--color-text)',
          'text-secondary': 'var(--color-text-secondary)',
          'text-muted': 'var(--color-text-muted)',
          'border': 'var(--color-border)',
          'border-focus': 'var(--color-border-focus)',
          'success': 'var(--color-success)',
          'warning': 'var(--color-warning)',
          'error': 'var(--color-error)',
          'input-bg': 'var(--color-input-bg)',
          'modal-overlay': 'var(--color-modal-overlay)'
        }
      }
    },
  },
  plugins: [],
}