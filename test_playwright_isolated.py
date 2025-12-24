#!/usr/bin/env python3
"""
Isolated test to reproduce the NotImplementedError
Run this to see the exact error location
"""

import asyncio
import sys

# Set event loop policy for Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_async_playwright():
    """Test async Playwright directly"""
    print("Testing async Playwright...")
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            print("[OK] Playwright context created")
            browser = await p.chromium.launch(headless=True)
            print("[OK] Browser launched")
            context = await browser.new_context()
            print("[OK] Context created")
            page = await context.new_page()
            print("[OK] Page created")
            await page.goto("https://wikipedia.org", timeout=10000)
            print("[OK] Navigated to page")
            result = await page.evaluate("() => document.title")
            print(f"[OK] Got result: {result}")
            await browser.close()
            print("\n[SUCCESS] Async Playwright works!")
            return True
    except NotImplementedError as e:
        print(f"\n[ERROR] NotImplementedError: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sync_playwright():
    """Test sync Playwright directly"""
    print("\nTesting sync Playwright...")
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            print("[OK] Playwright context created")
            browser = p.chromium.launch(headless=True)
            print("[OK] Browser launched")
            context = browser.new_context()
            print("[OK] Context created")
            page = context.new_page()
            print("[OK] Page created")
            page.goto("https://wikipedia.org", timeout=10000)
            print("[OK] Navigated to page")
            result = page.evaluate("() => document.title")
            print(f"[OK] Got result: {result}")
            browser.close()
            print("\n[SUCCESS] Sync Playwright works!")
            return True
    except NotImplementedError as e:
        print(f"\n[ERROR] NotImplementedError: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Playwright Compatibility Test")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print("=" * 60)
    
    # Test sync first (simpler)
    sync_result = test_sync_playwright()
    
    # Test async
    async_result = asyncio.run(test_async_playwright())
    
    print("\n" + "=" * 60)
    print("Results:")
    print(f"  Sync Playwright: {'✅ PASS' if sync_result else '❌ FAIL'}")
    print(f"  Async Playwright: {'✅ PASS' if async_result else '❌ FAIL'}")
    print("=" * 60)
    
    if sync_result:
        print("\n💡 SOLUTION: Use sync_playwright() in a thread!")
    elif async_result:
        print("\n💡 SOLUTION: Use async_playwright() directly!")
    else:
        print("\n⚠️  Both failed - check the tracebacks above")

