#!/bin/bash
set -e
URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
echo "Downloading cloudflared..."
curl -fsSL "$URL" -o "$HOME/cloudflared"
chmod +x "$HOME/cloudflared"
echo "Done. Run: ~/cloudflared tunnel --url http://localhost:8080"
