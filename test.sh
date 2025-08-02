curl -i -X POST https://api.automaton.fit/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Please create a workflow that forwards emails I get to automaton.mailtesting@gmail.com",
    "url": "https://sheggle.app.n8n.cloud/home/workflows"
  }'