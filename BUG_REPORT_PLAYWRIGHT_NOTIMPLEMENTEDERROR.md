# Bug Report: NotImplementedError in Playwright Sandbox on Windows

## 🐛 Bug Summary

**Severity:** High  
**Status:** Open  
**Component:** Playwright Sandbox Feature  
**Platform:** Windows 10/11  
**Python Version:** 3.13  
**Playwright Version:** 1.57.0

## 📋 Problem Description

The Playwright Sandbox feature fails to generate accessibility snapshots on Windows with a `NotImplementedError()`. The error occurs when attempting to use Playwright's async API within FastAPI's async context on Windows.

## 🔄 What We've Tried

### Attempt 1: Direct Async Playwright
- **Approach:** Used `async_playwright()` directly in FastAPI async function
- **Result:** `NotImplementedError()` - Windows event loop incompatibility

### Attempt 2: Threading with Async
- **Approach:** Wrapped async Playwright in `anyio.to_thread.run_sync()`
- **Result:** `NotImplementedError()` - Event loop policy issues

### Attempt 3: Custom Event Loop in Thread
- **Approach:** Created new event loop in separate thread with `WindowsSelectorEventLoopPolicy`
- **Result:** `NotImplementedError()` - Still failing

### Attempt 4: Sync Playwright in Thread
- **Approach:** Using `sync_playwright()` in `ThreadPoolExecutor` with `run_in_executor`
- **Result:** **CURRENT STATUS** - Needs testing after server restart

## 🔍 Error Details

### Error Message
```
Error: Failed to generate snapshot: Playwright compatibility issue: NotImplementedError()
```

### HTTP Response
- **Status Code:** 500 Internal Server Error
- **Endpoint:** `POST /api/playwright/snapshot`
- **Request Body:** `{"url": "wikipedia.org", "use_cache": false}`

### Backend Logs
The error is caught and logged, but the full traceback is needed to identify the exact line causing the issue.

## 🖥️ Environment

- **OS:** Windows 10/11 (Build 26100)
- **Python:** 3.13
- **Playwright:** 1.57.0
- **FastAPI:** 0.115.0+
- **Uvicorn:** 0.32.0+
- **Backend Port:** 8000
- **Frontend Port:** 8080/8081

## 📝 Steps to Reproduce

1. Install Playwright:
   ```powershell
   py -m pip install playwright
   py -m playwright install chromium
   ```

2. Start backend server:
   ```powershell
   $env:PORT="8000"
   py run_server.py
   ```

3. Start frontend:
   ```powershell
   npm run dev
   ```

4. Navigate to: `http://localhost:8080/sandbox`

5. Enter URL: `wikipedia.org` or `google.com`

6. Click "Generate Snapshot"

7. **Observed:** Error message appears: "Failed to generate snapshot: Playwright compatibility issue: NotImplementedError()"

8. **Expected:** Snapshot should be generated and displayed

## 🔧 Current Implementation

### Code Location
- **File:** `src/main.py`
- **Function:** `_generate_accessibility_snapshot()` (line ~600)
- **Helper:** `_generate_accessibility_snapshot_sync()` (line ~470)

### Current Approach
```python
# Uses sync_playwright() in a thread
def _generate_accessibility_snapshot_sync(url: str) -> str:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        # ... browser operations ...
```

```python
# Wraps sync function in thread executor
async def _generate_accessibility_snapshot(url: str) -> str:
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, _generate_accessibility_snapshot_sync, url)
```

## 🎯 Root Cause (CONFIRMED)

**The exact error location:**
```
File "...\asyncio\base_events.py", line 533, in _make_subprocess_transport
    raise NotImplementedError
```

**Root Cause:**
- Python 3.13 on Windows uses `SelectorEventLoop` by default
- `SelectorEventLoop` does **NOT** support subprocess creation (`asyncio.create_subprocess_exec`)
- Playwright **requires** subprocess creation to launch browser processes
- This is a **known limitation** of `SelectorEventLoop` on Windows

**The Fix:**
- Use `ProactorEventLoop` on Windows instead of `SelectorEventLoop`
- `ProactorEventLoop` **DOES** support subprocess creation
- This is the recommended event loop for Windows when subprocesses are needed

