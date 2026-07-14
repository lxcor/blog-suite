#!/bin/bash
set -e

SESSION="web-blog-suite"

tmux kill-session -t "$SESSION" 2>/dev/null || true
fuser -k 9050/tcp 2>/dev/null || true
