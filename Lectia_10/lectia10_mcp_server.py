from mcp.server.mcpserver import MCPServer

mcp = MCPServer("test-server")

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Adds 2 numbers
    
    Args:
        a: first number of your choice
        b: second number of your choice

    Returns:
        The sum of the 2 numbers
    """
    return a + b


@mcp.tool()
def multiply_numbers(a: int, b: int) -> int:
    """Multiply 2 numbers
        
    Args:
        a: first number of your choice
        b: second number of your choice

    Returns:
        The the product of the 2 numbers
    """
    return a * b


@mcp.resource("cv://cristian")
def get_cv() -> str:
    """Provides Cristian's CV content as a static resource, readable
    by any MCP client without needing to call it with parameters.

    Returns:
        The CV text content
    """
    return "Cristian Ungureanu - Tech Support background, learning AI Agent Development"

if __name__ == "__main__":
    mcp.run()