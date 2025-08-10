#!/bin/bash

echo "🏈 Creating Fantasy Football Draft Assistant App Bundle"
echo "====================================================="

# Create the app bundle structure
APP_NAME="Fantasy Football Draft Assistant 2025"
APP_DIR="${APP_NAME}.app"
CONTENTS_DIR="${APP_DIR}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"
RESOURCES_DIR="${CONTENTS_DIR}/Resources"

# Remove existing app if it exists
if [ -d "${APP_DIR}" ]; then
    echo "🗑️  Removing existing app bundle..."
    rm -rf "${APP_DIR}"
fi

# Create directory structure
echo "📁 Creating app bundle structure..."
mkdir -p "${MACOS_DIR}"
mkdir -p "${RESOURCES_DIR}"

# Create the Info.plist file
echo "📄 Creating Info.plist..."
cat > "${CONTENTS_DIR}/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>Fantasy Football Draft Assistant 2025</string>
    <key>CFBundleExecutable</key>
    <string>draft_assistant</string>
    <key>CFBundleIconFile</key>
    <string>app_icon</string>
    <key>CFBundleIdentifier</key>
    <string>com.draftassistant.app</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Fantasy Football Draft Assistant 2025</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.9</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create the main executable script
echo "🚀 Creating main executable..."
cat > "${MACOS_DIR}/draft_assistant" << 'EOF'
#!/bin/bash

# Get the directory where the app bundle is located
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUNDLE_DIR="$(dirname "$(dirname "${APP_DIR}")")"
RESOURCES_DIR="${BUNDLE_DIR}/Contents/Resources"

# Change to the resources directory
cd "${RESOURCES_DIR}"

# Run the Python app
python3 draft_assistant_app.py
EOF

# Make the executable script runnable
chmod +x "${MACOS_DIR}/draft_assistant"

# Copy the Python files to Resources
echo "📋 Copying Python files to app bundle..."
cp draft_assistant_app.py "${RESOURCES_DIR}/"

# Create a simple icon (text-based)
echo "🎨 Creating app icon..."
cat > "${RESOURCES_DIR}/app_icon.icns" << EOF
This would be an icon file in a real app
EOF

echo ""
echo "✅ App bundle created successfully!"
echo "📱 Location: ${APP_DIR}"
echo ""
echo "🎯 To run: Double-click '${APP_NAME}.app' in Finder"
echo ""
echo "Note: You may need to right-click and select 'Open' the first time"
echo "      to bypass macOS security restrictions."