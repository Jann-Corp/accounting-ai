/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gold: {
          DEFAULT: 'var(--accent-gold)',
          light: 'var(--accent-gold-light)',
          dark: 'var(--accent-gold-dark)',
        },
        bg: {
          primary: 'var(--bg-primary)',
          secondary: 'var(--bg-secondary)',
          card: 'var(--bg-card)',
          hover: 'var(--bg-hover)',
        },
        text: {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          muted: 'var(--text-muted)',
        },
        border: {
          DEFAULT: 'var(--border-color)',
          strong: 'var(--border-strong)',
        },
        income: 'var(--income-color)',
        expense: 'var(--expense-color)',
        transfer: 'var(--transfer-color)',
      },
      boxShadow: {
        'gold': '0 4px 16px rgba(212, 168, 67, 0.2)',
        'gold-lg': '0 8px 24px rgba(212, 168, 67, 0.25)',
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
      },
      backgroundImage: {
        'gradient-gold': 'var(--gradient-gold)',
        'gradient-dark-gold': 'var(--gradient-dark-gold)',
      },
    },
  },
  plugins: [],
}
