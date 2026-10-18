#!/data/data/com.termux/files/usr/bin/bash
set -eu
cd "$(dirname "$0")"
mkdir -p data
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi
if [ -f data/server.pid ] && kill -0 "$(cat data/server.pid)" 2>/dev/null; then
  echo "WiFácil Turbo já está em execução (PID $(cat data/server.pid))"
  exit 0
fi
nohup python app.py >> data/server.log 2>&1 &
echo $! > data/server.pid
sleep 1
kill -0 "$(cat data/server.pid)"
echo "WiFácil Turbo iniciado em http://127.0.0.1:8080"
