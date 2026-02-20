const config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: "#030303",
          surface: "#0A0C0A",
          surface2: "#0F130F",
          border: "#1A2E1A",
          phosphor: "#39FF14",
          dim: "#008F11",
          cyan: "#00FFFF",
          amber: "#FFB000",
          magenta: "#FF00FF",
          white: "#EAFBE6",
        },
      },
      fontFamily: {
        mono: [
          '"JetBrains Mono"',
          '"Fira Code"',
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          '"Liberation Mono"',
          '"Courier New"',
          "monospace",
        ],
      },
      boxShadow: {
        terminal: "0 0 0 1px rgba(57,255,20,0.18), 0 10px 30px rgba(0,0,0,0.55)",
      },
    },
  },
  plugins: [],
}

export default config
