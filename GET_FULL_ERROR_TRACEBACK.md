# How to Get the Full Error Traceback

## The Problem

We're getting `NotImplementedError()` but we need to see the **full traceback** to know exactly where it's failing.

## Steps to Get the Traceback

### Method 1: Check Backend Terminal

1. **Look at your backend terminal** (where `py run_server.py` is running)
2. **Make a request** that triggers the error:
   - Go to Swagger UI: `http://localhost:8000/docs`
   - Click `POST /api/playwright/snapshot`
   - Click "Try it out"
   - Enter: `{"url": "wikipedia.org", "use_cache": false}`
   - Click "Execute"
3. **Immediately check the backend terminal**
4. **Scroll up** to find the error logs
5. **Look for lines like:**
   ```
   ERROR: Error generating Playwright snapshot (NotImplementedError): ...
   Full traceback:
   Traceback (most recent call last):
     File "...", line X, in ...
       ...
   NotImplementedError: ...
   ```
6. **Copy the ENTIRE traceback** (from "Traceback" to the end)

### Method 2: Enable More Verbose Logging

Add this to see more details:

```python
# In src/main.py, around line 620
logger.error(f"Error generating Playwright snapshot ({error_type}): {error_msg}")
logger.error(f"Full traceback:\n{full_traceback}")
```

### Method 3: Test Directly from Python

Run this in a Python REPL to see the exact error:

```python
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # This will show the exact error location

asyncio.run(test())
```

## What to Look For

The traceback will show:
- **Which line** is causing the error
- **Which function** is calling it
- **What operation** is failing (browser launch, page navigation, etc.)

## Share the Traceback

Once you have the full traceback, share it and we can fix the exact issue!

