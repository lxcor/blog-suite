#!/bin/bash
set -e

cd "$(dirname "$0")/sandbox"

source .venv/bin/activate

python manage.py runserver_plus sophia.lxcor.com:9050 \
    --cert-file /etc/letsencrypt/live/sophia.lxcor.com/fullchain.pem \
    --key-file  /etc/letsencrypt/live/sophia.lxcor.com/privkey.pem \
    --insecure
