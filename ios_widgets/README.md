# Notion Scriptable Widgets (iOS)

This directory contains advanced JavaScript files for iOS widgets powered by [Scriptable](https://scriptable.app/). They allow you to pull tasks directly from a Notion database and display them on your iPhone's Lock Screen and Home Screen.

## Why Does This Exist?
Standard iOS widgets often suffer from poor space utilization and dumb text truncation (e.g., cutting off important task names with `...`). This project solves these issues through two major innovations:

1. **Dual-Screen Architecture**: By separating tasks into two distinct widgets (Left and Right), we maximize information density. 
2. **AI-Powered Visual Truncation**: Instead of letting iOS awkwardly cut off long task names, we calculate the exact visual width available on your specific screen size. We then use OpenAI's GPT-4o-mini to intelligently rewrite and abbreviate the task name in natural language so it fits perfectly on a single line without losing core meaning.

## Features

- **Dual Modes (Left/Right)**: 
  - `NotionLockScreen_Left.js`: Designed for immediate action. Displays `Past Due` and `Today` tasks. On lock screens, it drops future tasks entirely to save space.
  - `NotionLockScreen_Right.js`: Designed as an extension widget. Displays Future tasks (`Within 30 Days`, `No Date`, `After 30 Days`).
- **Intelligent LLM Shortening**: Automatically truncates long Notion task titles using the OpenAI GPT-4o-mini API.
  - Dynamically calculates visual budget (Chinese characters = 2 width, English letters = 1 width).
  - Deducts dynamic prefix lengths (like `10d!!`) to provide exact budgets to the LLM.
  - Includes an AI "Retry Engine": if the LLM hallucinates and ignores the length limit, it bounces the text back for further truncation.
- **Dynamic Caching**: The shortened titles are cached persistently on the device based on the available budget length. If a deadline gets closer and the date prefix shrinks, the widget automatically requests a slightly longer name to fill the freed-up space!
- **Responsive Layout**: Modifies lines and padding dynamically to fit the exact widget family (`small`, `medium`, `large`, `accessoryRectangular`).

## Build & Setup Instructions

To keep your API keys secure and out of version control, the source code in this directory uses placeholders (like `__NOTION_API_KEY__`). You must build the final scripts before copying them to your phone.

1. **Configure Environment Variables**: Ensure your `server/.env` file is populated with your `NOTION_API_TOKEN`, `NOTION_DATABASE_ID`, `OPENAI_API_KEY`, and `APP_LOCALE`.
2. **Build the Widgets**: Run the build script from the repository root:
   ```bash
   python3 tools/build_ios_widgets.py
   ```
   This will inject your secure keys and generate runnable `.js` files in the `dist/ios_widgets/` folder.
3. **Install on iOS**:
   - Install [Scriptable](https://apps.apple.com/us/app/scriptable/id1405459188) on your iOS device.
   - Create two new scripts in the app, and paste the code from the newly generated `dist/ios_widgets/NotionLockScreen_Left.js` and `NotionLockScreen_Right.js`.
   - Add the Scriptable widget to your iOS Lock Screen or Home Screen.
   - Long-press the widget and select the Script you created.
