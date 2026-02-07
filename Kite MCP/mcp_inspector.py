import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from kite_tools import KiteTools
from config import KiteConfig
import json

# Initialize Kite tools
kite_tools = KiteTools()

# Create MCP Server
app = Server("kite-mcp-server")


# ========== DEFINE MCP TOOLS ==========

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available Kite trading tools"""
    return [
        types.Tool(
            name="kite_get_profile",
            description="Get user profile information including name, email, and exchanges",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="kite_get_holdings",
            description="Get all stock holdings with quantities, average prices, and P&L",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="kite_get_positions",
            description="Get current day's trading positions",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="kite_get_margins",
            description="Get account margins and available balance",
            inputSchema={
                "type": "object",
                "properties": {
                    "segment": {
                        "type": "string",
                        "description": "Segment to get margins for (equity, commodity)",
                        "enum": ["equity", "commodity"],
                        "default": "equity"
                    }
                }
            }
        ),
        types.Tool(
            name="kite_place_order",
            description="Place a buy or sell order",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol (e.g., INFY, RELIANCE)"
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Exchange (NSE or BSE)",
                        "enum": ["NSE", "BSE"],
                        "default": "NSE"
                    },
                    "transaction_type": {
                        "type": "string",
                        "description": "Buy or Sell",
                        "enum": ["BUY", "SELL"]
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Number of shares to trade"
                    },
                    "order_type": {
                        "type": "string",
                        "description": "Market or Limit order",
                        "enum": ["MARKET", "LIMIT"],
                        "default": "MARKET"
                    },
                    "product": {
                        "type": "string",
                        "description": "Product type (CNC for delivery, MIS for intraday)",
                        "enum": ["CNC", "MIS"],
                        "default": "CNC"
                    },
                    "price": {
                        "type": "number",
                        "description": "Price for limit orders (optional)"
                    }
                },
                "required": ["symbol", "transaction_type", "quantity"]
            }
        ),
        types.Tool(
            name="kite_get_quote",
            description="Get live market quotes for instruments",
            inputSchema={
                "type": "object",
                "properties": {
                    "instruments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of instruments in format NSE:SYMBOL (e.g., ['NSE:INFY', 'NSE:RELIANCE'])"
                    }
                },
                "required": ["instruments"]
            }
        ),
        types.Tool(
            name="kite_logout",
            description="Logout and invalidate current session",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Execute MCP tool calls"""

    # Check authentication for most tools
    if name != "kite_login" and not KiteConfig.is_authenticated():
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "Not authenticated. Please login first using kite_login."
            })
        )]

    result = None

    # Route to appropriate Kite tool
    if name == "kite_get_profile":
        result = kite_tools.get_profile()

    elif name == "kite_get_holdings":
        result = kite_tools.get_holdings()

    elif name == "kite_get_positions":
        result = kite_tools.get_positions()

    elif name == "kite_get_margins":
        segment = arguments.get("segment", "equity")
        result = kite_tools.get_margins(segment)

    elif name == "kite_place_order":
        result = kite_tools.place_order(
            symbol=arguments["symbol"],
            exchange=arguments.get("exchange", "NSE"),
            transaction_type=arguments["transaction_type"],
            quantity=arguments["quantity"],
            order_type=arguments.get("order_type", "MARKET"),
            product=arguments.get("product", "CNC"),
            price=arguments.get("price")
        )

    elif name == "kite_get_quote":
        result = kite_tools.get_quote(arguments["instruments"])

    elif name == "kite_logout":
        result = kite_tools.invalidate_session()

    else:
        result = {"success": False, "error": f"Unknown tool: {name}"}

    return [types.TextContent(
        type="text",
        text=json.dumps(result, indent=2, default=str)
    )]


async def main():
    """Run MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    print("🚀 Kite MCP Server starting...")
    print("Connect using MCP Inspector or Claude Desktop")
    asyncio.run(main())
