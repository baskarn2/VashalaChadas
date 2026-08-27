#!/usr/bin/env bash
# Quick launcher script for Chandojñānam Local App

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ -f "$DIR/.venv/bin/python" ]; then
    PYTHON_EXEC="$DIR/.venv/bin/python"
elif [ -f "$DIR/venv/bin/python" ]; then
    PYTHON_EXEC="$DIR/venv/bin/python"
else
    PYTHON_EXEC="python3"
fi

echo "Starting Chandojñānam using $PYTHON_EXEC ..."
"$PYTHON_EXEC" run.py "$@"
