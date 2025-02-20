/*
 *   Copyright (c) 2024 
 *   All rights reserved.
 */
import express from "express";
import cors from 'cors';
import path from "path";
import { fileURLToPath } from "url";
import { dirname } from "path";

const app = express();
app.use(cors());
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Serve static files from the 'build' directory
app.use(express.static(path.join(__dirname, "build")));

app.get("*", (req, res) => {
    res.sendFile(path.join(__dirname, "build", "index.html"));
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
