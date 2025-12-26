"""
Enhanced Playwright Browser Navigation with Auto-Search

This module implements browser_navigate with automatic search functionality
as specified in the Playwright MCP Auto-Search Enhancement Specification.
"""

import logging
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Page, Locator, Browser, BrowserContext

logger = logging.getLogger(__name__)


async def browser_navigate(
    url: str,
    search_query: Optional[str] = None,
    auto_search: bool = True,
    search_box_selector: Optional[str] = None,
    search_button_selector: Optional[str] = None,
    wait_for_results: bool = True,
    wait_timeout: int = 10000,
    browser: Optional[Browser] = None,
    context: Optional[BrowserContext] = None,
    page: Optional[Page] = None,
) -> Dict[str, Any]:
    """
    Enhanced browser navigation with automatic search functionality.
    
    When searchQuery is provided, automatically:
    1. Navigates to the URL
    2. Detects and fills the search box
    3. Clicks search button or presses Enter
    4. Waits for results and returns results page snapshot
    
    Args:
        url: The URL to navigate to
        search_query: Optional search query to perform automatically
        auto_search: Whether to auto-perform search (default: True if search_query provided)
        search_box_selector: Optional custom selector for search box
        search_button_selector: Optional custom selector for search button
        wait_for_results: Whether to wait for results page to load (default: True)
        wait_timeout: Maximum wait time in ms (default: 10000)
        browser: Optional existing browser instance (for reuse)
        context: Optional existing browser context (for reuse)
        page: Optional existing page instance (for reuse)
        
    Returns:
        Dict with:
            - success: bool
            - url: str
            - search_performed: bool
            - search_query: Optional[str]
            - snapshot: str (accessibility snapshot in YAML format)
            - warnings: List[str]
            - errors: List[str]
    """
    warnings: List[str] = []
    errors: List[str] = []
    search_performed = False
    
    # Determine if we should perform search
    should_search = search_query and auto_search
    
    # If browser/context/page are provided, use them directly
    # Otherwise, create new instances
    if browser is not None or context is not None or page is not None:
        # Use provided instances - don't manage lifecycle
        if page is None:
            if context is None:
                raise ValueError("If browser is provided, context must also be provided. If context is provided, page must also be provided.")
            page = await context.new_page()
        if context is None:
            if browser is None:
                raise ValueError("If context is provided, browser must also be provided.")
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="America/New_York"
            )
            # Remove webdriver property to avoid detection
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
        
        # Execute with provided instances
        return await _execute_navigate(
            page, url, should_search, search_query,
            search_box_selector, search_button_selector,
            wait_for_results, wait_timeout, warnings, errors
        )
    
    # Create new browser instance using context manager pattern
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="America/New_York"
            )
            
            # Remove webdriver property to avoid detection
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            page = await context.new_page()
            
            return await _execute_navigate(
                page, url, should_search, search_query,
                search_box_selector, search_button_selector,
                wait_for_results, wait_timeout, warnings, errors
            )
    except Exception as e:
        error_msg = f"Error in browser_navigate: {str(e)}"
        logger.error(error_msg, exc_info=True)
        errors.append(error_msg)
        return {
            "success": False,
            "url": url,
            "search_performed": False,
            "search_query": search_query if should_search else None,
            "snapshot": "",
            "warnings": warnings,
            "errors": errors
        }


