#!/usr/bin/env node
/**
 * Preflight check — verifies Node 18+ and Python 3.10+ are available.
 * Run automatically by `npm run setup`.
 */

const { execSync } = require('child_process')

const MIN_NODE = 18
const MIN_PYTHON = [3, 10]

let ok = true

// Check Node.js version
const nodeMajor = parseInt(process.version.slice(1).split('.')[0], 10)
if (nodeMajor < MIN_NODE) {
  console.error(`\x1b[31m✗ Node.js ${MIN_NODE}+ required (found ${process.version})\x1b[0m`)
  ok = false
} else {
  console.log(`\x1b[32m✓ Node.js ${process.version}\x1b[0m`)
}

// Check Python version
try {
  const pyVersionRaw = execSync('python3 --version 2>&1', { encoding: 'utf8' }).trim()
  const match = pyVersionRaw.match(/Python (\d+)\.(\d+)/)
  if (match) {
    const major = parseInt(match[1], 10)
    const minor = parseInt(match[2], 10)
    if (major < MIN_PYTHON[0] || (major === MIN_PYTHON[0] && minor < MIN_PYTHON[1])) {
      console.error(`\x1b[31m✗ Python ${MIN_PYTHON.join('.')}+ required (found ${major}.${minor})\x1b[0m`)
      ok = false
    } else {
      console.log(`\x1b[32m✓ ${pyVersionRaw}\x1b[0m`)
    }
  } else {
    console.error(`\x1b[31m✗ Could not parse Python version: ${pyVersionRaw}\x1b[0m`)
    ok = false
  }
} catch (e) {
  console.error('\x1b[31m✗ Python 3 not found. Install Python 3.10+ from https://python.org\x1b[0m')
  ok = false
}

// Check pip
try {
  execSync('python3 -m pip --version', { stdio: 'pipe' })
  console.log('\x1b[32m✓ pip available\x1b[0m')
} catch (e) {
  console.error('\x1b[31m✗ pip not found. Install with: python3 -m ensurepip\x1b[0m')
  ok = false
}

if (!ok) {
  console.error('\n\x1b[31mPreflight checks failed. Fix the issues above and try again.\x1b[0m')
  process.exit(1)
} else {
  console.log('\n\x1b[32mAll checks passed. Ready to install.\x1b[0m\n')
}
