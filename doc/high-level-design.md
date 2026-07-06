# Personal Dashboard — 概要设计文档

> 版本: v2.0  
> 日期: 2026-07-03  
> 依据: [proposal.md](file:///Users/qin.an@hm.com/Developer/antigravity/Personal%20Dashboard/doc/proposal.md), 以及项目后续的多次迭代和优化

---

## 1. 系统总览

本系统是一个运行在 Raspberry Pi 3B+ 上的 **Web 应用**，由后端服务和前端网页两部分组成。后端负责定时从 Apple Reminders (CalDAV) 和 Notion (REST API) 拉取任务数据、合并排序后通过 JSON API 暴露；前端是一个响应式网页，各显示设备（Samsung M7、Nest Hub、电视、iPhone）通过浏览器或投屏访问同一个网页。

为了保证投屏的长效稳定，项目升级并使用了 **Python 3.9 虚拟环境** (`/home/pi/dashboard-venv-3.9`) 替代原有的系统级 Python 3.5，并全面采用 **Systemd (`dashboard.service`)** 接管进程的生命周期，从而避免了 SSH 会话断开导致的进程终止，并支持崩溃自动恢复。

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Raspberry Pi 3B+ (Headless)                     │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────┐        │
│  │                      Dashboard 应用 (Systemd 托管)           │        │
│  │                                                            │        │
│  │  ┌──────────────────────────────────────────────────┐      │        │
│  │  │               后端服务 (Python 3.9 Venv + Flask)   │      │        │
│  │  │                                                  │      │        │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │      │        │
│  │  │  │ Reminders   │  │   Notion    │  │  Task    │ │      │        │
│  │  │  │  Connector  │  │  Connector  │  │ Merger   │ │      │        │
│  │  │  └──────┬──────┘  └──────┬──────┘  └────┬─────┘ │      │        │
│  │  │         │                │               │       │      │        │
│  │  │  ┌──────┴────────────────┴───────────────┴─────┐ │      │        │
│  │  │  │              Data Cache                     │ │      │        │
│  │  │  └──────────────────────┬───────────────────── │ │      │        │
│  │  │                         │                      │ │      │        │
│  │  │  ┌──────────────────────┴──────────────────┐   │ │      │        │
│  │  │  │            REST API Layer               │   │ │      │        │
│  │  │  │  GET /api/tasks    GET /api/voice-summary│   │ │      │        │
│  │  │  └──────────────────────┬──────────────────┘   │ │      │        │
│  │  │                         │                      │ │      │        │
│  │  │  ┌──────────────────────┴──────────────────┐   │ │      │        │
│  │  │  │             Screen Cast Controller      │   │ │      │        │
│  │  │  │  (自动定时使用 catt 投屏至 Nest Hub)       │   │ │      │        │
│  │  │  └──────────────────────┬──────────────────┘   │ │      │        │
│  │  └─────────────────────────┼──────────────────────┘ │      │        │
│  │                            │                        │      │        │
│  │  ┌─────────────────────────┴──────────────────────┐ │      │        │
│  │  │         前端静态文件 (HTML + CSS + JS)           │ │      │        │
│  │  │  Flask static serving (带 No-Cache Headers)    │ │      │        │
│  │  └────────────────────────────────────────────────┘ │      │        │
│  └────────────────────────────────────────────────────────────┘        │
│                                                                        │
│  ┌──────────────────────────────────────┐                              │
│  │     现有服务 (OpenVPN, etc.) — 不变   │                              │
│  └──────────────────────────────────────┘                              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 模块划分

系统划分为 **7 个模块**。下表列出每个模块的职责边界：

| 模块 | 名称 | 层 | 职责 |
|------|------|-----|------|
| **M1** | Reminders Connector | 后端 | 通过 CalDAV 协议连接 iCloud，拉取指定 Lists 中的未完成任务 |
| **M2** | Notion Connector | 后端 | 通过 Notion REST API 查询指定 Database，拉取未完成的项目/想法 |
| **M3** | Task Merger | 后端 | 合并 M1 和 M2 的数据，统一数据模型，排序，缓存 |
| **M4** | REST API Layer | 后端 | 对外暴露 HTTP JSON API，供前端和语音模块调用 |
| **M5** | Dashboard Frontend | 前端 | 响应式网页，展示任务列表，深色/浅色自动切换（纯视觉，不控制屏幕本身） |
| **M6** | Voice Summary | 后端 | 生成纯文本任务摘要，供 Google Home Routine 通过 Webhook 调用 |
| **M7** | Screen Cast | 后端 | 后端定时器使用 `catt` 指令，负责强制推流网页至 Google Hub 并执行严格的夜间息屏逻辑 |

---

## 3. 各模块详细设计

### 3.1 M1 — Reminders Connector
职责与早期架构一致：通过 CalDAV 从 iCloud 拉取 `COMPLETED = false` 的任务，解析 `VTODO` 格式，提取时间与列表信息。遇到连接失败时，静默记录日志并使用之前的缓存数据，不阻塞前端显示。

### 3.2 M2 — Notion Connector
职责一致。使用 Filter 排除已完成的项目，提取属性如优先级（`Priority`）。最新版中增强了对优先级值的精确匹配（如 `1 - High ‼️`），以应对复杂的图标后缀问题。

### 3.3 M3 — Task Merger
后端的**核心调度与数据层**。每 5 分钟并发/顺序调用 M1 和 M2，合并数据并在内存中缓存 DashboardData。提供独立的优先级权重与过期逻辑计算。

### 3.4 M4 — REST API Layer
提供无状态的 HTTP API：
- `GET /api/tasks`：返回 JSON 格式的任务列表。所有 API 和静态文件已全局注入 `Cache-Control: no-cache, no-store, must-revalidate`，避免通过带参数的 URL 来清除前端缓存。
- `GET /api/voice-summary`：纯文本，供语音设备朗读。
- `GET /api/health`：提供状态监控接口。

### 3.5 M5 — Dashboard Frontend
单页 HTML/CSS/JS。每 60 秒通过 Fetch 拉取最新数据。支持双栏和大屏/小屏的响应式布局。
**主题切换：** 前端在 20:00 - 06:00 期间自动挂载 `dark-theme` 的 CSS 类名，使网页变为深色模式。这完全是视觉表现上的夜间模式，不代表让物理设备屏幕熄灭。

### 3.6 M6 — Voice Summary
针对 Google Home 语音设备的纯文本输出摘要，提供高度可读的任务与项目汇总。

### 3.7 M7 — Screen Cast Controller
引入 `catt` (Cast All The Things) 进行局域网 Chromecast 设备控制。包含核心特性：
- 每 10 分钟自动检查 Hub 当前状态（DashCast 或待机画报）。
- 如果检测到非工作状态（用户没有在使用别的功能，比如听歌）且处于应用待机模式时，将 Dashboard 推流至屏幕。
- **强制息屏 (Rest Mode)**: 在配置中的指定时间段（例如凌晨 1:00 至 6:00），会强制调用 `catt stop` 关闭投屏并防止在夜间重新点亮。

---

## 4. 配置与日志管理

- **.env**: 存储 `ICLOUD_USERNAME` / `ICLOUD_APP_PASSWORD` / `NOTION_API_TOKEN`
- **config.json**:
```json
{
  "theme": {
    "lightStartHour": 6,
    "lightEndHour": 20
  },
  "cast": {
    "nestHubName": "Rock Hub",
    "restStartHour": 1,
    "restEndHour": 6
  }
}
```
配置被明确分离为 UI 主题 (`theme`) 与投屏硬件休眠 (`cast`) 两部分。
- **日志**: 使用 Python `logging.handlers.RotatingFileHandler` 写入 `app.log`，限制大小 10MB 并滚动保留，避免长期运行导致存储耗尽。

---

## 5. 进程模型与部署
服务基于 **Systemd** 的后台托管服务部署。
`/etc/systemd/system/dashboard.service`:
```ini
[Unit]
Description=Personal Dashboard Flask App
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/dashboard/server
ExecStart=/home/pi/dashboard-venv-3.9/bin/python src/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```
- 使用独立编译的 Python 3.9 venv，彻底避开了系统默认 Python 3.5 带来的依赖兼容性和安全问题。
- `systemd` 防止了系统在断开 SSH (`systemd-logind` 默认策略) 以后意外清除残留孤儿进程（原使用 `nohup` 的痛点）。
