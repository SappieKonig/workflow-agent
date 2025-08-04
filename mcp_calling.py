#!/usr/bin/env python3
"""
Direct MCP Client Test - Test calling the original n8n MCP server directly
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import mcp.types as types
from dotenv import load_dotenv
load_dotenv()


class DirectMCPClient:
    """Direct client to test the original n8n-mcp server."""
    
    def __init__(self):
        self.process = None
        self.reader = None
        self.writer = None
        self.request_id = 0
    
    async def connect(self) -> "DirectMCPClient":
        """Connect to the original n8n-mcp server."""
        print("🔌 Connecting to original n8n-mcp server...", file=sys.stderr)
        
        # Original server configuration (same as proxy)
        index_path = Path(__file__).parent / "n8n-mcp" / "dist" / "mcp" / "index.js"
        # index_path = "/Users/ignacekonig/projects/n8n-mcp/dist/mcp/index.js"
        cmd = ["node", str(index_path)]
        env = os.environ.copy()
        env.update({
            "MCP_MODE": "stdio",
            "LOG_LEVEL": "error", 
            "DISABLE_CONSOLE_OUTPUT": "true",
            "N8N_API_URL": os.getenv("N8N_API_URL", ""),
            "N8N_API_KEY": os.getenv("N8N_API_KEY", "")
        })
        
        print(f"🚀 Starting command: {' '.join(cmd)}", file=sys.stderr)
        
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        self.reader = self.process.stdout
        self.writer = self.process.stdin
        
        # Initialize the connection
        await self._initialize()
        print("✅ Connected and initialized!", file=sys.stderr)
        return self
    
    async def disconnect(self) -> None:
        """Disconnect from the original n8n-mcp server."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        if self.process:
            self.process.terminate()
            await self.process.wait()
        print("🔌 Disconnected from original n8n-mcp server", file=sys.stderr)
    
    def _get_next_id(self) -> int:
        """Get next request ID."""
        self.request_id += 1
        return self.request_id
    
    async def _send_request(self, request: dict) -> None:
        """Send a request to the original server."""
        message = json.dumps(request) + "\n"
        self.writer.write(message.encode())
        await self.writer.drain()
        print(f"📤 SENT: {json.dumps(request, indent=2)}", file=sys.stderr)
    
    async def _read_response(self) -> dict:
        """Read a response from the original server."""
        line = await self.reader.readline()
        if not line:
            raise Exception("No response received from server")
        
        response = json.loads(line.decode().strip())
        print(f"📥 RECEIVED: {json.dumps(response, indent=2)}", file=sys.stderr)
        return response
    
    async def _initialize(self) -> None:
        """Send initialization sequence."""
        print("🔄 Sending initialize request...", file=sys.stderr)
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "direct-mcp-test",
                    "version": "1.0.0"
                }
            }
        }
        
        await self._send_request(init_request)
        init_response = await self._read_response()
        
        if "error" in init_response:
            raise Exception(f"Initialize failed: {init_response['error']}")
        
        # Send initialized notification
        print("🔄 Sending initialized notification...", file=sys.stderr)
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        await self._send_request(initialized_notification)
    
    async def list_tools(self) -> list[types.Tool]:
        """Test tools/list request."""
        print("📋 Testing tools/list...", file=sys.stderr)
        
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/list"
        }
        
        await self._send_request(request)
        response = await self._read_response()
        
        if "error" in response:
            print(f"❌ ERROR in tools/list: {response['error']}", file=sys.stderr)
            return []
        
        tools_data = response.get("result", {}).get("tools", [])
        print(f"✅ SUCCESS: Found {len(tools_data)} tools", file=sys.stderr)
        
        # Print first few tool names
        if tools_data:
            print("🔧 Available tools:", file=sys.stderr)
            for i, tool in enumerate(tools_data[:5]):
                print(f"   {i+1}. {tool['name']}", file=sys.stderr)
            if len(tools_data) > 5:
                print(f"   ... and {len(tools_data) - 5} more", file=sys.stderr)
        
        # Convert to MCP Tool objects
        tools = []
        for tool_data in tools_data:
            tools.append(types.Tool(
                name=tool_data["name"],
                description=tool_data.get("description", ""),
                inputSchema=tool_data.get("inputSchema", {})
            ))
        
        return tools
    
    async def call_tool(self, tool_name: str, arguments: dict | None = None) -> list[types.TextContent]:
        """Test tools/call request."""
        if arguments is None:
            arguments = {}
        
        print(f"🔧 Testing tools/call for '{tool_name}' with args: {arguments}", file=sys.stderr)
        
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        await self._send_request(request)
        response = await self._read_response()
        
        if "error" in response:
            print(f"❌ ERROR in tools/call: {response['error']}", file=sys.stderr)
            return []
        
        result = response.get("result", {})
        print(f"✅ SUCCESS: Tool call completed", file=sys.stderr)
        print(f"📊 Result structure: {list(result.keys())}", file=sys.stderr)
        
        # Convert to MCP TextContent objects
        content_data = result.get("content", [])
        content = []
        for item in content_data:
            if item.get("type") == "text":
                content.append(types.TextContent(
                    type="text",
                    text=item.get("text", "")
                ))
        
        return content


