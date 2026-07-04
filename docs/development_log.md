# Development Log & History

## V1: Inception
The project originated as an experimental integration between Notion and Apple Reminders to solve the "fragmented task management" problem. The initial architecture relied on heavy server-side polling.

## V2: The Sync Engine
We migrated to a local Mac-based `sync_engine.py` to leverage the native Swift CLI (`reminders_cli.swift`). This enabled actual bidirectional sync using a 3-way merge logic and Last-Writer-Wins (LWW) conflict resolution based on `lastModifiedDate`.

## V3: Open Source Standardization (Current)
- Codebase fully translated to English.
- Security refactored to use `.env` and `build_ios_widgets.py` injection, keeping private keys completely isolated from Git history.
- Added Jest (JS) and Pytest (Python) testing suites for CI/CD readiness.
