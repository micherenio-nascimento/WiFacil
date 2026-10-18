#!/data/data/com.termux/files/usr/bin/bash
set -eu
cd "$(dirname "$0")"
if [ -f data/server.pid ]; then
  kill "$(cat data/server.pid)" 2>/dev/null || true
  rm -f data/server.pid
fi
echo "WiFácil Turbo parado"
