#!/bin/bash
echo "🚀 启动 Apple Reminders <-> Notion 双向同步引擎"
echo "引擎将每隔 5 分钟 (300秒) 自动扫描并同步一次..."
echo "请保持此终端窗口开启（可以最小化）。按 Ctrl+C 停止同步。"
echo "--------------------------------------------------------"

while true; do
    python3 sync_engine.py
    sleep 300
done
