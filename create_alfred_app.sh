#!/bin/bash
# Create a proper ALFRED Mac Application

APP_NAME="ALFRED"
APP_DIR="/Users/jeffgreenfield/dev/ff_draft_vibe/$APP_NAME.app"

echo "🏈 Creating ALFRED Mac Application..."
echo "===================================="

# Remove old app if exists
if [ -d "$APP_DIR" ]; then
    echo "Removing old app..."
    rm -rf "$APP_DIR"
fi

# Create app structure
echo "Creating app structure..."
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Create the main executable
cat > "$APP_DIR/Contents/MacOS/ALFRED" << 'EOF'
#!/bin/bash
# ALFRED Fantasy Football Draft Assistant

PROJECT_DIR="/Users/jeffgreenfield/dev/ff_draft_vibe"
PORT=5555

# Change to project directory
cd "$PROJECT_DIR" || {
    osascript -e 'display alert "ALFRED Error" message "Cannot find project directory at '$PROJECT_DIR'" as critical'
    exit 1
}

# Check if server is already running
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    # Server already running, just open browser
    open "http://localhost:$PORT/"
else
    # Open Terminal and run the server
    osascript -e '
    tell application "Terminal"
        activate
        do script "cd \"'$PROJECT_DIR'\" && python3 alfred_clean.py"
    end tell'
    
    # Wait for server to start
    sleep 3
    
    # Open browser
    open "http://localhost:$PORT/"
fi
EOF

chmod +x "$APP_DIR/Contents/MacOS/ALFRED"

# Create Info.plist
cat > "$APP_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>ALFRED</string>
    <key>CFBundleIdentifier</key>
    <string>com.alfred.fantasyfootball</string>
    <key>CFBundleName</key>
    <string>ALFRED</string>
    <key>CFBundleDisplayName</key>
    <string>ALFRED Fantasy Football</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.12</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
EOF

echo "✅ ALFRED.app created successfully!"
echo ""
echo "You can now:"
echo "1. Copy to Applications: cp -r '$APP_DIR' /Applications/"
echo "2. Copy to Desktop: cp -r '$APP_DIR' ~/Desktop/"
echo "3. Double-click ALFRED.app to launch"
echo ""
echo "The app is located at: $APP_DIR"