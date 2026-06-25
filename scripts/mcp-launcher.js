#!/usr/bin/env node

const { spawn } = require("node:child_process");

const args = process.argv.slice(2);

if (args.length === 0) {
  console.error("Usage: node scripts/mcp-launcher.js <package> [args...]");
  process.exit(1);
}

const [packageName, ...rawArgs] = args;

const resolvedArgs = rawArgs.map((value) => {
  if (!value.startsWith("env:")) {
    return value;
  }

  const envName = value.slice(4);
  const envValue = process.env[envName];

  if (!envValue) {
    console.error(`Missing required environment variable: ${envName}`);
    process.exit(1);
  }

  return envValue;
});

const npxCommand = process.platform === "win32" ? "npx.cmd" : "npx";
const child = spawn(npxCommand, ["-y", packageName, ...resolvedArgs], {
  stdio: "inherit",
  env: process.env,
});

child.on("error", (error) => {
  console.error(`Failed to start ${packageName} via ${npxCommand}:`, error.message);
  process.exit(1);
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }

  process.exit(code ?? 1);
});
