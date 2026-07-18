/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "media",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        banda: {
          verde: "#22c55e",
          amarelo: "#eab308",
          vermelho: "#ef4444",
          cinza: "#9ca3af",
        },
      },
    },
  },
  plugins: [],
};
