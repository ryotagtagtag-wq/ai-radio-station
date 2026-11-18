import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// GitHub Pages サブパス (/<repo>/) とローカル開発 (./) の両方に対応。
// VITE_BASE 環境変数で上書き可能。未設定時は "./"。
const base = process.env.VITE_BASE || "./";

export default defineConfig({
  base,
  plugins: [
    react(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
  server: {
    port: 5173,
    open: true,
  },
});
