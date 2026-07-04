# Personal Dashboard

A fully integrated, multi-platform personal dashboard that syncs Apple Reminders, Notion, and iOS Lock Screen Widgets to streamline your task management.

## 🌟 Features

- **Bidirectional Sync**: Seamlessly syncs tasks between Apple Reminders and Notion databases.
- **iOS Lock Screen Widgets**: Highly customizable iOS widgets via Scriptable, displaying your most critical tasks directly on your lock screen.
- **Intelligent LLM Integration**: Uses OpenAI to smartly truncate task titles and intelligently manage note tags.
- **Automated Deployment**: Built-in Python scripts to inject tokens and deploy clean code to your iOS devices.

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js & npm (for iOS widget local testing)
- A Notion API Token and Database ID

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/personal-dashboard.git
   cd personal-dashboard
   ```
2. Install Python dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Set up environment variables and config:
   - Copy `.env.template` to `.env` (or create one in the `server/` directory) and add your keys.
   - Copy `server/config.template.json` to `server/config.json` and customize your device names and preferences.

### Running the Sync Engine
You can run the Apple Reminders to Notion sync engine manually:
```bash
python mac_sync/sync_engine.py
```

### Deploying iOS Widgets
Generate your personalized iOS Widget scripts (which safely injects your API tokens):
```bash
python tools/build_ios_widgets.py
```
Then copy the files from `dist/ios_widgets/` to your iOS Scriptable app.

## 🤝 Contributing
Contributions are welcome! Please check out [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to proceed.

## 📝 License
This project is licensed under the [MIT License](LICENSE).
