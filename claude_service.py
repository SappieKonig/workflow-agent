import subprocess
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatRequest(BaseModel):
    message: str
    url: str = None

def compress_response(claude_response: str) -> str:
    """Compress Claude's verbose response using OpenAI"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Compress the following response to this exact format:\n\nLine 1: 'Added workflow with ID: [ID]' or 'Edited workflow with ID: [ID]' or 'Updated workflow with ID: [ID]'\nLine 2: One brief sentence describing what the workflow does or what changed.\n\nExtract the workflow ID from the original response and determine if this was a creation or modification. Keep only the essential information."
                },
                {
                    "role": "user",
                    "content": claude_response
                }
            ],
            max_tokens=100,
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # Fallback: try to extract workflow ID manually if OpenAI fails
        import re
        id_match = re.search(r'ID[:\s]*([A-Za-z0-9_-]+)', claude_response)
        if id_match:
            workflow_id = id_match.group(1)
            # Determine if it's likely an edit or creation based on response content
            if any(word in claude_response.lower() for word in ['updated', 'modified', 'changed', 'edited']):
                return f"Edited workflow with ID: {workflow_id}\nWorkflow updated successfully."
            else:
                return f"Added workflow with ID: {workflow_id}\nWorkflow created successfully."
        return "Workflow processed successfully."

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Add URL context if provided
        prompt = request.message
        if request.url:
            if "/workflow/" in request.url:
                # Extract workflow ID from URL
                workflow_id = request.url.split("/workflow/")[-1]
                prompt = f"Context: User is currently viewing/editing workflow with ID: {workflow_id} on n8n at {request.url}\n\nPlease modify or update this existing workflow based on the user's request.\n\nUser request: {request.message}"
            else:
                prompt = f"Context: User is currently on this page: {request.url}\n\nPlease create a new workflow based on the user's request.\n\nUser request: {request.message}"
        
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            claude_response = result.stdout.strip()
            compressed_response = compress_response(claude_response)
            return {"response": compressed_response}
        else:
            return {"response": f"Error: {result.stderr.strip()}"}
            
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Request timeout")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Claude CLI not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)