#!/usr/bin/env node

/**
 * AIPass Drone - Node.js wrapper for global command execution
 * 
 * This wrapper enables the drone command to work globally from any terminal
 * by calling the Python drone.py script with proper path resolution.
 */

const { spawn } = require('child_process');
const path = require('path');

// Get the Python script path (migrated to apps/ directory)
const droneScript = path.join(__dirname, 'apps', 'drone.py');

// Get command line arguments (everything after 'drone')
let args = process.argv.slice(2);

// Note: 'drone create plan' with no folder argument is valid - creates in root
// PowerShell @ consumption only matters when a folder was actually intended

// Spawn Python process with arguments
const python = spawn('python3', [droneScript, ...args], {
    stdio: 'inherit'   // Inherit stdin, stdout, stderr
    // shell: false is default - preserves quoted arguments correctly
});

// Handle process exit
python.on('exit', (code) => {
    process.exit(code || 0);
});

// Handle errors
python.on('error', (err) => {
    console.error('Failed to start drone:', err.message);
    console.error('Make sure Python is installed and in your PATH');
    process.exit(1);
});