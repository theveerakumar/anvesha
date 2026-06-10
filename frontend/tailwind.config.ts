import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bloomberg: {
          bg: "#0a0e14",
          surface: "#13181f",
          border: "#1e2a3a",
          text: "#c5d0e0",
          dim: "#6a7a8e",
          green: "#00c853",
          red: "#ff1744",
          cyan: "#00bcd4",
          yellow: "#ffd600",
          highlight: "#1a2634",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
