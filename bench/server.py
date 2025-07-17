import asyncio
import time
import statistics
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import httpx
from keycloak import KeycloakOpenID
from dotenv import load_dotenv
import os
import subprocess

load_dotenv()

REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

keycloak_openid = KeycloakOpenID(
    server_url=os.environ.get("KEYCLOAK_SERVER_URL"),
    client_id=os.environ.get("KEYCLOAK_CLIENT_ID"),
    realm_name=os.environ.get("KEYCLOAK_REALM"),
    client_secret_key=os.environ.get("KEYCLOAK_CLIENT_SECRET"),
)
access_token = None

def jwt_factory(headers=None, timeout=None, auth=None):
    global access_token
    if not access_token or not keycloak_openid.introspect(access_token["access_token"])['active']:
        access_token = keycloak_openid.refresh_token(REFRESH_TOKEN)
    return httpx.AsyncClient(
        headers={"Authorization": f"Bearer {access_token['access_token']}"},
    )

async def benchmark(session):
    latencies_small = []
    latencies_large = []
    small_payload = "a" * 10
    large_payload = "b" * 500

    for _ in range(50):
        start = time.perf_counter()
        await session.call_tool("store_value", { 'name': small_payload, 'value': 42 })
        end = time.perf_counter()
        latencies_small.append(end - start)
    median_small = statistics.median(latencies_small)
    print(f"Median latency (small payload): {median_small:.6f} seconds")
    for _ in range(50):
        start = time.perf_counter()
        await session.call_tool("store_value", { 'name': large_payload, 'value': 42 })
        end = time.perf_counter()
        latencies_large.append(end - start)
    median_large = statistics.median(latencies_large)
    print(f"Median latency (large payload): {median_large:.6f} seconds")

async def bench_no_auth(server):
    async with streamablehttp_client(server) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await benchmark(session)

async def bench_auth(server):
    async with streamablehttp_client(server, httpx_client_factory=jwt_factory) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await benchmark(session)

async def main():
    global access_token
    server = "http://localhost:8000/mcp/"
    waf_server = "http://localhost:8080/mcp/"

    print("Benchmarking baseline:")
    server_proc = subprocess.Popen(
        ["python3", "server/main.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    try:
        await asyncio.sleep(5)
        await bench_no_auth(server)
    finally:
        server_proc.terminate()
        server_proc.wait()

    print("Benchmarking with auth:")
    env = os.environ.copy()
    env["AUTH_ENABLED"] = "true"
    server_proc = subprocess.Popen(
        ["python3", "server/main.py"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    try:
        await asyncio.sleep(5)
        await bench_auth(server)
    finally:
        server_proc.terminate()
        server_proc.wait()

    print("Benchmarking with rate limiting:")
    env = os.environ.copy()
    env["RATE_LIMITING_ENABLED"] = "true"
    server_proc = subprocess.Popen(
        ["python3", "server/main.py"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    try:
        await asyncio.sleep(5)
        await bench_no_auth(server)
    finally:
        server_proc.terminate()
        server_proc.wait()

    print("Benchmarking with waf:")
    server_proc = subprocess.Popen(
        ["python3", "server/main.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    try:
        await asyncio.sleep(5)
        await bench_no_auth(waf_server)
    finally:
        server_proc.terminate()
        server_proc.wait()

    print("Benchmarking with all mitigations:")
    access_token = None
    env = os.environ.copy()
    env["RATE_LIMITING_ENABLED"] = "true"
    env["AUTH_ENABLED"] = "true"
    server_proc = subprocess.Popen(
        ["python3", "server/main.py"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    try:
        await asyncio.sleep(5)
        await bench_auth(waf_server)
    finally:
        server_proc.terminate()
        server_proc.wait()

if __name__ == "__main__":
    asyncio.run(main())
