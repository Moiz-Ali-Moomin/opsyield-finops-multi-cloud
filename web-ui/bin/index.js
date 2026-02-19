#!/usr/bin/env node

import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const distPath = path.join(__dirname, "../dist");

console.log("🚀 Starting OpsYield frontend...");

spawn("npx", ["serve", "-s", distPath, "-l", "5173"], {
  stdio: "inherit",
  shell: true
});
