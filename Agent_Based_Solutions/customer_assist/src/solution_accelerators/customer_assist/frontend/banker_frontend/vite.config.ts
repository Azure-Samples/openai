// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "./build",
    emptyOutDir: true,
    sourcemap: false,
  },
  server: {
    host: "localhost",
    port: 3000,
    proxy: {
      "/api": {
        target: process.env.VITE_BACKEND_URI || "http://localhost:5000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
