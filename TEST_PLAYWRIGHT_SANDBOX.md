# Quick Test Guide - Playwright Sandbox

## Step-by-Step Testing Instructions

### Step 1: Install Playwright (Required)

Open a terminal/PowerShell and run:

```powershell
# Install Playwright Python package
pip install playwright

# Install Chromium browser (required for snapshots)
playwright install chromium
```

**Note:** If `playwright` command doesn't work, try:
```powershell
py -m playwright install chromium
```

### Step 2: Start the Backend Server

Open a **new terminal/PowerShell window** and run:

```powershell
# Navigate to project directory (if not already there)
cd "C:\Users\senti\OneDrive\Desktop\mcp SERVERS\Langchain MCP\restful-data-gateway-main"

# Start the backend server
py run_server.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!** The server needs to stay running.

### Step 3: Start the Frontend

Open **another new terminal/PowerShell window** and run:

```powershell
# Navigate to project directory
cd "C:\Users\senti\OneDrive\Desktop\mcp SERVERS\Langchain MCP\restful-data-gateway-main"

# Install frontend dependencies (if not already done)
npm install

# Start the frontend dev server
npm run dev
```

**Expected output:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:8080/
  ➜  Network: use --host to expose
```

**Keep this terminal open too!**

### Step 4: Test the Sandbox

1. **Open your browser** and go to:
   ```
   http://localhost:8080/sandbox
   ```

2. **Or** go to the home page first:
   ```
   http://localhost:8080
   ```
   Then click the **"Try Playwright Sandbox"** button

3. **Enter a URL** in the input field:
   - Try: `google.com`
   - Or: `github.com`
   - Or: `amazon.com`

4. **Click "Generate Snapshot"**

5. **Wait for the snapshot** (may take 10-30 seconds on first load)

6. **You should see:**
   - Left side: Live website in iframe
   - Right side: Structured accessibility snapshot (AI view)
   - Token count displayed

7. **Test the "Try a Prompt" feature:**
   - Enter a prompt like: `"Find the login button"` or `"Where is the search field?"`
   - Click "Test"
   - See highlighted matches in the snapshot

## Quick Test URLs

Try these popular sites (they're cached for faster results):
- `google.com`
- `github.com`
- `amazon.com`
- `stackoverflow.com`

## Troubleshooting

### Error: "Playwright is not available"

**Solution:**
```powershell
pip install playwright
playwright install chromium
```

### Error: "Failed to generate snapshot"

**Possible causes:**
1. Website took too long to load (30s timeout)
2. Website blocks automated access
3. Invalid URL

**Solution:** Try a different URL or check the backend terminal for error details

### Frontend can't connect to backend

**Check:**
1. Backend is running on port 8000 (check terminal)
2. Frontend is running on port 8080
3. No firewall blocking connections

**Test backend directly:**
```powershell
# Test health endpoint
curl http://localhost:8000/health

# Or in PowerShell
Invoke-WebRequest -Uri http://localhost:8000/health
```

### Port already in use

**If port 8000 is busy:**
```powershell
# Change port in .env file or set environment variable
$env:PORT="8001"
py run_server.py
```

Then update the frontend API URL (see below)

### Frontend API URL Configuration

If your backend is on a different port, create a `.env` file in the project root:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Or if backend is on port 8001:
```env
VITE_API_BASE_URL=http://localhost:8001
```

## Expected Behavior

✅ **First time loading a URL:**
- Takes 10-30 seconds
- Shows loading spinner
- Generates fresh snapshot

✅ **Loading cached sites (google.com, github.com, etc.):**
- Returns instantly
- Shows "✓ Using cached snapshot" message

✅ **Testing prompts:**
- Highlights matching lines in yellow
- Shows match count
- Displays context for each match

## What to Look For

1. **Dual-view works:** You see the website on the left, snapshot on the right
2. **Snapshot format:** Structured text showing `[role]` elements with names and descriptions
3. **Token count:** Shows estimated tokens (demonstrates efficiency vs screenshots)
4. **Prompt matching:** Highlights relevant elements when you test prompts
5. **Caching:** Popular sites load instantly on second visit

## Next Steps After Testing

Once you've verified it works:

1. **Try different URLs** to see various snapshot formats
2. **Test different prompts** to see element matching
3. **Check the token counts** to understand efficiency
4. **Review the snapshot structure** to see how AI "views" websites

## Production Deployment Notes

For production:
- Install Playwright browsers in your Docker container
- Set up proper caching (Redis recommended)
- Add rate limiting
- Configure CORS properly for your domain

