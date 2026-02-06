/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // Cores Oficiais Lojas Caçula
        'cacula-green': {
          DEFAULT: '#78B928',
          50: '#F2F9E8',
          100: '#E5F3D1',
          200: '#CCE7A3',
          300: '#B2DB75',
          400: '#99CF47',
          500: '#78B928', // Principal
          600: '#609420',
          700: '#486F18',
          800: '#304A10',
          900: '#182508',
        },
        'cacula-red': {
          DEFAULT: '#ED1C24',
          50: '#FEE8E9',
          100: '#FDD1D3',
          500: '#ED1C24', // Principal
          600: '#BE161D',
        },
        'cacula-yellow': {
          DEFAULT: '#FDB913',
          50: '#FFF9E5',
          100: '#FFF3CB',
          500: '#FDB913', // Principal
          600: '#CA940F',
        },
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
        background: "var(--background)",
        foreground: "var(--foreground)",
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          foreground: "var(--secondary-foreground)",
        },
        destructive: {
          DEFAULT: "var(--destructive)",
          foreground: "var(--destructive-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
        },
        popover: {
          DEFAULT: "var(--popover)",
          foreground: "var(--popover-foreground)",
        },
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--card-foreground)",
        },
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #78B928 0%, #99CF47 100%)',
        'gradient-accent': 'linear-gradient(135deg, #ED1C24 0%, #F7474F 100%)',
        'gradient-hero': 'linear-gradient(135deg, #78B928 0%, #FDB913 50%, #ED1C24 100%)',
        'gradient-surface': 'linear-gradient(to bottom right, rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.4))',
        'gradient-dark-surface': 'linear-gradient(to bottom right, rgba(31, 41, 55, 0.8), rgba(31, 41, 55, 0.4))',
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
}
