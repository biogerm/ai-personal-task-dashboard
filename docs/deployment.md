# Deployment Guide

This document outlines the hardware and deployment requirements for the Personal Dashboard.

## Hardware Requirements (Device Inventory)
Based on the current topology, the following devices are typically utilized:
1. **Always-On Mac (e.g., Mac Mini)**
   - Acts as the central Sync Engine host.
   - Required to run `reminders_cli.swift` due to Apple's native APIs.
2. **iPhone / iPad**
   - End-user devices displaying the Scriptable Lock Screen widgets.
3. **Smart Display (e.g., Google Nest Hub / Chromecast)**
   - Used for casting the dashboard UI.
   - Controlled via `catt` (DashCast).

## Step-by-Step Deployment

### 1. Backend Server & Sync Engine (Mac Mini)
1. Clone the repository and install dependencies via `requirements.txt`.
2. Copy `.env.template` to `.env` (located in the `server/` directory) and configure it with your `NOTION_API_TOKEN`, `NOTION_DATABASE_ID`, and other variables.
3. Copy `server/config.template.json` to `server/config.json` and configure your casting devices and list names.
4. Set up the Sync Engine background daemon:
   ```bash
   cd mac_sync
   ./install.sh
   # Grant TCC Reminders permission by running the app once
   open -W -g NotionSync.app
   ```
5. Start the Flask API:
   ```bash
   nohup python server/app.py > server.log 2>&1 &
   ```

### 2. iOS Widgets
1. Run `python tools/build_ios_widgets.py` on your host machine to generate the final JS files.
2. Transfer the contents of `dist/ios_widgets/NotionLockScreen_Left.js` and `NotionLockScreen_Right.js` to the Scriptable app on your iOS device.
3. Add a Scriptable Lock Screen widget and select the script.

### 3. Dashboard Casting (Nest Hub)
To cast the web interface to a Chromecast device:
```bash
# Note: Always stop the current cast before starting a new one to prevent caching issues.
python -m catt.cli -d 'Nest Hub Name' stop
sleep 3
python -m catt.cli -d 'Nest Hub Name' cast_site 'http://<YOUR_MAC_IP>:3000/'
```
