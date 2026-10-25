#!/bin/bash

source venv/bin/activate

if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "Activated: $VIRTUAL_ENV"
else
    echo "Failed to activate virtual environment"
fi

# run the following command to activate virtual environment
# source activate.sh
# not ./activate.sh