async def _execute_navigate(
    page: Page,
    url: str,
    should_search: bool,
    search_query: Optional[str],
    search_box_selector: Optional[str],
    search_button_selector: Optional[str],
    wait_for_results: bool,
    wait_timeout: int,
    warnings: List[str],
    errors: List[str]
) -> Dict[str, Any]:
    """
    Internal function to execute navigation and search logic.
    """
    search_performed = False
    
    # Step 1: Navigate to URL
    logger.info(f"Navigating to: {url}")
    try:
        await page.goto(url, wait_until="load", timeout=30000)
        # Wait a bit for dynamic content
        await page.wait_for_timeout(2000)
    except Exception as nav_error:
        logger.warning(f"Navigation error: {nav_error}")
        errors.append(f"Navigation error: {str(nav_error)}")
        # Continue anyway - might have partial page load
    
    # Step 2: Take snapshot for search box detection (if search requested)
    snapshot = ""
    if should_search:
        # First, take a snapshot to analyze page structure
        snapshot = await _generate_accessibility_snapshot(page)
        logger.info("Initial snapshot taken for search box detection")
        
        # Step 3: Detect and fill search box
        search_box = await _detect_search_box(
            page, search_box_selector, snapshot, warnings
        )
        
        if search_box:
            try:
                # Step 4: Type search query
                logger.info(f"Filling search box with: {search_query}")
                await search_box.fill(search_query)
                await page.wait_for_timeout(500)  # Small delay for input
                
                # Step 5: Detect and click search button (or press Enter)
                button_clicked = await _click_search_button(
                    page, search_button_selector, search_box, warnings
                )
                
                if button_clicked or not search_button_selector:
                    # Wait for search to complete
                    logger.info("Waiting for search results...")
                    try:
                        if wait_for_results:
                            await page.wait_for_load_state("networkidle", timeout=wait_timeout)
                        else:
                            await page.wait_for_timeout(3000)
                    except Exception:
                        # Fallback to shorter wait if networkidle times out
                        await page.wait_for_timeout(3000)
                    
                    search_performed = True
                    logger.info("Search performed successfully")
                else:
                    warnings.append("Search button not found - search may not have been triggered")
            except Exception as search_error:
                error_msg = f"Error performing search: {str(search_error)}"
                logger.warning(error_msg)
                warnings.append(error_msg)
                # Continue to return homepage snapshot
        else:
            warning_msg = "Search box not found - cannot perform automatic search"
            logger.warning(warning_msg)
            warnings.append(warning_msg)
    
    # Step 6: Generate final snapshot (either results page or homepage)
    if not snapshot or search_performed:
        snapshot = await _generate_accessibility_snapshot(page)
    
    return {
        "success": True,
        "url": url,
        "search_performed": search_performed,
        "search_query": search_query if should_search else None,
        "snapshot": snapshot,
        "warnings": warnings,
        "errors": errors
    }


async def _detect_search_box(
    page: Page,
    explicit_selector: Optional[str],
    snapshot: str,
    warnings: List[str]
) -> Optional[Locator]:
    """
    Detect search box on the page using priority order.
    
    Priority:
    1. Explicit selector (if provided)
    2. Accessibility tree analysis (role="searchbox")
    3. Common patterns (input[type="search"], etc.)
    4. Contextual search (placeholders, names, ids)
    """
    # Priority 1: Explicit selector
    if explicit_selector:
        try:
            locator = page.locator(explicit_selector).first
            if await locator.is_visible():
                logger.info(f"Using explicit search box selector: {explicit_selector}")
                return locator
        except Exception as e:
            warnings.append(f"Explicit selector '{explicit_selector}' not found: {str(e)}")
    
    # Priority 2: Accessibility tree - role="searchbox"
    try:
        searchbox = page.locator('[role="searchbox"]').first
        if await searchbox.is_visible():
            logger.info("Found search box via role='searchbox'")
            return searchbox
    except Exception:
        pass
    
    # Priority 3: Common patterns
    selectors = [
        'input[type="search"]',
        'input[placeholder*="search" i]',
        'input[placeholder*="Search" i]',
        'input[name*="search" i]',
        'input[id*="search" i]',
        'input[aria-label*="search" i]',
        'input[aria-label*="Search" i]',
    ]
    
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.is_visible():
                # Verify it's actually an input field
                tag_name = await locator.evaluate("el => el.tagName")
                if tag_name.upper() in ['INPUT', 'TEXTAREA']:
                    logger.info(f"Found search box via selector: {selector}")
                    return locator
        except Exception:
            continue
    
    # Priority 4: Contextual search - look for ticket/search site patterns
    contextual_selectors = [
        'input[placeholder*="Search events" i]',
        'input[placeholder*="Find tickets" i]',
        'input[placeholder*="Search artists" i]',
        'input[placeholder*="Search for" i]',
        'input[name*="q" i]',  # Common search query parameter name
        'input[id*="q" i]',
    ]
    
    for selector in contextual_selectors:
        try:
            locator = page.locator(selector).first
            if await locator.is_visible():
                tag_name = await locator.evaluate("el => el.tagName")
                if tag_name.upper() in ['INPUT', 'TEXTAREA']:
                    logger.info(f"Found search box via contextual selector: {selector}")
                    return locator
        except Exception:
            continue
    
    # No search box found
    return None


