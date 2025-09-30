/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './web/components/**/*.{js,ts,jsx,tsx}',
    './web/pages/**/*.{js,ts,jsx,tsx}',
    './common/components/**/*.{js,ts,jsx,tsx}',
  ],
  corePlugins: {
    preflight: false, // This allows to fix the headers by avoiding the default tailwind reset
  },
  darkMode: 'class',
  plugins: [],
  // Uses .dark class for dark mode
  theme: {
    extend: {
      borderRadius: {
        DEFAULT: '6px',
        'lg': '8px',
        'sm': '4px',
        'xlg': '10px',
      },

      colors: {
        // Alert colors
        alert: {
          'danger-bg': 'rgba(254, 239, 241)',
          'danger-dark-bg': 'rgba(34, 23, 40)',
          'info-bg': 'rgba(236, 249, 252)',
          'info-dark-bg': 'rgba(15, 32, 52)',
          'success-bg': 'rgba(39, 171, 149, 0.08)',
          'success-dark-bg': 'rgba(17, 32, 46)',
          'warning-bg': 'rgba(255, 248, 240)',
          'warning-dark-bg': 'rgba(34, 31, 39)',
        },

        // Alpha colors for overlays and subtle backgrounds
        alpha: {
          'basic-16': 'rgba(101, 109, 123, 0.16)',
          'basic-24': 'rgba(101, 109, 123, 0.24)',
          'basic-32': 'rgba(101, 109, 123, 0.32)',
          'basic-48': 'rgba(101, 109, 123, 0.48)',
          'basic-8': 'rgba(101, 109, 123, 0.08)',
          'black-16': 'rgba(0, 0, 0, 0.16)',
          'black-32': 'rgba(0, 0, 0, 0.32)',
          'black-8': 'rgba(0, 0, 0, 0.08)',
          'primary-16': 'rgba(149, 108, 255, 0.16)',
          'primary-24': 'rgba(149, 108, 255, 0.24)',
          'primary-32': 'rgba(149, 108, 255, 0.32)',
          'primary-8': 'rgba(149, 108, 255, 0.08)',
          'white-16': 'rgba(255, 255, 255, 0.16)',
          'white-24': 'rgba(255, 255, 255, 0.24)',
          'white-32': 'rgba(255, 255, 255, 0.32)',
          'white-48': 'rgba(255, 255, 255, 0.48)',
          'white-8': 'rgba(255, 255, 255, 0.08)',
        },

        // Background colors
        bg: {
          'dark-100': '#2d3443',
          'dark-200': '#202839',
          'dark-300': '#161d30',
          'dark-400': '#15192b',
          'dark-500': '#101628',
          'light-100': '#ffffff',
          'light-200': '#fafafb',
          'light-300': '#eff1f4',
          'light-500': '#e0e3e9',
        },

        // Body colors
        body: {
          DEFAULT: '#1a2634',
          dark: '#ffffff',
        },

        // Checkbox colors
        checkbox: {
          border: 'rgba(101, 109, 123, 0.24)',
          'border-dark': 'rgba(255, 255, 255, 0.24)',
          'checked-hover-border': '#4e25db',
          'focus-bg': 'rgba(149, 108, 255, 0.08)',
          'focus-border': '#906af6',
          'hover-border': '#6837fc',
        },

        // Semantic colors
        danger: {
          400: '#f57c78',
          DEFAULT: '#ef4d56',
        },

        'dark-text': '#ff0000',

        // Header colors
        header: {
          DEFAULT: '#1e0d26',
          dark: '#ffffff',
        },

        info: '#0aaddf',

        // Input colors
        input: {
          bg: '#fff',
          'bg-alt': '#f7f7f7',
          'bg-dark': '#161d30',
          'border': 'rgba(101, 109, 123, 0.16)',
          'border-dark': '#15192b',
          'placeholder': 'rgba(157, 164, 174, 1)',
          'placeholder-dark': 'rgba(157, 164, 174, 1)',
        },

        // Primary colors
        primary: {
          400: '#906af6',
          600: '#4e25db',
          700: '#3919b7',
          800: '#2a2054',
          900: '#1E0D26',
          DEFAULT: '#6837fc',
        },

        // Secondary colors
        secondary: {
          400: '#fae392',
          500: '#F7D56E',
          600: '#e5c55f',
          700: '#d4b050',
          DEFAULT: '#fae392',
        },

        success: {
          400: '#56ccad',
          600: '#13787b',
          DEFAULT: '#27ab95',
        },

        // Text colors
        text: {
          DEFAULT: '#FF0000',
          'icon-grey': '#656d7b',
          'icon-light': '#ffffff',
          'icon-light-grey': 'rgba(157, 164, 174, 1)',
        },

        warning: '#ff9f43',
      },

      fontFamily: {
        header: ['OpenSans', 'sans-serif'],
        sans: ['OpenSans', 'sans-serif'],
      },

      fontSize: {
        '2xl': '24px',
        '3xl': '30px',
        '4xl': '36px',
        '5xl': '48px',
        '6xl': '60px',
        'base': '16px',
        'lg': '18px',
        'sm': '14px',
        'xl': '20px',
        'xs': '12px',
      },

      height: {
        'btn': '44px',
        'btn-lg': '56px',
        'btn-sm': '40px',
        'btn-xsm': '32px',
        'input': '44px',
        'input-lg': '58px',
        'input-sm': '42px',
        'input-xsm': '34px',
        'textarea': '120px',
        'textarea-lg': '128px',
        'textarea-sm': '100px',
      },

      opacity: {
        'disabled': '0.32',
      },

      spacing: {
        'btn-x': '20px',
        'btn-x-lg': '24px',
        'btn-x-sm': '16px',
        'input-x': '16px',
        'input-x-lg': '20px',
        'input-x-sm': '14px',
        'input-y': '12px',
        'input-y-lg': '16px',
        'input-y-sm': '8px',
      },

      transitionDuration: {
        'button': '400ms',
        'highlight': '450ms',
      },

      transitionTimingFunction: {
        'material': 'cubic-bezier(0.23, 1, 0.32, 1)',
      },
    },
  },
}
