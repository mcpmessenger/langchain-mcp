# LangChain Agent MCP Server

> **A production-ready MCP server exposing LangChain agent capabilities through the Model Context Protocol, deployed on Google Cloud Run.**

[![GitHub Stars](https://img.shields.io/github/stars/mcpmessenger/LangchainMCP?style=social)](https://github.com/mcpmessenger/LangchainMCP)
[![GitHub Forks](https://img.shields.io/github/forks/mcpmessenger/LangchainMCP?style=social)](https://github.com/mcpmessenger/LangchainMCP)
[![License](https://img.shields.io/github/license/mcpmessenger/LangchainMCP)](https://github.com/mcpmessenger/LangchainMCP/blob/main/LICENSE)

## 🚀 Overview

This is a **standalone backend service** that wraps a LangChain agent as a single, high-level MCP Tool. The server is built with **FastAPI** and deployed on **Google Cloud Run**, providing a scalable, production-ready solution for exposing AI agent capabilities to any MCP-compliant client.

**Live Service:** https://langchain-agent-mcp-server-554655392699.us-central1.run.app

## ✨ Features

- ✅ **MCP Compliance** - Full Model Context Protocol support
- ✅ **LangChain Agent** - Multi-step reasoning with ReAct pattern
- ✅ **Playwright Sandbox** - Interactive preview of accessibility snapshots (NEW!)
- ✅ **Google Cloud Run** - Scalable, serverless deployment
- ✅ **Tool Support** - Extensible framework for custom tools
- ✅ **Production Ready** - Error handling, logging, and monitoring
- ✅ **Docker Support** - Containerized for easy deployment

## 🏗️ Architecture

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI | High-performance, asynchronous web server |
| **Agent Framework** | LangChain | Multi-step reasoning and tool execution |
| **Deployment** | Google Cloud Run | Serverless, auto-scaling hosting |
| **Containerization** | Docker | Consistent deployment environment |
| **Protocol** | Model Context Protocol (MCP) | Standardized tool and context sharing |

## 🛠️ Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Google Cloud account (for Cloud Run deployment)
- Docker (optional, for local testing)

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mcpmessenger/LangchainMCP.git
   cd LangchainMCP
   ```

2. **Install dependencies:**
   ```powershell
   # Windows
   py -m pip install -r requirements.txt
   
   # Linux/Mac
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file:
   ```env
   OPENAI_API_KEY=your-openai-api-key-here
   OPENAI_MODEL=gpt-4o-mini
   PORT=8000
   ```

4. **Run the server:**
   ```powershell
   # Windows
   py run_server.py
   
   # Linux/Mac
   python run_server.py
   ```

5. **Test the endpoints:**
   - Health: http://localhost:8000/health
   - Manifest: http://localhost:8000/mcp/manifest
   - API Docs: http://localhost:8000/docs
   - Playwright Sandbox: http://localhost:8080/sandbox (after starting frontend)

6. **Start the frontend (optional):**
   ```powershell
   # Install frontend dependencies (first time only)
   npm install
   
   # Start frontend dev server
   npm run dev
   ```
   Then visit http://localhost:8080/sandbox to use the Playwright Sandbox preview feature.

## ☁️ Google Cloud Run Deployment

The server is designed for deployment on **Google Cloud Run**. See our comprehensive deployment guides:

- **[DEPLOY_CLOUD_RUN_WINDOWS.md](DEPLOY_CLOUD_RUN_WINDOWS.md)** - Windows deployment guide
- **[DEPLOY_CLOUD_RUN.md](DEPLOY_CLOUD_RUN.md)** - General deployment guide
- **[QUICK_DEPLOY.md](QUICK_DEPLOY.md)** - Quick reference

### Quick Deploy

```powershell
# Windows PowerShell
.\deploy-cloud-run.ps1 -ProjectId "your-project-id" -Region "us-central1"

# Linux/Mac
./deploy-cloud-run.sh your-project-id us-central1
```

### Current Deployment

- **Service URL:** https://langchain-agent-mcp-server-554655392699.us-central1.run.app
- **Project:** slashmcp
- **Region:** us-central1
- **Status:** ✅ Live and operational

## 📡 API Endpoints

### MCP Endpoints

#### Get Manifest
```http
GET /mcp/manifest
```

Returns the MCP manifest declaring available tools.

**Response:**
```json
{
  "name": "langchain-agent-mcp-server",
  "version": "1.0.0",
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
          },
          "system_instruction": {
            "type": "string",
            "description": "Optional system-level instructions to customize agent behavior"
          }
        },
        "required": ["query"]
      }
    }
  ]
}
```

#### Invoke Tool
```http
POST /mcp/invoke
Content-Type: application/json

{
  "tool": "agent_executor",
  "arguments": {
    "query": "What is the capital of France?",
    "task_id": "optional-workflow-id"
  }
}
```

**With System Instruction (Optional):**
```http
POST /mcp/invoke
Content-Type: application/json

{
  "tool": "agent_executor",
  "arguments": {
    "query": "Analyze Tesla stock",
    "system_instruction": "You are a financial analyst. Provide detailed analysis with specific numbers."
  }
}
```

**Response:**
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

### System Instructions

The `agent_executor` tool supports an optional `system_instruction` parameter that allows you to customize the agent's behavior on a per-invocation basis.

**Usage:**
- **Basic Query** (uses default prompt):
  ```json
  {
    "tool": "agent_executor",
    "arguments": {
      "query": "What is the weather today?"
    }
  }
  ```

- **Query with Custom Instruction**:
  ```json
  {
    "tool": "agent_executor",
    "arguments": {
      "query": "Explain quantum computing",
      "system_instruction": "You are a physics professor. Explain concepts clearly and use examples."
    }
  }
  ```

- **Personality Customization**:
  ```json
  {
    "tool": "agent_executor",
    "arguments": {
      "query": "Tell me about space",
      "system_instruction": "You are a pirate explaining complex topics. Use pirate terminology!"
    }
  }
  ```

**Notes:**
- If `system_instruction` is omitted, the agent uses its default prompt
- Empty or whitespace-only instructions are ignored (default prompt is used)
- Each invocation with a custom instruction creates a new agent instance

### Playwright Sandbox Endpoints

#### Generate Accessibility Snapshot
```http
POST /api/playwright/snapshot
Content-Type: application/json

{
  "url": "wikipedia.org",
  "use_cache": true
}
```

**Response:**
```json
{
  "snapshot": "[body]\n  Name: Wikipedia\n  [main]\n    Name: Main content...",
  "url": "https://wikipedia.org",
  "cached": false,
  "token_count": 3307
}
```

**Features:**
- Generates structured accessibility snapshots of any website
- Shows how AI "views" websites through structured data
- Caching support for popular sites
- Token count estimation
- Windows-compatible (uses ProactorEventLoop)

#### Test Prompt Against Snapshot
```http
POST /api/playwright/test-prompt
Content-Type: application/json

{
  "snapshot": "[body]\n  [button]\n    Name: Login",
  "prompt": "Find the login button"
}
```

**Response:**
```json
{
  "matches": [
    {
      "line": 2,
      "content": "[button] Name: Login",
      "context": "..."
    }
  ],
  "prompt": "Find the login button",
  "total_matches": 1
}
```

**Playwright Sandbox UI:**
Visit `http://localhost:8080/sandbox` to use the interactive preview feature:
- Enter any URL to generate a snapshot
- View live website side-by-side with AI accessibility snapshot
- Test prompts to find elements in the snapshot
- See token savings compared to full HTML/screenshots

### Other Endpoints

- `GET /` - Server information
- `GET /health` - Health check
- `GET /api/tasks` - Safe task summaries (optional monitoring)
- `GET /api/tasks/{task_id}` - Safe task summary (optional monitoring)
- `GET /docs` - Interactive API documentation (Swagger UI)

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | ✅ Yes |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o-mini` | No |
| `PORT` | Server port | `8000` | No |
| `API_KEY` | Optional API key for authentication | - | No |
| `MAX_ITERATIONS` | Maximum agent iterations | `10` | No |
| `DEFAULT_SYSTEM_INSTRUCTION` | Default system prompt (Glazyr) | - | No |
| `VERBOSE` | Enable verbose logging | `false` | No |
| `POLICY_ENFORCEMENT` | Enforce /mcp/invoke policy gates | `false` | No |
| `MAX_QUERY_CHARS` | Max allowed query size | `5000000` | No |
| `ALLOWLISTED_DOMAINS` | Comma-separated domain allowlist (query URLs) | - | No |
| `REDIS_URL` | Enable Redis state store + task monitoring | - | No |
| `TASK_TTL_SECONDS` | Task summary TTL | `86400` | No |
| `RECENT_TASKS_MAX` | Recent task index size | `200` | No |

## 📚 Documentation

📖 **[Full Documentation Site](https://mcpmessenger.github.io/LangchainMCP/)** - Complete documentation with examples (GitHub Pages)

**Quick Links:**
- **[Getting Started](docs/getting-started.md)** - Set up and run locally
- **[Examples](docs/examples.md)** - Code examples including **"Build a RAG agent in 10 lines"**
- **[Deployment Guide](docs/deployment.md)** - Deploy to Google Cloud Run
- **[API Reference](docs/api-reference.md)** - Complete API documentation
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

**Build Docs Locally:**
```powershell
# Windows
.\build-docs.ps1 serve

# Linux/Mac
./build-docs.sh serve
```

**Additional Guides:**
- **[README_BACKEND.md](README_BACKEND.md)** - Complete technical documentation
- **[PLAYWRIGHT_SANDBOX_SETUP.md](PLAYWRIGHT_SANDBOX_SETUP.md)** - Playwright Sandbox setup and usage
- **[BUG_REPORT_PLAYWRIGHT_NOTIMPLEMENTEDERROR.md](BUG_REPORT_PLAYWRIGHT_NOTIMPLEMENTEDERROR.md)** - Windows compatibility fix documentation
- **[DEPLOY_CLOUD_RUN_WINDOWS.md](DEPLOY_CLOUD_RUN_WINDOWS.md)** - Windows deployment guide
- **[INSTALL_PREREQUISITES.md](INSTALL_PREREQUISITES.md)** - Prerequisites installation
- **[SLASHMCP_INTEGRATION.md](SLASHMCP_INTEGRATION.md)** - SlashMCP integration guide
- **[docs/glazyr-integration.md](docs/glazyr-integration.md)** - Glazyr integration notes (screenshots → MCP invoke)

## 🧪 Testing

```powershell
# Test health endpoint
Invoke-WebRequest -Uri "https://langchain-agent-mcp-server-554655392699.us-central1.run.app/health"

# Test agent invocation
$body = @{
    tool = "agent_executor"
    arguments = @{
        query = "What is 2+2?"
    }
} | ConvertTo-Json

Invoke-WebRequest -Uri "https://langchain-agent-mcp-server-554655392699.us-central1.run.app/mcp/invoke" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

# Test with system instruction
$bodyWithInstruction = @{
    tool = "agent_executor"
    arguments = @{
        query = "What is 2+2?"
        system_instruction = "You are a math teacher. Explain your reasoning step by step."
    }
} | ConvertTo-Json

Invoke-WebRequest -Uri "https://langchain-agent-mcp-server-554655392699.us-central1.run.app/mcp/invoke" `
    -Method POST `
    -ContentType "application/json" `
    -Body $bodyWithInstruction
```

## 🎭 Playwright Sandbox Feature

The Playwright Sandbox is an interactive preview feature that demonstrates how AI agents "view" websites through structured accessibility data. This feature is particularly useful for understanding the value of structured snapshots compared to full HTML or screenshots.

### Features

- **Dual-View Interface**: See the live website alongside its structured accessibility snapshot
- **Token Efficiency**: Compare token counts - snapshots are typically 90%+ smaller than full HTML
- **Interactive Testing**: Test prompts to find elements in the snapshot
- **Caching**: Popular sites are cached for faster demo results
- **Windows Compatible**: Fixed `NotImplementedError` on Windows using ProactorEventLoop

### Quick Start

1. **Install Playwright:**
   ```powershell
   py -m pip install playwright
   py -m playwright install chromium
   ```

2. **Start Backend:**
   ```powershell
   py run_server.py
   ```

3. **Start Frontend:**
   ```powershell
   npm install  # First time only
   npm run dev
   ```

4. **Visit Sandbox:**
   Open http://localhost:8080/sandbox and try URLs like:
   - `wikipedia.org`
   - `github.com`
   - `google.com`

### How It Works

1. **Enter a URL** - The system navigates to the website using Playwright
2. **Generate Snapshot** - Extracts structured accessibility information (roles, names, descriptions)
3. **View Comparison** - See the live site vs. the AI's structured view
4. **Test Prompts** - Try asking the AI to find specific elements

### Technical Details

- **Backend**: FastAPI endpoint with Playwright integration
- **Frontend**: React + Vite with TanStack Query
- **Event Loop**: Uses ProactorEventLoop on Windows for subprocess support
- **Stealth Mode**: Anti-bot detection measures for better compatibility
- **Error Handling**: Graceful handling of sites that block automated access

See [PLAYWRIGHT_SANDBOX_SETUP.md](PLAYWRIGHT_SANDBOX_SETUP.md) for detailed setup instructions.

## 🏗️ Project Structure

```
.
├── src/
│   ├── main.py              # FastAPI application with MCP endpoints
│   ├── agent.py             # LangChain agent definition and tools
│   ├── pages/
│   │   └── Sandbox.tsx      # Playwright Sandbox UI component
│   ├── mcp_manifest.json    # MCP manifest configuration
│   └── start.sh             # Cloud Run startup script
├── tests/
│   └── test_mcp_endpoints.py # Test suite
├── Dockerfile               # Container configuration
├── requirements.txt         # Python dependencies (includes playwright)
├── deploy-cloud-run.ps1     # Windows deployment script
├── deploy-cloud-run.sh      # Linux/Mac deployment script
└── cloudbuild.yaml          # Cloud Build configuration
```

## 🚀 Deployment Options

### Google Cloud Run (Recommended)

- **Scalable** - Auto-scales based on traffic
- **Serverless** - Pay only for what you use
- **Managed** - No infrastructure to manage
- **Fast** - Low latency with global CDN

See [DEPLOY_CLOUD_RUN_WINDOWS.md](DEPLOY_CLOUD_RUN_WINDOWS.md) for detailed instructions.

### Docker (Local/Other Platforms)

```bash
docker build -t langchain-agent-mcp-server .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key langchain-agent-mcp-server
```

## 📊 Performance

- **P95 Latency:** < 5 seconds for standard 3-step ReAct chains
- **Scalability:** Horizontal scaling on Cloud Run
- **Uptime:** 99.9% target (Cloud Run SLA)
- **Throughput:** Handles concurrent requests efficiently

## 🔒 Security

- API key authentication (optional)
- Environment variable management
- Secret Manager integration (Cloud Run)
- HTTPS by default (Cloud Run)
- CORS configuration

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📜 License

This project is licensed under the MIT License.

## 🔗 Links

- **GitHub Repository:** https://github.com/mcpmessenger/LangchainMCP
- **Live Service:** https://langchain-agent-mcp-server-554655392699.us-central1.run.app
- **API Documentation:** https://langchain-agent-mcp-server-554655392699.us-central1.run.app/docs
- **Model Context Protocol:** https://modelcontextprotocol.io/

## 🙏 Acknowledgments

- Built with [LangChain](https://www.langchain.com/)
- Deployed on [Google Cloud Run](https://cloud.google.com/run)
- Uses [FastAPI](https://fastapi.tiangolo.com/) for the web framework

---

**Status:** ✅ Production-ready and deployed on Google Cloud Run
