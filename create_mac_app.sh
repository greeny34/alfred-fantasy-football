#!/bin/bash
# Create macOS Application for ALFRED

echo "Creating ALFRED.app..."

# Create app structure
mkdir -p "ALFRED.app/Contents/MacOS"
mkdir -p "ALFRED.app/Contents/Resources"

# Create the main executable
cat > "ALFRED.app/Contents/MacOS/ALFRED" << 'EOF'
#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$DIR/../../.." && pwd )"

# Change to project directory
cd "$PROJECT_DIR"

# Use Terminal to run the app (so you can see output)
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_DIR' && source .venv/bin/activate && python src/engines/draft_assistant_app.py\""
EOF

# Make it executable
chmod +x "ALFRED.app/Contents/MacOS/ALFRED"

# Create Info.plist
cat > "ALFRED.app/Contents/Info.plist" << 'EOF'
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
</dict>
</plist>
EOF

# Create a simple icon (football emoji as text file for now)
echo "🏈" > "ALFRED.app/Contents/Resources/icon.txt"

echo "✅ ALFRED.app created successfully!"
echo ""
echo "You can now:"
echo "1. Double-click ALFRED.app to launch"
echo "2. Drag ALFRED.app to your Applications folder"
echo "3. Add it to your Dock for easy access"