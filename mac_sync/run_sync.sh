#!/bin/bash
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd "/path/to/Personal Dashboard/mac_sync"
python3 sync_engine.py >> sync_engine.log 2>&1
