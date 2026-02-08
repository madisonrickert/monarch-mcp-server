"""Authentication tools."""

import asyncio
import json
import logging
import os
import traceback

from mcp.server.fastmcp import Context

from monarch_mcp_server import auth
from monarch_mcp_server.app import mcp
from monarch_mcp_server.client import clear_client_cache
from monarch_mcp_server.secure_session import secure_session

logger = logging.getLogger(__name__)


@mcp.tool()
async def setup_authentication() -> str:
    """Get instructions for setting up secure authentication with Monarch Money."""
    return """🔐 Monarch Money - Authentication Options

Option 1: Elicitation login (Recommended for interactive clients)
   Call 'monarch_login' to enter email/password (and MFA if needed)
   via a secure form in your client UI. Credentials never pass
   through the model. Or 'monarch_login_with_token' to paste a
   browser-copied session token.

Option 2: Google OAuth (browser-based)
   Call 'authenticate_with_google' to open a browser and sign in
   with your Google account.

Option 3: Email/Password (Terminal)
   Run in terminal: python login_setup.py

Call 'monarch_logout' to clear the stored session.

✅ Session persists across restarts
✅ Token stored securely in system keyring"""


@mcp.tool()
async def monarch_login(ctx: Context) -> str:
    """Sign in to Monarch Money.

    Opens a secure form in the client UI to collect email, password, and
    (if required) an MFA code. Credentials never pass through the model —
    they flow client-UI → server directly via the MCP protocol.
    """
    return await auth.login_interactive(ctx)


@mcp.tool()
async def monarch_login_with_token(ctx: Context) -> str:
    """Sign in to Monarch Money using a browser-copied session token.

    Useful for SSO users who can't use password login. Grab the token from
    browser DevTools → Application → Local Storage → app.monarchmoney.com.
    """
    return await auth.login_with_token_interactive(ctx)


@mcp.tool()
async def monarch_logout() -> str:
    """Clear the stored Monarch Money session from the system keyring."""
    return await auth.logout()


@mcp.tool()
async def authenticate_with_google() -> str:
    """
    Open a browser window to authenticate with Monarch Money using Google OAuth.

    This will:
    1. Open a browser window
    2. Navigate to Monarch login page
    3. You sign in with Google (or email/password)
    4. Token is automatically captured and saved

    Use this when you get authentication errors or need to refresh your session.

    Returns:
        Success or failure message.
    """
    try:
        from playwright.async_api import async_playwright

        captured_token = None

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled']
            )

            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )

            page = await context.new_page()

            async def handle_request(request):
                nonlocal captured_token
                auth_header = request.headers.get('authorization', '')
                if auth_header.startswith('Token ') and not captured_token:
                    captured_token = auth_header.replace('Token ', '')

            page.on('request', handle_request)

            await page.goto("https://app.monarch.com/login")

            # Wait for token capture (max 5 minutes)
            max_wait = 300
            waited = 0
            while not captured_token and waited < max_wait:
                await asyncio.sleep(1)
                waited += 1

            await browser.close()

            if captured_token:
                secure_session.save_token(captured_token)
                clear_client_cache()
                return json.dumps({"success": True, "message": "Authentication successful! Token saved."}, indent=2)
            else:
                return json.dumps({"success": False, "message": "Timeout - no token captured. Please try again."}, indent=2)

    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return json.dumps({
            "success": False,
            "message": f"Authentication failed: {str(e)}"
        }, indent=2)


@mcp.tool()
async def check_auth_status() -> str:
    """Check if already authenticated with Monarch Money."""
    try:
        token = secure_session.load_token()
        if token:
            status = "✅ Authentication token found in secure keyring storage\n"
        else:
            status = "❌ No authentication token found in keyring\n"

        email = os.getenv("MONARCH_EMAIL")
        if email:
            status += f"📧 Environment email: {email}\n"

        status += (
            "\n💡 Try get_accounts to test connection or run login_setup.py if needed."
        )

        return status
    except Exception as e:
        return f"Error checking auth status: {str(e)}"


@mcp.tool()
async def debug_session_loading() -> str:
    """Debug keyring session loading issues."""
    try:
        token = secure_session.load_token()
        if token:
            return f"✅ Token found in keyring (length: {len(token)})"
        else:
            return "❌ No token found in keyring. Run login_setup.py to authenticate."
    except Exception as e:
        error_details = traceback.format_exc()
        return f"❌ Keyring access failed:\nError: {str(e)}\nType: {type(e)}\nTraceback:\n{error_details}"
