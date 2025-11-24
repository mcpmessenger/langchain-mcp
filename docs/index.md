# LangChain Agent MCP Server Documentation

Welcome to the LangChain Agent MCP Server documentation! This guide will help you understand, deploy, and use the MCP server to expose LangChain agent capabilities.

## What is This?

The LangChain Agent MCP Server is a production-ready backend service that wraps LangChain agents as Model Context Protocol (MCP) tools. It's deployed on Google Cloud Run and provides a scalable, serverless solution for AI agent capabilities.

## Quick Links

- [Getting Started](getting-started.md) - Set up and run the server locally
- [Deployment Guide](deployment.md) - Deploy to Google Cloud Run
- [Examples](examples.md) - Code examples and tutorials
- [API Reference](api-reference.md) - Complete API documentation
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

## Key Features

- ✅ **MCP Compliant** - Full Model Context Protocol support
- ✅ **LangChain Integration** - Multi-step reasoning with ReAct agents
- ✅ **Google Cloud Run** - Serverless, auto-scaling deployment
- ✅ **Production Ready** - Error handling, logging, monitoring
- ✅ **Extensible** - Easy to add custom tools

## Architecture

```
┌─────────────┐
│ MCP Client  │
│ (SlashMCP)  │
└──────┬──────┘
       │ HTTP/HTTPS
       ▼
┌─────────────────────────┐
│  FastAPI Server         │
│  (MCP Endpoints)        │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│  LangChain Agent        │
│  (ReAct Pattern)        │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│  Tools (Web, Weather)   │
└─────────────────────────┘
```

## Service Status

**Live Service:** https://langchain-agent-mcp-server-554655392699.us-central1.run.app

- ✅ Health: `/health`
- ✅ Manifest: `/mcp/manifest`
- ✅ Invoke: `/mcp/invoke`
- ✅ API Docs: `/docs`

---

**Ready to get started?** Check out the [Getting Started Guide](getting-started.md)!

