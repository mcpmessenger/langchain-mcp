# Troubleshooting Guide

Common issues and solutions for the LangChain Agent MCP Server.

## Local Development Issues

### Python Not Found

**Issue:** `python` or `py` command not recognized

**Solution:**
- Windows: Use `py` instead of `python`
- Verify installation: `py --version`
- Add Python to PATH if needed

### pip Not Found

**Issue:** `pip` command not recognized

**Solution:**
```powershell
# Windows
py -m pip install -r requirements.txt

# Linux/Mac
python -m pip install -r requirements.txt
```

### Module Import Errors

**Issue:** `ImportError: cannot import name 'Tool'`

**Solution:**
- Check LangChain version: `pip show langchain`
- Update requirements: `pip install -r requirements.txt --upgrade`
- Verify imports work: `py -c "from langchain_core.tools import Tool; print('OK')"`

### API Key Not Detected

**Issue:** Server warns about missing API key

**Solution:**
1. Verify `.env` file exists in project root
2. Check API key format: `OPENAI_API_KEY=sk-proj-...`
3. Restart server after updating `.env`

## Deployment Issues

### Docker Build Fails

**Issue:** Build errors or missing dependencies

**Solution:**
- Check Docker is running: `docker ps`
- Verify Dockerfile syntax
- Check requirements.txt for version conflicts

### Cloud Run Deployment Fails

**Issue:** Container fails to start

**Solution:**
1. Check logs:
   ```powershell
   gcloud run services logs read langchain-agent-mcp-server --region us-central1
   ```
2. Verify PORT environment variable is handled correctly
3. Check startup script permissions: `chmod +x src/start.sh`

### 401 Unauthorized from OpenAI

**Issue:** Agent returns 401 errors

**Solution:**
1. Verify API key is set:
   ```powershell
   gcloud run services describe langchain-agent-mcp-server --region us-central1
   ```
2. Check key is valid at: https://platform.openai.com/account/api-keys
3. Verify billing/credits on OpenAI account

### Service Returns 404

**Issue:** Endpoints return 404 Not Found

**Solution:**
- Verify service URL is correct (no typos)
- Check service is running: `/health` endpoint
- Verify endpoint paths: `/mcp/manifest`, `/mcp/invoke`

## Performance Issues

### Slow Response Times

**Issue:** Agent takes too long to respond

**Solution:**
- Reduce `MAX_ITERATIONS` environment variable
- Use faster model: `OPENAI_MODEL=gpt-4o-mini`
- Increase Cloud Run resources: `--memory 4Gi --cpu 4`

### Agent Hits Iteration Limit

**Issue:** "Agent stopped due to iteration limit"

**Solution:**
- Increase `MAX_ITERATIONS` (default: 10)
- Simplify queries
- Check if agent is stuck in a loop

## Integration Issues

### SlashMCP 404 Errors

**Issue:** MCP gateway returns 404

**Solution:**
1. Verify service URL is correct (check for typos)
2. Test endpoints directly: `/health`, `/mcp/manifest`
3. Check CORS configuration
4. Verify service is publicly accessible

### MCP Client Connection Issues

**Issue:** Cannot connect to server

**Solution:**
- Verify service is running: Check `/health`
- Check network connectivity
- Verify URL format: `https://...` not `http://...`
- Check firewall/security settings

## Getting Help

### Check Logs

**Local:**
```powershell
# Server logs are printed to console
```

**Cloud Run:**
```powershell
gcloud run services logs read langchain-agent-mcp-server \
    --platform managed \
    --region us-central1 \
    --limit 50
```

### Verify Configuration

```powershell
# Check environment variables
gcloud run services describe langchain-agent-mcp-server \
    --region us-central1 \
    --format="value(spec.template.spec.containers[0].env)"
```

### Test Endpoints

```powershell
# Health
Invoke-WebRequest -Uri "https://langchain-agent-mcp-server-554655392699.us-central1.run.app/health"

# Manifest
Invoke-WebRequest -Uri "https://langchain-agent-mcp-server-554655392699.us-central1.run.app/mcp/manifest"
```

## Common Error Messages

### "OPENAI_API_KEY not set"
- Set in `.env` file for local development
- Set in Cloud Run environment variables for deployment

### "Cannot import name 'Tool'"
- Update LangChain: `pip install langchain-core --upgrade`
- Check version compatibility

### "Container failed to start"
- Check Cloud Run logs
- Verify Docker image builds successfully
- Check PORT environment variable handling

### "MCP gateway request failed with status 404"
- Verify service URL is correct
- Check service is running
- Test endpoints directly

---

**Still having issues?** Check the [GitHub Issues](https://github.com/mcpmessenger/LangchainMCP/issues) or create a new one.