async def main():
    """Main test function."""
    print("🚀 Starting Direct MCP Client Test", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    
    # Clear output file at start
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write("Direct MCP Client Test Results\n" + "=" * 50 + "\n\n")
    
    client = DirectMCPClient()
    
    try:
        # Step 1: Connect
        await client.connect()
        print("\n" + "=" * 50, file=sys.stderr)
        
        # Step 2: List tools
        tools = await client.list_tools()
        print("\n" + "=" * 50, file=sys.stderr)
        
        if not tools:
            print("❌ No tools found, cannot proceed with tool calling test", file=sys.stderr)
            return
        
        # Step 3: Test multiple tools
        print("🧪 Testing tool calls...", file=sys.stderr)
        
        # Test 1: get_database_statistics (simple, no args)
        print("\n🔧 Test 1: get_database_statistics", file=sys.stderr)
        result1 = await client.call_tool("get_database_statistics")
        if result1:
            print("✅ SUCCESS", file=sys.stderr)
            if result1 and result1[0].text:
                with open("output.txt", "a", encoding="utf-8") as f:
                    f.write(f"Test 1 - get_database_statistics:\n{result1[0].text}\n\n")
        
        # Test 2: list_nodes with arguments
        print("\n🔧 Test 2: list_nodes with limit", file=sys.stderr)
        result2 = await client.call_tool("list_nodes", {"limit": 3})
        if result2:
            print("✅ SUCCESS", file=sys.stderr)
            if result2 and result2[0].text:
                with open("output.txt", "a", encoding="utf-8") as f:
                    f.write(f"Test 2 - list_nodes:\n{result2[0].text}\n\n")
        
        # Test 3: search_nodes 
        print("\n🔧 Test 3: search_nodes", file=sys.stderr)
        result3 = await client.call_tool("search_nodes", {"query": "webhook", "limit": 2})
        if result3:
            print("✅ SUCCESS", file=sys.stderr)
            if result3 and result3[0].text:
                with open("output.txt", "a", encoding="utf-8") as f:
                    f.write(f"Test 3 - search_nodes:\n{result3[0].text}\n\n")
        
        # Test 4: Create a Gmail forwarding workflow
        print("\n🔧 Test 4: Creating a Gmail forwarding workflow", file=sys.stderr)
        workflow_data = {
            "name": "Gmail Email Forwarding",
            "nodes": [
                {
                    "id": "gmail-trigger",
                    "name": "Gmail Trigger",
                    "type": "n8n-nodes-base.gmailTrigger",
                    "position": [240, 300],
                    "parameters": {
                        "event": "messageReceived",
                        "simple": True,
                        "filters": {
                            "readStatus": "unread"
                        },
                        "authentication": "oAuth2"
                    },
                    "typeVersion": 1
                },
                {
                    "id": "gmail-send",
                    "name": "Forward Email",
                    "type": "n8n-nodes-base.gmail",
                    "position": [460, 300],
                    "parameters": {
                        "sendTo": "automaton.mailtesting@gmail.com",
                        "message": "=<div style=\"border-left: 4px solid #ccc; padding-left: 10px; margin: 10px 0;\"><p><strong>---------- Forwarded message ----------</strong></p><p><strong>From:</strong> {{ $node['Gmail Trigger'].json.sender.name }} &lt;{{ $node['Gmail Trigger'].json.sender.emailAddress }}&gt;</p><p><strong>Date:</strong> {{ $node['Gmail Trigger'].json.date }}</p><p><strong>Subject:</strong> {{ $node['Gmail Trigger'].json.subject }}</p><p><strong>To:</strong> {{ $node['Gmail Trigger'].json.to }}</p></div><div>{{ $node['Gmail Trigger'].json.body }}</div>",
                        "options": {},
                        "subject": "=Fwd: {{ $node['Gmail Trigger'].json.subject }}",
                        "resource": "message",
                        "emailType": "html",
                        "operation": "send",
                        "authentication": "oAuth2"
                    },
                    "typeVersion": 2
                }
            ],
            "connections": {
                "Gmail Trigger": {
                    "main": [
                        [
                            {
                                "node": "Forward Email",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                }
            },
            "settings": {
                "executionOrder": "v1",
                "saveManualExecutions": True
            }
        }
        
        result4 = await client.call_tool("n8n_create_workflow", workflow_data)
        if result4:
            print("✅ SUCCESS", file=sys.stderr)
            if result4 and result4[0].text:
                with open("output.txt", "a", encoding="utf-8") as f:
                    f.write(f"Test 4 - n8n_create_workflow:\n{result4[0].text}\n\n")
        
        # Test 5: Validate the workflow we just created
        print("\n🔧 Test 5: Validating the created workflow", file=sys.stderr)
        result5 = await client.call_tool("validate_workflow", {
            "workflow": workflow_data,
            "options": {
                "validateNodes": True,
                "validateConnections": True,
                "validateExpressions": True,
                "profile": "ai-friendly"
            }
        })
        if result5:
            print("✅ SUCCESS", file=sys.stderr)
            if result5 and result5[0].text:
                with open("output.txt", "a", encoding="utf-8") as f:
                    f.write(f"Test 5 - validate_workflow:\n{result5[0].text}\n\n")
        
        print(f"\n🎉 All tool calls completed successfully!", file=sys.stderr)
        
    except Exception as e:
        print(f"💥 EXCEPTION: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    
    finally:
        await client.disconnect()
        print("\n🏁 Test completed", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())