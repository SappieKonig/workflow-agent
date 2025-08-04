import asyncio
import json
import os
from mcp_calling import DirectMCPClient
from dotenv import load_dotenv
load_dotenv()


async def main():
    client = DirectMCPClient()
    await client.connect()
    
    uuid = client.add_credentials(os.getenv("N8N_API_KEY"), os.getenv("N8N_API_URL"))

    # tools = await client.list_tools()
    # print(tools)
    
    # Pass API credentials as tool arguments instead of environment variables
    workflows = await client.call_tool("n8n_list_workflows", {
        "apiUuid": uuid
    })
    
    for workflow in json.loads(workflows[0].text)['data']['workflows']:
        print(workflow['id'])
    await client.disconnect()
    
if __name__ == "__main__":
    asyncio.run(main())