import type { Config } from 'tailwindcss';

// Design tokens distilled from the LumiPic UI findings: a dark, cinematic
// palette with subtle blue-tinted surfaces, muted-blue CTAs, and large radii.
const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primaryBg: '#050816',
        surface: '#0B1220',
        surfaceAlt: '#071120',
        surfaceLine: 'rgba(255,255,255,0.08)',
        primaryText: '#F5F7FA',
        secondaryText: 'rgba(255,255,255,0.65)',
        mutedText: 'rgba(255,255,255,0.4)',
        cta: '#5F97D3',
        ctaHover: '#6AA6E8',
        accentBlue: '#1389FF',
        accentBlue2: '#1E90FF',
        warning: '#FF3B30',
        premium: '#F6A800',
      },
      borderRadius: {
        card: '20px',
        button: '22px',
        pill: '28px',
      },
      boxShadow: {
        card: '0 8px 30px rgba(0,0,0,0.35)',
      },
      keyframes: {
        indeterminate: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(250%)' },
        },
      },
      animation: {
        indeterminate: 'indeterminate 1.2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};

export default config;
