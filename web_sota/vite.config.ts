import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 10884,
    host: "127.0.0.1",
    proxy: {
      // Same-origin fetches from the React app during dev (backend: start.ps1 port 10885)
      "/api": { target: "http://127.0.0.1:10885", changeOrigin: true },
      "/mcp": { target: "http://127.0.0.1:10885", changeOrigin: true, ws: true },
    },
  },
});
