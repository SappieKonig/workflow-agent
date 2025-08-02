. .env

ABSOLUTE_PATH=$(pwd)

# Setup n8n-mcp if directory doesn't exist
if [ ! -d "n8n-mcp" ]; then
    echo "Setting up n8n-mcp..."
    git clone https://github.com/czlonkowski/n8n-mcp.git
    git clone https://github.com/n8n-io/n8n-docs.git
    cd n8n-mcp
    npm install
    npm run build
    npm run rebuild
    cd ..
    echo "n8n-mcp setup complete"
fi

# Add MCP server to Claude
claude mcp add n8n-mcp \
    -e N8N_API_KEY=$N8N_API_KEY \
    -e N8N_API_URL=$N8N_API_URL \
    -e MCP_MODE=$MCP_MODE \
    -e LOG_LEVEL=$LOG_LEVEL \
    -e DISABLE_CONSOLE_OUTPUT=$DISABLE_CONSOLE_OUTPUT \
    -- node $ABSOLUTE_PATH/n8n-mcp/dist/mcp/index.js