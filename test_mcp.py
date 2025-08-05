import asyncio
import json
import os
from mcp_calling import DirectMCPClient
from dotenv import load_dotenv
load_dotenv()


async def main():
    client = DirectMCPClient()
    await client.connect()
    
    tools = await client.list_tools()
    print(tools)
    
    # Pass API credentials as tool arguments instead of environment variables
    workflows = await client.call_tool("n8n_list_workflows", {
        "apiUuid": "b9cad45b-05b0-43cb-ba2b-a747ca0b8d71"
    })
    
    for workflow in json.loads(workflows[0].text)['data']['workflows']:
        print(workflow['id'])
    await client.disconnect()
    
if __name__ == "__main__":
    asyncio.run(main())