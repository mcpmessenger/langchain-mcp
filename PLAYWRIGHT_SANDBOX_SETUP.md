# Playwright Sandbox Setup Guide

This guide explains how to set up and use the Playwright Sandbox preview feature.

## Overview

The Playwright Sandbox allows users to "test drive" the playwright-mcp server directly on the Registry website before installing it. Users can:

1. Enter a URL and see the accessibility tree output
2. Compare the live website view with the AI's structured view
3. Test prompts to see how the AI finds elements in the snapshot

## Prerequisites

### 1. Install Playwright

The backend requires Playwright to be installed. Run:

```bash
# Install Playwright Python package
pip install playwright>=1.40.0

# Install Playwright browsers
playwright install chromium
```

**Note:** On Windows, you may need to use `py -m playwright install chromium` instead.

### 2. Verify Installation

Check that Playwright is available:

```python
python -c "from playwright.async_api import async_playwright; print('Playwright installed successfully')"
```

## Running the Sandbox

### Development Setup

1. **Start the Backend Server:**
   ```bash
   # Make sure you're in the project root
   py run_server.py
   # Or
   python run_server.py
   ```
   
   The server should start on `http://localhost:8000`

2. **Start the Frontend:**
   ```bash
   npm run dev
   # Or
   yarn dev
   ```
   
   The frontend should start on `http://localhost:8080`

3. **Access the Sandbox:**
   - Navigate to `http://localhost:8080/sandbox`
   - Or click "Try Playwright Sandbox" from the home page

### Production Setup

For production deployments, ensure:

1. Playwright browsers are installed in the container/environment
2. The `VITE_API_BASE_URL` environment variable is set to your backend URL
3. CORS is properly configured (already set to allow all origins by default)

## API Endpoints

### POST /api/playwright/snapshot

Generates a structured accessibility snapshot of a webpage.

**Request:**
```json
{
  "url": "google.com",
  "use_cache": true
}
```

**Response:**
```json
{
  "snapshot": "[button]\n  Name: Search\n  Description: Search button...",
  "url": "https://google.com",
  "cached": false,
  "token_count": 1234
}
```

### POST /api/playwright/test-prompt

Tests a prompt against a snapshot to find matching elements.

**Request:**
```json
{
  "snapshot": "...",
  "prompt": "Find the login button"
}
```

**Response:**
```json
{
  "matches": [
    {
      "line": 42,
      "content": "[button] Name: Login",
      "context": "..."
    }
  ],
  "prompt": "Find the login button",
  "total_matches": 1
}
```

## Caching

The sandbox automatically caches snapshots for popular sites:
- amazon.com
- github.com
- google.com
- stackoverflow.com

Cached results are returned instantly, saving compute costs for demo purposes.

## Troubleshooting

### "Playwright is not available" Error

**Solution:** Install Playwright and its browsers:
```bash
pip install playwright
playwright install chromium
```

### "Failed to generate snapshot" Error

**Common causes:**
1. **Network timeout:** The website took too long to load (30s timeout)
2. **Invalid URL:** Make sure the URL is accessible
3. **CORS issues:** Some websites block automated access

**Solution:** Try a different URL or check server logs for details.

### Frontend Can't Connect to Backend

**Solution:** 
1. Verify backend is running on port 8000
2. Set `VITE_API_BASE_URL=http://localhost:8000` in your `.env` file
3. Check CORS settings in `src/main.py`

### Browser Installation Issues

If Playwright browsers fail to install:

**Windows:**
```powershell
py -m playwright install chromium
```

**Linux/Mac:**
```bash
playwright install chromium
```

**Docker:**
Add to your Dockerfile:
```dockerfile
RUN playwright install chromium
RUN playwright install-deps chromium
```

## Features

### Dual-View Panel

- **Left Side:** Live website rendered in an iframe
- **Right Side:** Structured accessibility snapshot (AI view)

### Try a Prompt

Users can enter prompts like:
- "Find the login button"
- "Where is the search field?"
- "Show me all links"

The system highlights matching elements in the snapshot.

### Token Savings Display

The snapshot shows estimated token count, demonstrating how much more efficient structured data is compared to screenshots or full HTML.

## Architecture

- **Backend:** FastAPI endpoint using Playwright's accessibility API
- **Frontend:** React component with dual-view panel
- **Caching:** In-memory cache for popular sites (50 entry limit)
- **Error Handling:** Graceful fallbacks if Playwright is unavailable

## Security Notes

- The sandbox uses iframes with restricted sandbox attributes
- Only accessibility tree data is returned (no raw HTML/screenshots)
- URLs are validated before processing
- Timeout limits prevent resource exhaustion

## Next Steps

For production deployment:
1. Consider using Redis for distributed caching
2. Add rate limiting to prevent abuse
3. Implement proper authentication if needed
4. Use a dedicated Playwright service for better isolation

