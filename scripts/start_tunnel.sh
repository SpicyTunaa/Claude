#!/bin/bash
# Start cloudflared quick tunnel, write URL to /tmp/cloudflared_url.txt
# main.py reads this file to set WEBAPP_URL automatically.

LOGFILE=/tmp/cloudflared.log
URLFILE=/tmp/cloudflared_url.txt

rm -f "$URLFILE"

"$HOME/cloudflared" tunnel --url "http://localhost:${PORT:-8080}" > "$LOGFILE" 2>&1 &
CF_PID=$!

# Wait up to 30s for the tunnel URL to appear in logs
for i in $(seq 1 30); do
    URL=$(grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' "$LOGFILE" 2>/dev/null | head -1)
    if [ -n "$URL" ]; then
        echo "$URL" > "$URLFILE"
        echo "Cloudflared tunnel ready: $URL"
        break
    fi
    sleep 1
done

if [ ! -f "$URLFILE" ]; then
    echo "WARNING: cloudflared URL not detected after 30s" >&2
fi

# Keep running — forward signals to cloudflared
trap "kill $CF_PID 2>/dev/null" EXIT INT TERM
wait $CF_PID
