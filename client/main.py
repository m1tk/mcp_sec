from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
import asyncio
from dotenv import load_dotenv
import os
import httpx
from keycloak import KeycloakOpenID

from gemini import llm
from local_tools import list_files, read_file_content

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
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

async def run_agent():
    client = MultiServerMCPClient(
        {
            "mcp-1": {
                "url": "http://localhost:8000/mcp/",
                "transport": "streamable_http",
                "httpx_client_factory": jwt_factory
            }
        }
    )
    tools = await client.get_tools()
    tools.extend([list_files, read_file_content])
    agent = create_react_agent(llm, tools)

    history = [("system", "You are a helpful assistant. You must always call a tool when the user's request requires it. Do not use cached answers. If the user asks for something that needs a tool, call the tool, even if you have called it before for a similar request.")]

    while True:
        try:
            user_input = await asyncio.to_thread(input, "\nYou: ")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if user_input.lower() in ("exit", "quit"):
            print("Exiting.")
            break

        if not user_input.strip():
            continue

        print("Agent: ", end="", flush=True)
        try:
            agent_response_content = ""
            async for event in agent.astream_events(
                {"messages": history + [("user", user_input)]},
                version="v2",
            ):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        # Print content as it comes in
                        print(content, end="", flush=True)
                        agent_response_content += content
            print()
            history.append(("user", user_input))
            history.append(("assistant", agent_response_content))
        except Exception as e:
            print(f"\nError during agent execution: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run_agent())
    except Exception as e:
        print(f"An error occurred: {e}")