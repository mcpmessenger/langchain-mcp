# API Reference

Complete API documentation for the LangChain Agent MCP Server.

## Base URL

**Production:** https://langchain-agent-mcp-server-554655392699.us-central1.run.app

**Local:** http://localhost:8000

## Endpoints

### GET /

Server information and available endpoints.

**Response:**
```json
{
  "name": "LangChain Agent MCP Server",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "manifest": "/mcp/manifest",
    "invoke": "/mcp/invoke"
  }
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

### GET /mcp/manifest

Returns the MCP manifest declaring available tools.

**Response:**
```json
{
  "name": "langchain-agent-mcp-server",
  "version": "1.0.0",
  "description": "LangChain Agent MCP Server...",
  "tools": [
    {
      "name": "agent_executor",
      "description": "Execute a complex, multi-step reasoning task...",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "The user's query or task"
          }
        },
        "required": ["query"]
      }
    }
  ]
}
```

### POST /mcp/invoke

Executes the LangChain agent with a user query.

**Request:**
```json
{
  "tool": "agent_executor",
  "arguments": {
    "query": "What is the capital of France?"
  }
}
```

**Success Response (200):**
```json
{
  "content": [
    {
      "type": "text",
      "text": "The capital of France is Paris."
    }
  ],
  "isError": false
}
```

**Error Response (400/500):**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Error message here"
    }
  ],
  "isError": true
}
```

**Error Codes:**
- `400` - Bad Request (missing query, unknown tool)
- `401` - Unauthorized (invalid API key)
- `500` - Internal Server Error (agent execution failed)

### GET /docs

Interactive API documentation (Swagger UI).

Visit: https://langchain-agent-mcp-server-554655392699.us-central1.run.app/docs

## Authentication

### Optional API Key Authentication

If `API_KEY` environment variable is set, include in requests:

```http
Authorization: Bearer your-api-key
```

## Rate Limiting

Currently no rate limiting is implemented. Consider adding rate limiting for production use.

## Error Handling

All errors follow the MCP response format:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Error description"
    }
  ],
  "isError": true
}
```

## Examples

### cURL

```bash
# Health check
curl https://langchain-agent-mcp-server-554655392699.us-central1.run.app/health

# Get manifest
curl https://langchain-agent-mcp-server-554655392699.us-central1.run.app/mcp/manifest

# Invoke agent
curl -X POST https://langchain-agent-mcp-server-554655392699.us-central1.run.app/mcp/invoke \
  -H "Content-Type: application/json" \
  -d '{"tool":"agent_executor","arguments":{"query":"What is 2+2?"}}'
```

### Python

```python
import requests

url = "https://langchain-agent-mcp-server-554655392699.us-central1.run.app/mcp/invoke"
response = requests.post(
    url,
    json={
        "tool": "agent_executor",
        "arguments": {"query": "What is 2+2?"}
    }
)
print(response.json())
```

### JavaScript

```javascript
fetch('https://langchain-agent-mcp-server-554655392699.us-central1.run.app/mcp/invoke', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    tool: 'agent_executor',
    arguments: { query: 'What is 2+2?' }
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

---

For more examples, see [Examples](examples.md).