async def _click_search_button(
    page: Page,
    explicit_selector: Optional[str],
    search_box: Locator,
    warnings: List[str]
) -> bool:
    """
    Detect and click search button.
    
    Priority:
    1. Explicit selector (if provided)
    2. Form submit button within same form
    3. Aria label matching
    4. Button text matching
    5. Fallback: Enter key press
    """
    # Priority 1: Explicit selector
    if explicit_selector:
        try:
            button = page.locator(explicit_selector).first
            if await button.is_visible():
                await button.click()
                logger.info(f"Clicked search button via explicit selector: {explicit_selector}")
                return True
        except Exception as e:
            warnings.append(f"Explicit button selector '{explicit_selector}' not found: {str(e)}")
    
    # Priority 2: Form submit button - find form containing search box
    try:
        # Check if search box is in a form, and find submit button within that form
        form_locator = search_box.locator('xpath=ancestor::form')
        form_count = await form_locator.count()
        if form_count > 0:
            # Look for submit button within the form
            submit_button = form_locator.locator('button[type="submit"], input[type="submit"]').first
            if await submit_button.is_visible():
                await submit_button.click()
                logger.info("Clicked form submit button")
                return True
    except Exception:
        pass
    
    # Priority 3: Aria label matching
    try:
        button = page.locator('button[aria-label*="search" i], button[aria-label*="Search" i], button[aria-label*="submit" i]').first
        if await button.is_visible():
            await button.click()
            logger.info("Clicked search button via aria-label")
            return True
    except Exception:
        pass
    
    # Priority 4: Button text matching
    try:
        # Try different text patterns
        text_patterns = ["Search", "search", "Go", "Submit", "Find"]
        for pattern in text_patterns:
            try:
                button = page.get_by_role("button", name=pattern, exact=False).first
                if await button.is_visible():
                    await button.click()
                    logger.info(f"Clicked search button via text content: {pattern}")
                    return True
            except Exception:
                continue
        # Also try with locator filter
        buttons = page.locator('button').all()
        for btn in buttons[:10]:  # Limit to first 10 buttons
            try:
                text = await btn.inner_text()
                if text and any(pattern.lower() in text.lower() for pattern in text_patterns):
                    if await btn.is_visible():
                        await btn.click()
                        logger.info(f"Clicked search button via text: {text}")
                        return True
            except Exception:
                continue
    except Exception:
        pass
    
    # Priority 5: Fallback - Press Enter in search box
    try:
        await search_box.press("Enter")
        logger.info("Pressed Enter in search box (fallback)")
        return True
    except Exception as e:
        warnings.append(f"Failed to press Enter in search box: {str(e)}")
        return False


async def _generate_accessibility_snapshot(page: Page) -> str:
    """
    Generate an accessibility snapshot of the current page.
    Returns YAML-like formatted string.
    """
    try:
        # Use Playwright's accessibility snapshot API
        snapshot = await page.accessibility.snapshot()
        
        # Format as YAML-like structure
        def format_node(node: Dict[str, Any], indent: int = 0) -> str:
            """Recursively format accessibility tree nodes"""
            if not node:
                return ""
            
            prefix = "  " * indent
            role = node.get("role", "unknown")
            name = node.get("name", "")
            
            lines = []
            if name:
                lines.append(f'{prefix}- {role} "{name}"')
            else:
                lines.append(f'{prefix}- {role}')
            
            # Add children
            children = node.get("children", [])
            for child in children:
                child_output = format_node(child, indent + 1)
                if child_output:
                    lines.append(child_output)
            
            return "\n".join(lines)
        
        if snapshot:
            return format_node(snapshot)
        else:
            return "No accessibility tree available"
            
    except Exception as e:
        logger.warning(f"Error generating accessibility snapshot: {e}")
        # Fallback to simpler DOM-based snapshot
        try:
            # Get a simplified text representation
            body_text = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, a, button, input, textarea, [role]');
                    const results = [];
                    elements.forEach(el => {
                        const role = el.getAttribute('role') || el.tagName.toLowerCase();
                        const name = el.textContent?.trim().substring(0, 100) || el.getAttribute('aria-label') || '';
                        if (name) {
                            results.push(`- ${role} "${name}"`);
                        } else {
                            results.push(`- ${role}`);
                        }
                    });
                    return results.slice(0, 100).join('\\n');  // Limit to first 100 elements
                }
            """)
            return body_text or "Could not generate snapshot"
        except Exception:
            return "Error generating snapshot"

