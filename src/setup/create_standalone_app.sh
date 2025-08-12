#!/bin/bash
# Create standalone macOS Application for ALFRED

echo "Creating standalone ALFRED.app..."

# Remove old app if exists
rm -rf "ALFRED Fantasy Football.app"

# Create app structure
mkdir -p "ALFRED Fantasy Football.app/Contents/MacOS"
mkdir -p "ALFRED Fantasy Football.app/Contents/Resources"

# Create the main executable with HARDCODED path
cat > "ALFRED Fantasy Football.app/Contents/MacOS/ALFRED" << 'EOF'
#!/bin/bash

# Hardcoded project directory
PROJECT_DIR="/Users/jeffgreenfield/dev/ff_draft_vibe"

# Check if project exists
if [ ! -d "$PROJECT_DIR" ]; then
    osascript -e 'display dialog "ALFRED project not found at: '"$PROJECT_DIR"'" buttons {"OK"} default button "OK"'
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    osascript -e 'display dialog "Python virtual environment not found. Please run: pip install -r requirements.txt" buttons {"OK"} default button "OK"'
    exit 1
fi

# Use Terminal to run the app
osascript << EOA
tell application "Terminal"
    activate
    do script "cd '$PROJECT_DIR' && source .venv/bin/activate && python src/engines/draft_assistant_app.py; exit"
end tell
EOA
EOF

# Make it executable
chmod +x "ALFRED Fantasy Football.app/Contents/MacOS/ALFRED"

# Create Info.plist
cat > "ALFRED Fantasy Football.app/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>ALFRED</string>
    <key>CFBundleName</key>
    <string>ALFRED Fantasy Football</string>
    <key>CFBundleIdentifier</key>
    <string>com.alfred.fantasyfootball</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>icon</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.10</string>
</dict>
</plist>
EOF

echo "✅ ALFRED Fantasy Football.app created!"
echo ""
echo "This app will work from ANYWHERE including Applications folder"
echo "because it has the full path hardcoded."
echo ""
echo "To install:"
echo "1. Drag 'ALFRED Fantasy Football.app' to Applications"
echo "2. Double-click to run"