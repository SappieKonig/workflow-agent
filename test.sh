#!/bin/bash

# Make curl request to claude_service.py on port 8000
curl -X POST https://api.automaton.fit/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a workflow that forwards mails I get to automaton.mailtesting@gmail.com. Be sure to sync the workflow to my n8n instance, do not ask for confirmation.",
    "api_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjNmQ5YjAxYS0wOGRiLTQ5NDEtYTFiNC1kNGEyMWEzZjNjZTEiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU0MTQ0MTkwLCJleHAiOjE3NTY2Nzc2MDB9.6ITeZW5xm7ou372gs1MvXKekZ8DV0HnTozSJH1ERLns",
    "api_url": "https://sheggle.app.n8n.cloud/",
    "auth_token": "eba41fc8-7b73-4dda-9e3c-216608b3397a"
  }'