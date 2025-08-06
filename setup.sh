. .env

ABSOLUTE_PATH=$(pwd)

# Add ANTHROPIC_MODEL to shell config
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    SHELL_CONFIG="$HOME/.zshrc"
else
    # Linux
    SHELL_CONFIG="$HOME/.bashrc"
fi

# Check if ANTHROPIC_MODEL is already in the shell config
if ! grep -q "ANTHROPIC_MODEL=claude-sonnet-4-20250514" "$SHELL_CONFIG"; then
    echo "export ANTHROPIC_MODEL=claude-sonnet-4-20250514" >> "$SHELL_CONFIG"
    echo "Added ANTHROPIC_MODEL to $SHELL_CONFIG"
fi

# Setup n8n-mcp if directory doesn't exist
if [ ! -d "n8n-mcp" ]; then
    echo "Setting up n8n-mcp..."
    git clone git@github.com:SappieKonig/n8n-mcp.git
    cd n8n-mcp
    npm install
    npm run build
    npm run rebuild
    cd ..
    echo "n8n-mcp setup complete"
fi

# Add MCP server to Claude
claude mcp add n8n-mcp \
    -- uv run $ABSOLUTE_PATH/mcp_proxy.py