## 💡 Potential Solutions

### Solution 1: Use ProactorEventLoop (✅ IMPLEMENTED)
- ✅ Change from `WindowsSelectorEventLoopPolicy()` to `WindowsProactorEventLoopPolicy()`
- ✅ `ProactorEventLoop` supports subprocess creation on Windows
- ✅ Use async Playwright directly (no threading needed)
- ✅ **Status:** Ready to test

### Solution 2: Subprocess Approach
- Launch Playwright in a separate Python process
- Communicate via stdin/stdout or HTTP
- More isolated but adds complexity

### Solution 3: Use Playwright's HTTP API
- Run Playwright as a separate service
- Communicate via HTTP requests
- Most isolated but requires separate process management

### Solution 4: Alternative Library
- Use Selenium instead of Playwright
- Or use `requests-html` with PyQt5/headless browser
- May have different compatibility characteristics

## 📊 Expected vs Actual Behavior

| Aspect | Expected | Actual |
|--------|----------|--------|
| Snapshot Generation | ✅ Works | ❌ NotImplementedError |
| Error Message | Clear error | Generic "compatibility issue" |
| Backend Logs | Full traceback | Partial (needs full traceback) |
| Windows Compatibility | Should work | ❌ Failing |

## 🔍 Debugging Information Needed

To properly diagnose, we need:

1. **Full Python Traceback** from backend terminal when error occurs
2. **Playwright Version:** `playwright --version`
3. **Python Version:** `python --version`
4. **Event Loop Details:** What event loop is FastAPI using?
5. **Subprocess Behavior:** Are Playwright subprocesses launching correctly?

## 🧪 Test Cases

### Test Case 1: Simple URL
- **Input:** `wikipedia.org`
- **Expected:** Snapshot generated successfully
- **Actual:** NotImplementedError

### Test Case 2: Popular Site (Cached)
- **Input:** `google.com`
- **Expected:** Returns cached snapshot instantly
- **Actual:** NotImplementedError (never gets to cache)

### Test Case 3: Complex Site
- **Input:** `github.com`
- **Expected:** Snapshot with many elements
- **Actual:** NotImplementedError

## 🎁 Bug Bounty Requirements

To claim this bug bounty, the fix must:

1. ✅ **Work on Windows 10/11** - Primary requirement
2. ✅ **Generate accessibility snapshots** - Core functionality
3. ✅ **Work within FastAPI async context** - Architecture requirement
4. ✅ **Handle errors gracefully** - User experience
5. ✅ **Support caching** - Performance requirement
6. ✅ **Be production-ready** - Code quality standards

### Bonus Points

- ⭐ Works on Linux/Mac as well (cross-platform)
- ⭐ Better error messages
- ⭐ Performance optimizations
- ⭐ Comprehensive logging
- ⭐ Unit tests

## 📚 References

- [Playwright Python Docs](https://playwright.dev/python/)
- [FastAPI Async Guide](https://fastapi.tiangolo.com/async/)
- [Python asyncio Windows Issues](https://docs.python.org/3/library/asyncio-platforms.html#windows)
- [Playwright GitHub Issues](https://github.com/microsoft/playwright-python/issues)

## 🔗 Related Files

- `src/main.py` - Main backend implementation
- `src/pages/Sandbox.tsx` - Frontend component
- `requirements.txt` - Dependencies
- `test_playwright.py` - Test script (works standalone)

## 📝 Notes

- The standalone test script (`test_playwright.py`) **works correctly** when run directly
- The issue only occurs when Playwright is called from within FastAPI's async context
- This suggests the problem is with **integration**, not Playwright itself

## 🚀 Next Steps

1. **Get Full Traceback:** Check backend terminal when error occurs
2. **Test Current Fix:** Restart server and test sync Playwright approach
3. **If Still Failing:** Consider subprocess or HTTP API approach
4. **Document Solution:** Update code with working solution

---

**Reported By:** AI Assistant  
**Date:** 2025-12-23  
**Last Updated:** 2025-12-23

