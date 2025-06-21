#!/bin/bash
set -o errexit

# Install system dependencies
apt-get update
apt-get install -y --no-install-recommends build-essential curl

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
export PATH="$HOME/.cargo/bin:$PATH"

# Install Python dependencies
pip install --no-cache-dir -r requirements.txt
