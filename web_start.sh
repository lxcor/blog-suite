#!/bin/bash
set -e

SESSION="web-blog-suite"

cd "$(dirname "$0")"

tmux kill-session -t "$SESSION" 2>/dev/null || true

tmux new-session -d -s "$SESSION" -c "$(pwd)" \
    "cd sandbox && source .venv/bin/activate && python manage.py runserver_plus sophia.lxcor.com:9050 \
        --cert-file /etc/letsencrypt/live/sophia.lxcor.com/fullchain.pem \
        --key-file  /etc/letsencrypt/live/sophia.lxcor.com/privkey.pem \
        --insecure"

echo "Started in tmux session '$SESSION' (attach: tmux attach -t $SESSION)"
