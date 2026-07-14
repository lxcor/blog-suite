#!/bin/bash
set -e

PROJECT=$(basename "$(cd "$(dirname "$0")" && pwd)")
SESSION="crc-$PROJECT"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -c "$PROJECT_DIR" "claude --remote-control $SESSION"
echo "Started CRC in tmux session '$SESSION' (attach: tmux attach -t $SESSION)"
