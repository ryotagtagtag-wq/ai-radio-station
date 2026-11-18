import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import VitePWA from "vite-plugin-pwa";

// GitHub Pages サブパス (/<repo>/) とローカル開発 (./) の両方に対応。
// VITE_BASE 環境変数で上書き可能。未設定時は "./"。
const base = process.env.VITE_BASE || "./";

export default defineConfig({
  base,
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,png,svg,mp3,json}"],
        runtimeCaching: [
          {
            urlPattern: /^https?.*/,
            handler: "NetworkFirst",
            options: {
              cacheName: "api-cache",
              expiration: { maxEntries: 50, maxAgeSeconds: 86400 },
            },
          },
        ],
      },
      includeAssets: ["favicon.svg", "robots.txt", "apple-touch-icon.png"],
      manifest: {
        name: "AI パーソナルラジオ局",
        short_name: "AI Radio",
        description: "GitHub Actions で自動生成されるAIパーソナルラジオ局",
        start_url: "./",
        display: "standalone",
        background_color: "#ffffff",
        theme_color: "#3b82f6",
        icons: [
          {
            src: "/pwa-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "/pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
          },
        ],
      },
    }),
  ],
  build: {
    outDir: "dist",
    sourcemap: true,
  },
  server: {
    port: 5173,
    open: true,
  },
});
