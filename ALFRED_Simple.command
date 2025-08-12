#!/bin/bash
# ALFRED Simple Draft Assistant

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "🏈 Starting ALFRED Simple Draft Assistant..."
echo "================================"
echo ""

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "Installing Flask..."
    pip install flask
fi

# Run the simple draft assistant
python simple_working_draft.py