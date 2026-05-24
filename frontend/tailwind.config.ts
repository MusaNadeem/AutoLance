import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-outfit)", "system-ui", "sans-serif"],
        display: ["var(--font-space-grotesk)", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      colors: {
        // Neo-Brutalist Base
        surface: {
          900: "#050505", // Extremely dark, tinted black
          800: "#0a0a0a",
          700: "#141414",
          600: "#1f1f1f",
          500: "#2e2e2e",
        },
        border: {
          DEFAULT: "#2e2e2e",
          focus: "#ccff00", // Neon lime focus
        },
        // Neon Accents
        neon: {
          lime: "#ccff00",
          orange: "#ff4500",
          cyan: "#00e5ff",
          pink: "#ff007f",
        },
        // Semantic
        success: "#ccff00", // Reusing lime for high-impact success
        warning: "#ff4500", // Orange
        danger: "#ff007f",  // Pink
        info: "#00e5ff",    // Cyan
      },
      backgroundImage: {
        "grid-pattern": "linear-gradient(to right, #141414 1px, transparent 1px), linear-gradient(to bottom, #141414 1px, transparent 1px)",
      },
      boxShadow: {
        "brutal-sm": "2px 2px 0px 0px rgba(204, 255, 0, 1)",
        "brutal-md": "4px 4px 0px 0px rgba(204, 255, 0, 1)",
        "brutal-lg": "8px 8px 0px 0px rgba(204, 255, 0, 1)",
        "brutal-orange": "4px 4px 0px 0px rgba(255, 69, 0, 1)",
        "brutal-cyan": "4px 4px 0px 0px rgba(0, 229, 255, 1)",
      },
      borderRadius: {
        // Sharper radiuses for brutalist feel
        lg: "0px",
        md: "0px",
        sm: "0px",
        none: "0px",
        full: "9999px",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out forwards",
        "slide-up": "slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards", // Custom easing, not bouncy
        "marquee": "marquee 20s linear infinite",
        "blink": "blink 1s step-end infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(24px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        marquee: {
          "0%": { transform: "translateX(0%)" },
          "100%": { transform: "translateX(-100%)" },
        },
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0" },
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
