/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      fontFamily: {
        serif: ['Cormorant Garamond', 'serif'],
        sans: ['Inter', 'sans-serif'],
      },
      colors: {
        primary: '#c9a66b',
        secondary: '#8b7355',
      },
      filter: {
        grayscale: 'grayscale(100%)',
      },
    },
  },
  plugins: [],
}
