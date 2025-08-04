#!/bin/bash

# Make curl request to claude_service.py on port 8000
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a workflow that forwards mails I get to automaton.mailtesting@gmail.com. Be sure to sync the workflow to my n8n instance.",
    "api_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjNmQ5YjAxYS0wOGRiLTQ5NDEtYTFiNC1kNGEyMWEzZjNjZTEiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU0MTQ0MTkwLCJleHAiOjE3NTY2Nzc2MDB9.6ITeZW5xm7ou372gs1MvXKekZ8DV0HnTozSJH1ERLns",
    "api_url": "https://sheggle.app.n8n.cloud/"
  }'