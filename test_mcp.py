import asyncio
import json
import os
from mcp_calling import DirectMCPClient
from dotenv import load_dotenv
load_dotenv()


async def main():
    client = DirectMCPClient()
    await client.connect()
    
    # Pass API credentials as tool arguments instead of environment variables
    workflows = await client.call_tool("n8n_list_workflows", {
        "apiUrl": "https://sheggle.app.n8n.cloud/",
        "apiKey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjNmQ5YjAxYS0wOGRiLTQ5NDEtYTFiNC1kNGEyMWEzZjNjZTEiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU0MTQ0MTkwLCJleHAiOjE3NTY2Nzc2MDB9.6ITeZW5xm7ou372gs1MvXKekZ8DV0HnTozSJH1ERLns"
    })
    
    for workflow in json.loads(workflows[0].text)['data']['workflows']:
        print(workflow['id'])
    await client.disconnect()
    
if __name__ == "__main__":
    asyncio.run(main())