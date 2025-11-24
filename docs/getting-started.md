# Getting Started

This guide will help you set up and run the LangChain Agent MCP Server locally.

## Prerequisites

- Python 3.11 or higher
- OpenAI API key
- Git (optional, for cloning)

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/mcpmessenger/LangchainMCP.git
cd LangchainMCP
```

### Step 2: Install Dependencies

**Windows:**
```powershell
py -m pip install -r requirements.txt
```

**Linux/Mac:**
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
PORT=8000
HOST=0.0.0.0
```

### Step 4: Run the Server

**Windows:**
```powershell
py run_server.py
```

**Linux/Mac:**
```bash
python run_server.py
```

You should see:
```
Loaded environment variables from .env
Starting LangChain Agent MCP Server on 0.0.0.0:8000
API Documentation: http://0.0.0.0:8000/docs
```

## Verify Installation

### Test Health Endpoint

```powershell
# Windows PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/health"

# Linux/Mac
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy"}
```

### Test MCP Manifest

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/mcp/manifest"
```

### Test Agent Invocation

```powershell
$body = @{
    tool = "agent_executor"
    arguments = @{
        query = "What is 2+2?"
    }
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/mcp/invoke" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

## Next Steps

- [Deploy to Google Cloud Run](deployment.md)
- [Explore Examples](examples.md)
- [Read API Documentation](api-reference.md)

