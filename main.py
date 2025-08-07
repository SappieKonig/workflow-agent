import asyncio
import os
import csv
import json
from datetime import datetime
from typing import Optional, Dict, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
    session_id: Optional[str] = None
    n8n_credentials: Optional[Dict] = None

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


def rephrase_to_active_form(text: str) -> str:
    """Use GPT-4o to rephrase todo items to active form."""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Convert the following task description to active/progressive form (present continuous tense). Keep it concise and clear. Examples:\n'Research available nodes' -> 'Researching available nodes'\n'Create workflow' -> 'Creating workflow'\n'Validate configuration' -> 'Validating configuration'"
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=50,
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception:
        # Fallback: simple conversion
        if text.startswith(('Create', 'Add', 'Remove', 'Update', 'Delete', 'Check', 'Validate', 'Test', 'Research', 'Design', 'Implement', 'Configure', 'Setup', 'Build')):
            return text.replace('Create', 'Creating').replace('Add', 'Adding').replace('Remove', 'Removing').replace('Update', 'Updating').replace('Delete', 'Deleting').replace('Check', 'Checking').replace('Validate', 'Validating').replace('Test', 'Testing').replace('Research', 'Researching').replace('Design', 'Designing').replace('Implement', 'Implementing').replace('Configure', 'Configuring').replace('Setup', 'Setting up').replace('Build', 'Building')
        return f"Working on: {text}"

class TodoTracker:
    """Track todo items and detect status changes."""
    def __init__(self):
        self.previous_todos: Dict[str, str] = {}  # id -> status
        
    def process_todo_event(self, event: dict) -> Optional[str]:
        """Process TodoWrite events and return message if item became in_progress."""
        message = event.get("message", {})
        content = message.get("content", [])
        
        for item in content:
            if item.get("type") == "tool_use" and item.get("name") == "TodoWrite":
                todos = item.get("input", {}).get("todos", [])
                
                for todo in todos:
                    todo_id = todo.get("id")
                    status = todo.get("status")
                    content_text = todo.get("content")
                    
                    # Check if this todo just became in_progress
                    if todo_id and status == "in_progress":
                        prev_status = self.previous_todos.get(todo_id)
                        if prev_status != "in_progress":
                            # New in_progress item detected
                            self.previous_todos[todo_id] = status
                            # Rephrase to active form
                            active_text = rephrase_to_active_form(content_text)
                            return active_text
                    
                    # Update status tracking
                    if todo_id:
                        self.previous_todos[todo_id] = status
        
        return None

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
    """Stream Claude's response using Server-Sent Events."""
    async def generate_sse():
        try:
            # Validate auth token
            if not request.auth_token or not request.auth_token.strip():
                yield f'data: {json.dumps({"type": "error", "data": "Authentication token is required"})}\n\n'
                return
            
            if not validate_auth_token(request.auth_token):
                yield f'data: {json.dumps({"type": "error", "data": "Invalid or expired authentication token"})}\n\n'
                return
            
            # Prepare prompt with context
            prompt = request.message
            if request.api_url:
                if "/workflow/" in request.api_url:
                    workflow_id = request.api_url.split("/workflow/")[-1].split("/")[0]
                    prompt = f"I'm on n8n workflow page with ID: {workflow_id}\n\n{prompt}"
                else:
                    prompt = f"I'm on n8n page: {request.api_url}\n\n{prompt}"
            
            # Store credentials temporarily
            request_uuid = str(uuid.uuid4())
            credential = N8NCredential(api_key=request.api_key, api_url=request.api_url)
            credential.write(cred_dir / f"{request_uuid}.json")
            
            # Add credentials context if available
            credentials_context = ""
            if request.n8n_credentials:
                credentials_data = request.n8n_credentials.get('rawResponse', {}).get('data', [])
                if credentials_data:
                    cred_list = []
                    for cred in credentials_data:
                        cred_info = f"- {cred.get('name', 'Unknown')} (ID: {cred.get('id', 'unknown')}, Type: {cred.get('type', 'unknown')})"
                        cred_list.append(cred_info)
                    credentials_context = f"\n\nAvailable n8n credentials you can reference by ID:\n" + "\n".join(cred_list)
            
            system_prompt = """You are an n8n workflow creation and management expert. You have access to tools to create, update, and manage n8n workflows via API."""
            prompt = f"{system_prompt}\n\nThe UUID of this request with which you can call tools on the user's n8n is {request_uuid}{credentials_context}\n\n{prompt}"
            
            # Build Claude command with streaming JSON output
            claude_cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose"]
            if request.session_id:
                claude_cmd.extend(["--resume", request.session_id])
            
            # Start subprocess
            process = await asyncio.create_subprocess_exec(
                *claude_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Initialize todo tracker
            todo_tracker = TodoTracker()
            
            # Stream stdout line by line
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                try:
                    # Parse JSON line
                    event = json.loads(line.decode().strip())
                    event_type = event.get("type")
                    
                    # Check for TodoWrite events
                    if event_type == "assistant":
                        # Process todo events
                        todo_message = todo_tracker.process_todo_event(event)
                        if todo_message:
                            # Send todo update as progress update
                            yield f"data: {json.dumps({'type': 'progress-update', 'data': todo_message})}\n\n"
                        
                        # Don't send message IDs anymore - only todo updates
                    
                    elif event_type == "result":
                        # Send final result with session_id in data
                        result_data = {
                            'text': event.get('result', ''),
                            'session_id': event.get('session_id')
                        }
                        yield f"data: {json.dumps({'type': 'result', 'data': json.dumps(result_data)})}\n\n"
                
                except json.JSONDecodeError:
                    # Skip non-JSON lines
                    continue
            
            # Wait for process to complete
            await process.wait()
            
            # Clean up credentials
            if os.path.exists(cred_dir / f"{request_uuid}.json"):
                os.remove(cred_dir / f"{request_uuid}.json")
            
            # Stream ends naturally, no explicit done event needed
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )

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