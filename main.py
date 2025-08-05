import asyncio
import os
import csv
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import uuid
from pathlib import Path
from n8n_credential import N8NCredential

from dotenv import load_dotenv

load_dotenv()

base_dir = Path(__file__).parent
cred_dir = base_dir / "creds"
cred_dir.mkdir(parents=True, exist_ok=True)
system_prompt = (base_dir / "system_prompt.txt").read_text()

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
    auth_token: str
    api_key: str
    api_url: str

class FeedbackRequest(BaseModel):
    feedback: str

def validate_auth_token(token: str) -> bool:
    """Validate auth token against the database."""
    try:
        from auth_cli import check_token
        return check_token(token)
    except Exception:
        # If there's any error importing or running check_token, deny access
        return False


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
    except Exception:
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
        # Validate auth token input first
        if not request.auth_token or not request.auth_token.strip():
            raise HTTPException(status_code=401, detail="Authentication token is required")
        
        # Validate auth token against database
        if not validate_auth_token(request.auth_token):
            raise HTTPException(status_code=401, detail="Invalid or expired authentication token")
        
        # Add URL context if provided
        prompt = request.message
        if request.api_url:
            if "/workflow/" in request.api_url:
                # Extract workflow ID from URL
                workflow_id = request.api_url.split("/workflow/")[-1]
                prompt = f"Context: User is currently viewing/editing workflow with ID: {workflow_id} on n8n at {request.api_url}\n\nPlease modify or update this existing workflow based on the user's request.\n\nUser request: {request.message}"
            else:
                prompt = f"Context: User is currently on this page: {request.api_url}\n\nPlease create a new workflow based on the user's request.\n\nUser request: {request.message}"

        request_uuid = uuid.uuid4()
        N8NCredential(api_key=request.api_key, api_url=request.api_url).write(cred_dir / f"{request_uuid}.json")

        system_prompt = "Exclusively use the n8n-mcp tools."

        prompt = f"{system_prompt}\n\nThe UUID of this request with which you can call tools on the user's n8n is {request_uuid}\n\n{prompt}"

        print(f"Running claude command with UUID: {request_uuid}")
        
        # Use async subprocess to avoid blocking the server
        process = await asyncio.create_subprocess_exec(
            "claude", "-p", prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=300
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise HTTPException(status_code=408, detail="Request timeout")
        
        if process.returncode == 0:
            claude_response = stdout.decode().strip()
            print(f"Claude response: {claude_response}")
            return {"response": claude_response}
        else:
            return {"response": f"Error: {stderr.decode().strip()}"}
            
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Claude CLI not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(cred_dir / f"{request_uuid}.json"):
            os.remove(cred_dir / f"{request_uuid}.json")

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit user feedback to CSV file."""
    feedback_file = base_dir / "feedback.csv"
    
    # Create CSV with headers if it doesn't exist
    file_exists = feedback_file.exists()
    
    with open(feedback_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write headers if new file
        if not file_exists:
            writer.writerow(['timestamp', 'feedback'])
        
        # Write feedback with timestamp
        writer.writerow([
            datetime.now().isoformat(),
            request.feedback
        ])
    
    return {"status": "success", "message": "Thank you for your feedback!"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)