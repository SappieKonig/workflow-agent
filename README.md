# Workflow Agent

A workflow automation system that bridges n8n with Claude AI through a browser extension and FastAPI service. This tool enables users to create, edit, and manage n8n workflows using natural language through Claude AI.

## Overview

The Workflow Agent consists of three main components:
- **Browser Extension**: A Chrome extension providing a chat interface for interacting with Claude AI
- **FastAPI Service**: A Python backend that connects the browser extension to Claude CLI and n8n
- **n8n-mcp Integration**: MCP (Model Context Protocol) tools for direct n8n API interaction

## Prerequisites

- Python 3.10+
- uv (Python package manager)
- Chrome/Chromium browser
- Claude CLI installed and configured
- n8n instance with API access
- OpenAI API key (optional, for response compression)

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd workflow_agent
   ```

2. **Run the setup script**:
   ```bash
   ./setup.sh
   ```
   This will:
   - Install n8n-mcp and dependencies
   - Configure Claude Code integration
   - Set up the Python environment

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and URLs
   ```

4. **Generate browser extension config**:
   ```bash
   uv run generate_browser_config.py
   ```

5. **Install the browser extension**:
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `browser-extension` folder

6. **Start the service**:
   ```bash
   uv run main.py
   ```

## Architecture

```
Browser Extension ↔ FastAPI Service ↔ Claude CLI ↔ n8n-mcp ↔ n8n API
```

### Components

- **Browser Extension** (`browser-extension/`): Chrome extension with chat UI
- **FastAPI Service** (`main.py`): Python backend handling requests
- **n8n-mcp** (`n8n-mcp/`): MCP server providing n8n tools to Claude
- **MCP Proxy** (`mcp_proxy.py`): Alternative proxy implementation
- **Credentials Manager** (`n8n_credential.py`): Secure credential handling

## Usage

1. Click the extension icon in Chrome
2. Click "Show Chat Box" to open the interface
3. Type natural language commands to:
   - Create new workflows: "Create a workflow that sends Slack notifications"
   - Edit existing workflows: "Add error handling to the current workflow"
   - Query workflow status: "Show me recent executions"

## Configuration

### Environment Variables

Create a `.env` file with:
```bash
N8N_API_KEY=your_n8n_api_key
N8N_API_URL=https://your-n8n-instance.com
CLAUDE_SERVICE_TARGET=http://127.0.0.1:8000/chat
OPENAI_API_KEY=your_openai_api_key  # Optional
MCP_MODE=stdio
LOG_LEVEL=error
DISABLE_CONSOLE_OUTPUT=true
```

### Browser Extension Configuration

The browser extension configuration is auto-generated from environment variables:
```bash
uv run generate_browser_config.py
```

## Development

### Project Structure

```
workflow_agent/
├── browser-extension/      # Chrome extension files
├── n8n-mcp/               # n8n MCP server (submodule)
├── creds/                 # Temporary credential storage
├── main.py                # FastAPI service
├── mcp_proxy.py          # Alternative MCP proxy
├── n8n_credential.py     # Credential management
├── setup.sh              # Setup script
└── test.sh               # Test script
```

### Testing

Run tests with:
```bash
./test.sh
```

### MCP Tools

The n8n-mcp integration provides tools for:
- Node discovery and documentation
- Workflow creation and management
- Workflow validation
- Template search and usage
- n8n API operations

## Security

- API credentials are stored temporarily and deleted after use
- All communication is local (localhost) by default
- Browser extension only communicates with configured service URL
- Credentials are never exposed to the browser

## Troubleshooting

1. **Extension not loading**: Ensure Developer mode is enabled in Chrome
2. **Claude CLI errors**: Verify Claude CLI is installed and in PATH
3. **n8n connection issues**: Check API key and URL in `.env`
4. **MCP tools not available**: Run `./setup.sh` again to reconfigure

## License

See LICENSE file for details.