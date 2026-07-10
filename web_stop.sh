#!/bin/bash
set -e

fuser -k 9050/tcp 2>/dev/null || true
