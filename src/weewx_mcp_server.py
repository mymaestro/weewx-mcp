#!/usr/bin/env python3
"""
WeeWX MCP Server - Query your personal weather station data with natural language

This MCP server provides tools to query WeeWX database for weather information.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Any, Sequence
import sys

# MCP SDK imports
try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: mcp package not found. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Default WeeWX database path - users can override via config
DEFAULT_DB_PATH = "/var/lib/weewx/weewx.sdb"

class WeeWXMCPServer:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.server = Server("weewx-mcp")
        
    def connect_db(self):
        """Connect to WeeWX database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Access columns by name
            return conn
        except sqlite3.Error as e:
            raise Exception(f"Could not connect to WeeWX database at {self.db_path}: {e}")
    
    def get_current_conditions(self) -> dict:
        """Get the most recent weather reading"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # Get the latest record from archive table
        cursor.execute("""
            SELECT dateTime, outTemp, outHumidity, barometer, windSpeed, 
                   windDir, rain, rainRate, dewpoint
            FROM archive 
            ORDER BY dateTime DESC 
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {"error": "No data found"}
        
        return {
            "timestamp": datetime.fromtimestamp(row['dateTime']).isoformat(),
            "temperature": row['outTemp'],
            "humidity": row['outHumidity'],
            "pressure": row['barometer'],
            "wind_speed": row['windSpeed'],
            "wind_direction": row['windDir'],
            "rain": row['rain'],
            "rain_rate": row['rainRate'],
            "dewpoint": row['dewpoint']
        }
    
    def query_temperature_range(self, start_date: str, end_date: str) -> dict:
        """Get temperature statistics for a date range"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # Convert ISO dates to Unix timestamps
        start_ts = int(datetime.fromisoformat(start_date).timestamp())
        end_ts = int(datetime.fromisoformat(end_date).timestamp())
        
        cursor.execute("""
            SELECT 
                MIN(outTemp) as min_temp,
                MAX(outTemp) as max_temp,
                AVG(outTemp) as avg_temp,
                MIN(dateTime) as min_temp_time,
                MAX(dateTime) as max_temp_time
            FROM archive 
            WHERE dateTime >= ? AND dateTime <= ?
        """, (start_ts, end_ts))
        
        row = cursor.fetchone()
        
        # Get the actual dates when min/max occurred
        cursor.execute("""
            SELECT dateTime, outTemp 
            FROM archive 
            WHERE dateTime >= ? AND dateTime <= ?
            ORDER BY outTemp DESC 
            LIMIT 1
        """, (start_ts, end_ts))
        max_row = cursor.fetchone()
        
        cursor.execute("""
            SELECT dateTime, outTemp 
            FROM archive 
            WHERE dateTime >= ? AND dateTime <= ?
            ORDER BY outTemp ASC 
            LIMIT 1
        """, (start_ts, end_ts))
        min_row = cursor.fetchone()
        
        conn.close()
        
        return {
            "period": f"{start_date} to {end_date}",
            "min_temperature": row['min_temp'],
            "max_temperature": row['max_temp'],
            "avg_temperature": round(row['avg_temp'], 1) if row['avg_temp'] else None,
            "hottest_day": datetime.fromtimestamp(max_row['dateTime']).strftime('%Y-%m-%d %H:%M') if max_row else None,
            "coldest_day": datetime.fromtimestamp(min_row['dateTime']).strftime('%Y-%m-%d %H:%M') if min_row else None
        }
    
    def query_rainfall(self, start_date: str, end_date: str) -> dict:
        """Get rainfall totals for a date range"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        start_ts = int(datetime.fromisoformat(start_date).timestamp())
        end_ts = int(datetime.fromisoformat(end_date).timestamp())
        
        cursor.execute("""
            SELECT SUM(rain) as total_rain,
                   COUNT(*) as num_readings,
                   MAX(rainRate) as max_rain_rate
            FROM archive 
            WHERE dateTime >= ? AND dateTime <= ?
        """, (start_ts, end_ts))
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            "period": f"{start_date} to {end_date}",
            "total_rainfall": round(row['total_rain'], 2) if row['total_rain'] else 0,
            "max_rain_rate": row['max_rain_rate'],
            "num_readings": row['num_readings']
        }
    
    def find_wind_events(self, min_speed: float, start_date: str, end_date: str) -> list:
        """Find instances where wind exceeded a threshold"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        start_ts = int(datetime.fromisoformat(start_date).timestamp())
        end_ts = int(datetime.fromisoformat(end_date).timestamp())
        
        cursor.execute("""
            SELECT dateTime, windSpeed, windGust, windDir
            FROM archive 
            WHERE dateTime >= ? AND dateTime <= ?
              AND (windSpeed >= ? OR windGust >= ?)
            ORDER BY windSpeed DESC
            LIMIT 50
        """, (start_ts, end_ts, min_speed, min_speed))
        
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            events.append({
                "timestamp": datetime.fromtimestamp(row['dateTime']).strftime('%Y-%m-%d %H:%M'),
                "wind_speed": row['windSpeed'],
                "wind_gust": row['windGust'],
                "wind_direction": row['windDir']
            })
        
        return events
    
    def setup_handlers(self):
        """Setup MCP tool handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available weather query tools"""
            return [
                Tool(
                    name="get_current_conditions",
                    description="Get the most recent weather conditions from your station",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="query_temperature_range",
                    description="Get temperature statistics (min, max, average) for a date range",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start date in ISO format (YYYY-MM-DD)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date in ISO format (YYYY-MM-DD)"
                            }
                        },
                        "required": ["start_date", "end_date"]
                    }
                ),
                Tool(
                    name="query_rainfall",
                    description="Get total rainfall and statistics for a date range",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start date in ISO format (YYYY-MM-DD)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date in ISO format (YYYY-MM-DD)"
                            }
                        },
                        "required": ["start_date", "end_date"]
                    }
                ),
                Tool(
                    name="find_wind_events",
                    description="Find times when wind speed exceeded a threshold",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "min_speed": {
                                "type": "number",
                                "description": "Minimum wind speed threshold (mph or m/s depending on your setup)"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Start date in ISO format (YYYY-MM-DD)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date in ISO format (YYYY-MM-DD)"
                            }
                        },
                        "required": ["min_speed", "start_date", "end_date"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict | None) -> Sequence[TextContent]:
            """Handle tool execution"""
            try:
                if name == "get_current_conditions":
                    result = self.get_current_conditions()
                    
                elif name == "query_temperature_range":
                    result = self.query_temperature_range(
                        arguments["start_date"],
                        arguments["end_date"]
                    )
                    
                elif name == "query_rainfall":
                    result = self.query_rainfall(
                        arguments["start_date"],
                        arguments["end_date"]
                    )
                    
                elif name == "find_wind_events":
                    result = self.find_wind_events(
                        arguments["min_speed"],
                        arguments["start_date"],
                        arguments["end_date"]
                    )
                    
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
    
    async def run_stdio(self):
        """Run the MCP server with stdio transport"""
        self.setup_handlers()
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="weewx-mcp",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )
    
    async def run_sse(self, host: str = "127.0.0.1", port: int = 8080):
        """Run the MCP server with SSE transport"""
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route
        from starlette.responses import Response
        import uvicorn
        
        self.setup_handlers()
        
        # Create SSE transport with /messages endpoint
        sse = SseServerTransport("/messages")
        
        async def handle_sse(request):
            """Handle SSE connection requests"""
            async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send
            ) as streams:
                await self.server.run(
                    streams[0],
                    streams[1],
                    InitializationOptions(
                        server_name="weewx-mcp",
                        server_version="0.1.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={}
                        )
                    )
                )
            return Response()
        
        async def handle_messages(request):
            """Handle POST messages from client"""
            await sse.handle_post_message(
                request.scope,
                request.receive,
                request._send
            )
            return Response()
        
        # Create Starlette app with both endpoints
        app = Starlette(
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Route("/messages", endpoint=handle_messages, methods=["POST"]),
            ]
        )
        
        print(f"Starting WeeWX MCP server on http://{host}:{port}")
        print(f"SSE endpoint: http://{host}:{port}/sse")
        print(f"Messages endpoint: http://{host}:{port}/messages")
        
        # Run the server
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="WeeWX MCP Server")
    parser.add_argument(
        "--db-path",
        default=DEFAULT_DB_PATH,
        help=f"Path to WeeWX database (default: {DEFAULT_DB_PATH})"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport type: stdio (for local/SSH) or sse (for HTTP)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind SSE server to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for SSE server (default: 8080)"
    )
    
    args = parser.parse_args()
    
    server = WeeWXMCPServer(db_path=args.db_path)
    
    if args.transport == "sse":
        await server.run_sse(host=args.host, port=args.port)
    else:
        await server.run_stdio()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())