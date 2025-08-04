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
        "apiUuid": "9d3b6fdd-4b8f-4076-8b71-de549a54111c"
    })
    
    for workflow in json.loads(workflows[0].text)['data']['workflows']:
        print(workflow['id'])
    await client.disconnect()
    
if __name__ == "__main__":
    asyncio.run(main())