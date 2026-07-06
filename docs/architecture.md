# Architecture Overview

The Personal Dashboard is a multi-tier system composed of a Python-based synchronization engine, a Flask web backend, and iOS Scriptable widgets.

## Core Components

### 1. Sync Engine (`mac_sync/sync_engine.py`)
A standalone Python daemon designed to run on macOS. It serves as the primary bridge between Apple Reminders and Notion.
- **Apple Reminders CLI**: Uses a Swift script (`reminders_cli.swift`) to extract and update native Apple Reminders data.
- **Notion API**: Communicates with Notion via the official REST API.
- **Conflict Resolution**: Implements a robust 3-way merge strategy utilizing timestamp-based Last-Writer-Wins (LWW) to resolve bidirectional conflicts.

### 2. Flask API Server (`server/app.py`)
A lightweight web server providing API endpoints for external interactions, primarily voice commands and smart integrations.
- **Task Merger**: Merges data streams from Notion and Apple Reminders into a unified view.
- **LLM Integration**: Interfaces with OpenAI to dynamically summarize long tasks and intelligently route voice queries.

### 3. iOS Widgets (`ios_widgets/`)
JavaScript modules executed by the iOS Scriptable application.
- Fetches the unified task list.
- Renders high-priority tasks and smart context directly onto the iOS Lock Screen.
- Designed to run within the memory and network constraints of the iOS Widget environment.

## Deployment Topology
- **Sync Engine**: Runs as a `launchd` daemon on the always-on Mac Mini (required for local Apple Reminders TCC access).
- **Flask Server**: Runs on the Mac Mini (or a local Linux server like Raspberry Pi via `systemd` using the provided `dashboard.service`), listening for local network requests.
- **End-User Devices**: iPhones rendering the widgets, fetching data from the Flask Server.
