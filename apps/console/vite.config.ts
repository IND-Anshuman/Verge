import react from "@vitejs/plugin-react";
import { execSync } from "child_process";
import { resolve } from "path";
import { defineConfig } from "vite";

// Detect if the FastAPI gateway is actively running on port 8000.
// If it is offline, we disable the proxy configuration completely to prevent Vite
// from spamming ECONNREFUSED connection traces to the terminal.
let isBackendUp = false;
try {
  const output = execSync("netstat -ano", { encoding: "utf8" });
  isBackendUp = output.includes(":8000 ");
} catch {
  // Fallback to false if command fails
}

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },
  server: {
    port: 5173,
    proxy: isBackendUp
      ? {
          "/api": {
            target: "http://localhost:8000",
            changeOrigin: true,
          },
          "/health": {
            target: "http://localhost:8000",
            changeOrigin: true,
          },
        }
      : {},
  },
});
