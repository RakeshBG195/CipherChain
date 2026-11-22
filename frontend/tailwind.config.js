/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { extend: { colors: { navy: { 950: "#03050f", 900: "#050816", 800: "#0b1226", 700: "#121b36" },
    neon: { cyan: "#22d3ee", blue: "#3b82f6", purple: "#a855f7" } },
    fontFamily: { mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"] } } },
  plugins: [],
};
