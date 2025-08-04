. .env

ABSOLUTE_PATH=$(pwd)

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