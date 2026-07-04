#!/bin/bash
set -e

echo "==========================================="
echo " Installing NotionSync Background Daemon"
echo "==========================================="

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APP_NAME="NotionSync.app"
APP_PATH="$DIR/$APP_NAME"
PLIST_NAME="com.user.reminders_sync.plist"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME"

echo "1. Building AppleScript wrapper app at $APP_PATH..."
# We use osacompile to generate a native macOS App that runs our Python script.
# This app serves as the host for TCC (Privacy) permissions.
osacompile -e 'do shell script "export PATH=\"/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin\"; cd \"'"$DIR"'\" && /usr/bin/python3 sync_engine.py >> sync_engine.log 2>&1"' -o "$APP_PATH"

echo "2. Generating launchd plist..."
cat <<EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.reminders_sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/open</string>
        <string>-W</string>
        <string>-g</string>
        <string>$APP_PATH</string>
    </array>
    <key>StartInterval</key>
    <integer>300</integer>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

echo "3. Loading daemon into launchd..."
# Unload if it already exists to refresh
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo "==========================================="
echo "✅ Installation Complete!"
echo "IMPORTANT: macOS Gatekeeper might require you to explicitly allow Reminders access."
echo "Please run the app manually ONCE by executing:"
echo "    open -W -g \"$APP_PATH\""
echo "And click 'Allow' if prompted."
echo "After that, the background daemon will silently run every 5 minutes."
echo "Logs will be written to: $DIR/sync_engine.log"
echo "==========================================="
