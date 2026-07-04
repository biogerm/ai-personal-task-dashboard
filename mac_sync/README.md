# Apple Reminders <-> Notion Bidirectional Sync Engine

This directory contains the central sync engine that enables real-time, true bidirectional synchronization between Apple Reminders (iOS/macOS) and a Notion Database.

## Architecture

The system consists of three main parts:
1. **iOS Shortcuts (Capture Layer)**: A quick entry shortcut on iPhone/iPad that instantly pushes the task title to Notion and saves the Notion `page_id` back into the Apple Reminder's `Notes` field.
2. **Swift CLI (`reminders_cli.swift`)**: A low-level executable that interfaces with Apple's `EventKit` framework to read and mutate Apple Reminders (Requires explicit macOS Privacy/TCC permissions).
3. **Python Brain (`sync_engine.py`)**: The core engine that orchestrates the sync. It uses a **3-Way Merge** algorithm based on `sync_state.json` and timestamp conflict resolution (`last_edited_time` vs `lastModifiedDate`).

## 3-Way Merge Conflict Resolution
To prevent the "infinite update loop", the engine resolves conflicts at the **property level**:
- It tracks the last known synced state in `sync_state.json`.
- It independently evaluates 5 properties: `Title`, `Notes`, `Due Date`, `Priority`, and `Status`.
- If both Reminders and Notion deviate from the last known state (simultaneous edits), it arbitrates using Last-Writer-Wins based on timestamps.

## Installation & Automation (macOS)

Because of macOS's strict TCC (Transparency, Consent, and Control) privacy restrictions, background daemon scripts (like `launchd` or `cron`) are silently blocked from accessing Apple Reminders. To bypass this, we wrap the Python sync engine inside a native macOS Application.

Because source code and deployment artifacts should be kept separate, **you must generate this Application locally on your machine**.

### 1. Run the Installer
We provide an automated installer that will:
- Dynamically build a macOS wrapper App (`NotionSync.app`) configured for your absolute directory path.
- Generate a `launchd` plist file and install it to `~/Library/LaunchAgents/`.
- Load the daemon to run silently every 5 minutes.

Open your terminal and run:
```bash
cd mac_sync
./install.sh
```

### 2. Grant Initial Authorization
Because Apple strictly regulates Reminders access, you must explicitly grant permission to the wrapper app the very first time it runs.
After running `./install.sh`, execute this in your terminal to trigger the prompt:
```bash
open -W -g NotionSync.app
```
A prompt will appear asking for permission to access your Reminders. Click **Allow**.
*(Note: The app runs completely silently in the background, so you won't see any windows pop up).*

That's it! The background daemon will now silently run every 5 minutes. Logs will be written to `mac_sync/sync_engine.log`.

## Important Note for Front-End Developers

The Dashboard UI should **never** attempt to read from Apple Reminders directly. **Notion is the Single Source of Truth.**

To distinguish between a task originating from Apple Reminders and a task manually created in Notion:
Check the `created_by` ID of the Notion page. 
Tasks synchronized via this engine will have the Notion Integration Bot's ID (e.g., `YOUR_NOTION_BOT_ID`), whereas manually created tasks will have the user's personal account ID.
