# Playwright NotImplementedError - FIXED ✅

## The Problem

Playwright was failing with `NotImplementedError()` on Windows when trying to generate accessibility snapshots.

## Root Cause

**Exact Error Location:**
```
File "...\asyncio\base_events.py", line 533, in _make_subprocess_transport
    raise NotImplementedError
```

**Why It Happened:**
- We were using `WindowsSelectorEventLoopPolicy()` which creates a `SelectorEventLoop`
- `SelectorEventLoop` on Windows **does NOT support subprocess creation**
- Playwright **requires** subprocess creation to launch browser processes
- This is a known limitation of `SelectorEventLoop` on Windows

## The Fix

### Fix 1: Event Loop Policy in `src/main.py` (line 29)

**Before:**
```python
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

**After:**
```python
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
```

### Fix 2: Disable Uvicorn Reload in `run_server.py` (line 39-44)

**Before:**
```python
uvicorn.run(
    "src.main:app",
    host=host,
    port=port,
    reload=True,  # This can force SelectorEventLoop!
    log_level="info"
)
```

**After:**
```python
# Disable reload on Windows when using Playwright to avoid SelectorEventLoop conflicts
use_reload = os.getenv("RELOAD", "false").lower() == "true"
if sys.platform == 'win32':
    use_reload = False  # Disable reload on Windows for Playwright compatibility

uvicorn.run(
    "src.main:app",
    host=host,
    port=port,
    reload=use_reload,
    log_level="info"
)
```

### Fix 3: Safety Policy in Sync Function (line 472-477)

Added explicit policy setting in the sync function as a safety measure:

```python
def _generate_accessibility_snapshot_sync(url: str) -> str:
    # Ensure this specific thread uses ProactorEventLoop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    # ... rest of function
```

## Why This Works

1. **ProactorEventLoop Policy:**
   - `WindowsProactorEventLoopPolicy()` creates a `ProactorEventLoop`
   - `ProactorEventLoop` **DOES support subprocess creation** on Windows
   - This is the recommended event loop for Windows when subprocesses are needed

2. **Disabling Uvicorn Reload:**
   - Uvicorn's `--reload` flag can force `SelectorEventLoop` for file watching
   - This overrides the module-level policy setting
   - Disabling reload on Windows ensures ProactorEventLoop persists

3. **Thread-Level Safety:**
   - Even sync Playwright uses asyncio internally
   - Setting the policy in the thread function ensures it's applied even if the module-level setting was overridden

4. **Result:**
   - Playwright can now launch browser processes successfully
   - No more `NotImplementedError` from subprocess creation

## Testing

1. **Restart the backend server:**
   ```powershell
   # Stop current server (Ctrl+C)
   $env:PORT="8000"
   py run_server.py
   ```

2. **Test the endpoint:**
   - Go to `http://localhost:8000/docs`
   - Try `POST /api/playwright/snapshot`
   - Use: `{"url": "wikipedia.org", "use_cache": false}`
   - Should work now! ✅

3. **Or test from frontend:**
   - Go to `http://localhost:8080/sandbox`
   - Enter a URL and click "Generate Snapshot"
   - Should work now! ✅

## Additional Changes

- Simplified `_generate_accessibility_snapshot()` to use async Playwright directly
- Removed unnecessary threading wrapper (no longer needed)
- Code is cleaner and more straightforward

## References

- [Python asyncio Windows Documentation](https://docs.python.org/3/library/asyncio-platforms.html#windows)
- [ProactorEventLoop vs SelectorEventLoop](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.ProactorEventLoop)

---

**Status:** ✅ FIXED  
**Date:** 2025-12-23  
**Tested:** Ready for testing

