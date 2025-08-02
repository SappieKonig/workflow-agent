# Right Side Chatbox Extension

A browser extension that provides a chat interface on the right side of web pages, integrated with Claude AI for workflow automation.

## Setup

### Prerequisites
- Python 3.10+
- uv (Python package manager)
- Chrome/Chromium browser
- Claude CLI installed and configured
- OpenAI API key (for response compression)

### 1. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and configure the following variables:
```bash
N8N_API_KEY=your_n8n_api_key
N8N_API_URL=https://your-n8n-instance.com
CLAUDE_SERVICE_TARGET=http://127.0.0.1:8000/chat
OPENAI_API_KEY=your_openai_api_key
MCP_MODE=stdio
LOG_LEVEL=error
DISABLE_CONSOLE_OUTPUT=true
```

### 2. Install n8n-mcp and Configure Claude Code

Run the setup script to install n8n-mcp and add it to Claude Code:
```bash
./setup.sh
```

This script will:
- Clone the n8n-mcp repository if it doesn't exist
- Clone the n8n-docs repository for documentation
- Install npm dependencies and build the project
- Add the n8n-mcp server to Claude Code with your environment variables

### 3. Generate Browser Extension Config

Generate the browser extension configuration from environment variables:
```bash
uv run generate_browser_config.py
```

This creates `browser-extension/config.js` with the correct service URL.

### 4. Install Browser Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Select the `browser-extension` folder
5. The extension should now appear in your extensions list

### 5. Start the Claude Service

Start the FastAPI service that bridges the browser extension to Claude:
```bash
uv run claude_service.py
```

The service will run on `http://127.0.0.1:8000` by default.

### 6. Usage

1. Navigate to any webpage
2. Click the extension icon in your browser toolbar
3. Click "Show Chat Box" to display the chat interface
4. Type your message and press Enter or click Send
5. The extension will send your request to Claude and display the response

## Configuration Updates

When you change `CLAUDE_SERVICE_TARGET` in `.env`, run the config generator again:
```bash
uv run generate_browser_config.py
```

Then reload the extension in Chrome to pick up the new configuration.

## Features

- Right-side chat interface on any webpage
- Integration with Claude AI via FastAPI service
- Context-aware: passes current page URL to Claude
- Workflow detection: recognizes n8n workflow pages for targeted assistance
- Response compression via OpenAI for better UX
- Persistent chat history using Chrome storage
- Auto-resizing input textarea

## Architecture

```
Browser Extension � FastAPI Service (claude_service.py) � Claude CLI � n8n API
```

The browser extension communicates with a local FastAPI service, which in turn uses the Claude CLI to process requests and interact with n8n workflows.