#!/bin/bash
# Lightweight backup script for critical files
# Usage: ./backup_critical_file.sh <file_path>

if [ $# -eq 0 ]; then
    echo "Usage: $0 <file_path>"
    echo "Creates timestamped backup before making changes to critical files"
    exit 1
fi

FILE_PATH="$1"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

if [ ! -f "$FILE_PATH" ]; then
    echo "File not found: $FILE_PATH"
    exit 1
fi

# Determine backup location based on file type
if [[ "$FILE_PATH" == templates/* ]]; then
    BACKUP_DIR="templates/backups"
    mkdir -p "$BACKUP_DIR"
    FILENAME=$(basename "$FILE_PATH" .html)
    BACKUP_PATH="$BACKUP_DIR/${FILENAME}_BACKUP_${TIMESTAMP}.html"
else
    # For other files, create backup in same directory
    DIR=$(dirname "$FILE_PATH")
    FILENAME=$(basename "$FILE_PATH")
    BACKUP_PATH="${DIR}/${FILENAME}.backup.${TIMESTAMP}"
fi

cp "$FILE_PATH" "$BACKUP_PATH"
echo "✅ Backup created: $BACKUP_PATH"

# Also commit current state as safety measure
git add "$FILE_PATH"
git commit -m "🔒 AUTO-BACKUP: Saving state before modifying $FILE_PATH

Created backup: $BACKUP_PATH
Timestamp: $TIMESTAMP

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo "✅ Current state committed to git"