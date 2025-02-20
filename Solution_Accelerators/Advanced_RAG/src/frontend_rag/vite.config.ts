/*
 *   Copyright (c) 2024
 *   All rights reserved.
 */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    build: {
        outDir: "./build",
        emptyOutDir: true,
        sourcemap: false
    },
    server: {
        host: "localhost",
        port: 3000
    }
});
