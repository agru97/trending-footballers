/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: '#4D96FF',
      },
      animation: {
        'gradient-xy': 'gradient-xy 6s ease infinite',
        'drawLine': 'drawLine 1.5s ease-out forwards',
      },
      keyframes: {
        'gradient-xy': {
          '0%, 100%': {
            'background-size': '400% 400%',
            'background-position': 'left top'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right bottom'
          }
        }
      },
      screens: {
        'xs': '375px',  // For medium phones
        'sm': '425px'   // For large phones
      }
    },
  },
  plugins: [],
}

