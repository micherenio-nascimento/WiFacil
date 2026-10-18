#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
HOST=${1:-termux-a01}
DEST=/data/data/com.termux/files/home/wifacil-turbo

echo "Enviando o código para $HOST:$DEST"
ssh "$HOST" "mkdir -p '$DEST'"
scp "$ROOT"/src/app.py \
    "$ROOT"/src/config.json \
    "$ROOT"/src/firewall.sh \
    "$ROOT"/src/start.sh \
    "$ROOT"/src/stop.sh \
    "$ROOT"/src/.env.example \
    "$HOST:$DEST/"
ssh "$HOST" "cd '$DEST' && chmod 700 firewall.sh start.sh stop.sh && python -m py_compile app.py"

echo "Implantação concluída. Crie $DEST/.env no primeiro uso."
