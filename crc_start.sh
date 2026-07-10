#!/bin/bash
set -e

PROJECT=$(basename "$(cd "$(dirname "$0")" && pwd)")
SESSION="crc-$PROJECT"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "CRC session already running: $SESSION"
    exit 0
fi

tmux new-session -d -s "$SESSION" -c "$PROJECT_DIR" "claude --remote-control $SESSION"
echo "Started CRC session: $SESSION"
