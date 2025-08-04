from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from mcp_calling import DirectMCPClient


@asynccontextmanager
async def server_lifespan(_server: Server) -> AsyncIterator[DirectMCPClient]:
    client = await DirectMCPClient().connect()
    try:
        yield {'client': client}
    finally:
        await client.disconnect()
        

server = Server('n8n-mcp-proxy', server_lifespan)


@server.list_tools()
async def list_tools(client: DirectMCPClient) -> list[types.Tool]:
    return await client.list_tools()


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    ctx = server.request_context
    client = ctx.lifespan_context['client']

    results = await client.call_tool(name, arguments)
    return results
    

async def run():
    """Run the server with lifespan management."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="n8n-mcp-proxy",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
