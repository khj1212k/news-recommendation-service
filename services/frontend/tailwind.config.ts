import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#101010',
        sand: '#f2efe8',
        moss: '#2f5d50',
        ember: '#d14f3f',
        haze: '#e6dcc8'
      },
      fontFamily: {
        serif: ['"Nanum Myeongjo"', 'serif'],
        sans: ['"IBM Plex Sans KR"', 'sans-serif']
      },
      boxShadow: {
        glow: '0 10px 30px rgba(17, 58, 45, 0.25)'
      }
    }
  },
  plugins: []
}

export default config
