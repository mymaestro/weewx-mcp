# weewx-mcp

An MCP (Model Context Protocol) server that enables natural language queries to your WeeWX personal weather station data.

## Overview

This MCP server provides a bridge between AI language models and WeeWX weather stations, allowing you to query your personal weather data using natural language. Ask questions like "What was the hottest day last week?" or "When did we have high wind speeds?" and get instant answers from your weather station database.

## Features

- **Current Conditions**: Get the most recent weather readings from your station
- **Temperature Analytics**: Query min/max/average temperatures over date ranges
- **Rainfall Analysis**: Get total rainfall and rain rate statistics
- **Wind Events**: Find instances where wind speed exceeded a threshold
- **Flexible Transport**: Works with both stdio (local/SSH) and SSE (HTTP) transports

## Installation

### Prerequisites

- Python 3.8+
- WeeWX installed and running with a SQLite database
- pip package manager

### System Dependencies (Linux)

On Debian/Ubuntu (including ARM devices), install build tools and headers needed for packages like `cffi` and `cryptography`:

```bash
sudo apt update
sudo apt install -y build-essential libffi-dev python3-dev libssl-dev pkg-config
```

### Setup

1. Clone this repository:
```bash
git clone https://github.com/mymaestro/weewx-mcp.git
cd weewx-mcp
```

2. Create a virtual environment and install dependencies (recommended):
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip wheel setuptools
pip install mcp
```

For SSE transport support, also install inside the venv:
```bash
pip install "starlette>=0.20.0" "uvicorn>=0.20.0"
```

### Externally Managed Python (Debian/Ubuntu)

If you see `error: externally-managed-environment` when using system `pip`, use one of:

- Virtual environment (above): Isolated per-project installs.
- pipx (for global CLI tool installs):
```bash
sudo apt update
sudo apt install -y pipx
pipx ensurepath
pipx install mcp
```

Avoid system-wide `pip install` on Debian/Ubuntu; prefer venv or pipx.

## Usage

### Via Stdio (Local/SSH)

This is the default mode, suitable for local use or SSH connections:

```bash
python src/weewx_mcp_server.py
```

By default, it looks for WeeWX database at `/var/lib/weewx/weewx.sdb`. To specify a different path:

```bash
python src/weewx_mcp_server.py --db-path /path/to/weewx.sdb
```

### Via SSE (HTTP)

To run the server as an HTTP service:

```bash
python src/weewx_mcp_server.py --transport sse --host 127.0.0.1 --port 8080
```

The SSE transport exposes two endpoints:
- **SSE endpoint** (`/sse`): Client connects here via GET for the event stream
- **Messages endpoint** (`/messages/`): For posting messages back to the server

Connect your MCP client to `http://127.0.0.1:8080/sse` (or use `0.0.0.0` for remote access).

## Available Tools

### get_current_conditions
Returns the most recent weather reading including temperature, humidity, pressure, wind, and rainfall data.

### query_temperature_range
Get temperature statistics (min, max, average) for a specified date range.

**Parameters:**
- `start_date`: ISO format (YYYY-MM-DD)
- `end_date`: ISO format (YYYY-MM-DD)

### query_rainfall
Get total rainfall and statistics for a date range.

**Parameters:**
- `start_date`: ISO format (YYYY-MM-DD)
- `end_date`: ISO format (YYYY-MM-DD)

### find_wind_events
Find instances where wind speed exceeded a threshold within a date range.

**Parameters:**
- `min_speed`: Wind speed threshold (units depend on your WeeWX configuration)
- `start_date`: ISO format (YYYY-MM-DD)
- `end_date`: ISO format (YYYY-MM-DD)

### query_humidity_range
Get humidity statistics (min, max, average) for a specified date range.

**Parameters:**
- `start_date`: ISO format (YYYY-MM-DD)
- `end_date`: ISO format (YYYY-MM-DD)

**Returns:** min/max/avg humidity and timestamps of peak/low values.

### query_daily_rainfall
Get total rainfall aggregated per day over a date range.

**Parameters:**
- `start_date`: ISO format (YYYY-MM-DD)
- `end_date`: ISO format (YYYY-MM-DD)

**Returns:** overall total plus a list of `{date, total_rainfall}`.

### query_pressure_trend
Compute barometric pressure change and rate over a date range.

**Parameters:**
- `start_date`: ISO format (YYYY-MM-DD)
- `end_date`: ISO format (YYYY-MM-DD)

**Returns:** start/end pressure, absolute change, hours spanned, and rate per hour.

## Configuration

The server reads from your WeeWX SQLite database. Ensure:

1. WeeWX is running and logging data
2. You have read access to the WeeWX database file
3. The database path is correctly specified

## Integration with Claude/LLMs

This MCP server integrates with Claude and other language models that support MCP. Configuration varies by platform:

### Claude Code

Add the server using the CLI:

```bash
claude mcp add --transport sse weewx http://127.0.0.1:8080/sse
```

For remote servers, replace `127.0.0.1` with your server's IP address.

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "weewx": {
      "command": "python",
      "args": ["/path/to/weewx-mcp/src/weewx_mcp_server.py", "--db-path", "/var/lib/weewx/weewx.sdb"],
      "env": {}
    }
  }
}
```

### Other Clients

- **Claude API**: Use with MCP client configuration
- **Other LLMs**: Follow their MCP integration documentation

## Database

The server queries the standard WeeWX SQLite database structure. The main table used is:
- `archive`: Contains all historical weather readings

Fields queried:
- `dateTime`: Timestamp of reading
- `outTemp`: Outside temperature
- `outHumidity`: Outside humidity
- `barometer`: Barometric pressure
- `windSpeed`: Wind speed
- `windDir`: Wind direction
- `windGust`: Wind gust speed
- `rain`: Rainfall amount
- `rainRate`: Rainfall rate
- `dewpoint`: Dew point temperature

## Error Handling

The server includes error handling for:
- Database connection failures
- Invalid date formats
- Missing data
- Unknown tools

Errors are returned as JSON responses indicating the issue.

## Development

### Adding New Queries

To add new weather queries:

1. Implement a new method in the `WeeWXMCPServer` class
2. Add a corresponding tool definition in `setup_handlers()`
3. Add the tool execution case in `handle_call_tool()`

Example:

```python
def query_humidity_range(self, start_date: str, end_date: str) -> dict:
    """Get humidity statistics for a date range"""
    # Your implementation here
    pass
```

## Troubleshooting
### "ffi.h: No such file or directory" (cffi build failure)

This indicates missing `libffi` development headers. Install system packages, then retry inside your virtual environment:

```bash
sudo apt update
sudo apt install -y libffi-dev build-essential python3-dev pkg-config
source .venv/bin/activate
pip install --upgrade pip
pip install mcp
```

On some ARM architectures or newer Python versions, wheels may be unavailable and source builds are required — the packages above resolve that.

### Database Not Found
- Verify WeeWX is installed and running
- Check the database path with `--db-path` parameter
- Ensure your user has read permissions on the database file

### No Data Returned
- Ensure WeeWX has been collecting data
- Check the date range you're querying
- Verify the database isn't locked

### Import Errors
- Activate your virtual environment, then install MCP with `pip install mcp`
- For SSE, also install `pip install "starlette>=0.20.0" "uvicorn>=0.20.0"`

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

- Built on the [Model Context Protocol](https://modelcontextprotocol.io/)
- Designed for [WeeWX](https://weewx.com/) weather station software
