from fastmcp import FastMCP

mcp = FastMCP("Spotify Copilot")


@mcp.tool()
def hello_spotify(name: str) -> str:
    """
    Test MCP tool.
    """
    return f"Hello {name}, MCP is working!"


if __name__ == "__main__":
    mcp.run()