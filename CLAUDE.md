# Claude Context for Workflow Agent

## Branding Guidelines

Brand colors for the extension:
- Primary Red: #FF4040 
- Dark Red: #B32D2D
- Dark Gray: #292929
- Light Gray: #FAFAFA

## Project Structure

```
workflow_agent/
├── main.py                 # FastAPI service that bridges browser to Claude CLI
├── mcp_proxy.py           # Alternative MCP proxy implementation
├── n8n_credential.py      # Credential management for n8n API
├── generate_browser_config.py  # Generates browser extension config
├── setup.sh               # Setup script for n8n-mcp and dependencies
├── test.sh                # Test script
├── browser-extension/     # Chrome extension files
│   ├── manifest.json     
│   ├── popup.js          
│   ├── content.js        
│   └── config.js         # Auto-generated from env vars
├── n8n-mcp/              # n8n MCP server providing Claude tools
├── creds/                # Temporary credential storage
└── .env                  # Environment configuration
```

## Package Management

This project uses **uv** as the Python package manager. All Python commands should be run with:

```bash
uv run <command>
```

Examples:
- `uv run main.py` - Start the FastAPI service
- `uv run generate_browser_config.py` - Generate browser config
- `uv run test_mcp.py` - Run MCP tests