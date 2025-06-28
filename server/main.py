from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings
from fastapi import HTTPException
from mcp.server.auth.middleware.auth_context import get_access_token

import os
import subprocess
from dotenv import load_dotenv
import sqlite3
from typing import Dict
import uvicorn
import logging

from auth import KeycloakOAuthProvider

load_dotenv()

if os.environ.get("OTEL_ENABLED", "false").lower() == "true":
    from otel import setup_telemetry
    setup_telemetry()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "test",
    auth_server_provider=KeycloakOAuthProvider(
        server_url=os.environ.get("KEYCLOAK_SERVER_URL"),
        realm_name=os.environ.get("KEYCLOAK_REALM")
    ),
    auth=AuthSettings(
        issuer_url=os.environ.get("KEYCLOAK_SERVER_URL"),
        resource_server_url=os.environ.get("KEYCLOAK_SERVER_URL")
    )
)

conn = sqlite3.connect("./server.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS elements (name TEXT, value INTEGER)")

"""
WAF can be configured by forwarding traffic to MCP server.
In our case it is not necesarry because we handle user inputs safely.
But it should be considered nonetheless.
See following WAFs: SafeLine, Nginx ModSecurity
"""

@mcp.tool()
async def get_all_elements() -> Dict[str, int]:
    cursor.execute("SELECT name, value FROM elements")
    elements = {row[0]: row[1] for row in cursor.fetchall()}
    return elements


@mcp.tool()
async def remove_element(name: str) -> bool:
    """
    Remove an element
    """
    if not 'admin' in get_access_token().scopes:
        raise HTTPException(status_code=403, detail="Admin role required")
    cursor.execute("DELETE FROM elements WHERE name = ?", (name,))
    logger.info(f"Remove element: {name}")
    conn.commit()
    success = cursor.rowcount > 0
    return success

@mcp.tool()
async def store_value(name: str, value: int) -> bool:
    """
    Insert new element
    """
    if not 'admin' in get_access_token().scopes:
        raise HTTPException(status_code=403, detail="Admin role required")
    logger.info(f"Store element: {name} with value {value}")
    cursor.execute("INSERT INTO elements (name, value) VALUES (?, ?)", (name, value))
    conn.commit()
    return True

@mcp.tool()
async def check_connectivity(ip: str) -> bool:
    """
    Check connectivity to a given IP address
    """
    return subprocess.run(["ping", "-W", "5", "-c", "1", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

if __name__ == "__main__":
    app = mcp.streamable_http_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        # Rate limitting can be configured with reverse proxy instead as well
        limit_concurrency=100,  # Maximum number of concurrent connections
        limit_max_requests=1000,  # Maximum number of requests per connection
        timeout_keep_alive=120,  # Keep-alive timeout in seconds
    )