# weewx-mcp

An MCP (Model Context Protocol) server that enables natural language queries to your WeeWX personal weather station data.

## Overview

This MCP server provides a bridge between AI language models and WeeWX weather stations, allowing you to query your personal weather data using natural language. Ask questions like "What was the hottest day last week?" or "When did we have high wind speeds?" and get instant answers from your weather station database.

### 🌐 Web Interface Options

This project offers **three architectural approaches** for adding a modern web interface to your WeeWX weather station. Each is designed for different use cases, hardware capabilities, and preferences:

#### 1. [WeeWX Hybrid Architecture](WEEWX_HYBRID_ARCHITECTURE.md) ⭐ **Recommended**

**Best for: Most users wanting balance of simplicity and intelligence**

- 📱 Mobile-first responsive dashboard with pre-generated charts
- 🤖 Optional Claude API integration for natural language queries
- 💡 Lightweight (runs on Raspberry Pi)
- 💵 Pay-as-you-go ($1-20/month typical usage)
- ⚡ Fast setup (~25 minutes)
- 📊 Works offline for dashboard, online for NLP queries
- 🎯 Perfect balance: simple infrastructure + smart AI when needed

**Key Features:**
- Static dashboard with current conditions and historical charts
- Natural language query interface: "What was the hottest day last week?"
- Direct database API endpoints for programmatic access
- PWA-ready, install to mobile home screen
- Dark mode, accessibility features

**Use this if:** You want a modern dashboard that occasionally understands natural language, without heavy infrastructure.

---

#### 2. [WeeWX + Ollama + Open WebUI Integration](WEEWX_OLLAMA_OPENWEBUI_INTEGRATION.md)

**Best for: Power users with good hardware who want fully local AI**

- 🏠 100% local conversational AI (no API keys)
- 💬 Full chat interface with conversation history
- 🖥️ Requires 8GB+ RAM for Ollama models
- 🐳 Docker-based deployment
- 🔒 Complete offline capability
- 🆓 No per-query costs

**Key Features:**
- Full-featured chat interface via Open WebUI
- Multiple LLM model support (Mistral, Llama, etc.)
- Conversation context and history
- Tool/function calling for weather data access
- Weather-specific system prompts

**Use this if:** You have adequate hardware, want completely offline AI, and prefer a conversational interface.

---

#### 3. [WeeWX Native Skin + Service Extension](WEEWX_NATIVE_SKIN_ARCHITECTURE.md)

**Best for: Minimal hardware, maximum simplicity**

- 🪶 Ultra-lightweight (256MB RAM sufficient)
- 🚀 Fastest setup (~20 minutes)
- 📱 Mobile-responsive dashboard
- 🎨 Leverages WeeWX's native Cheetah templates
- 🆓 Zero ongoing costs
- ⚡ Pre-generated charts load instantly

**Key Features:**
- Clean dashboard using WeeWX skin system
- REST API for structured queries
- Custom chart generation on-demand
- No external dependencies
- Built-in unit conversions and aggregations

**Use this if:** You want a simple, fast dashboard without AI complexity, or are running on constrained hardware (Raspberry Pi, etc.).

---

### Comparison Table

| Feature | Hybrid | Ollama+WebUI | Native Skin |
|---------|--------|--------------|-------------|
| **Interface** | Web Dashboard + Query Form | Full Chat UI | Web Dashboard |
| **NLP Quality** | Excellent (Claude) | Good (Ollama) | None |
| **Hardware** | Minimal | 8GB+ RAM | Minimal (256MB) |
| **Setup Time** | 25 min | 45 min | 20 min |
| **Cost** | $1-20/month | Free | Free |
| **Offline** | Dashboard only | Full | Full |
| **Mobile-Friendly** | ✓ PWA-ready | ✓ | ✓ PWA-ready |
| **Ideal For** | Most users | Power users | Simplicity lovers |

All three approaches:
- ✅ Maintain full data privacy (data stays local)
- ✅ Integrate seamlessly with the core weewx-mcp server
- ✅ Support mobile, tablet, and desktop devices
- ✅ Offer dark mode and accessibility features
- ✅ Can coexist (run multiple approaches simultaneously)

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

### Hybrid REST API (Phase 1)

Run the lightweight REST API server for dashboard and programmatic access:

```bash
python src/weewx_hybrid_api.py --host 127.0.0.1 --port 9090
```

Key endpoints:

- `GET /api/status` - Health check, database status
- `GET /api/current` - Current conditions
- `GET /api/temperature?start=YYYY-MM-DD&end=YYYY-MM-DD`
- `GET /api/rainfall?start=YYYY-MM-DD&end=YYYY-MM-DD`
- `GET /api/wind?min_speed=10&start=YYYY-MM-DD&end=YYYY-MM-DD`
- `GET /api/humidity?start=YYYY-MM-DD&end=YYYY-MM-DD`
- `GET /api/daily-rain?start=YYYY-MM-DD&end=YYYY-MM-DD`
- `GET /api/pressure?start=YYYY-MM-DD&end=YYYY-MM-DD`

Install optional dependencies first if needed:

```bash
pip install ".[api]"
```

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

### find_longest_dry_spell
Find the longest consecutive stretch of days with zero rainfall in a date range. Uses `archive_day_rain.sum` for per-day totals.

**Parameters:**
- `start_date`: ISO format (YYYY-MM-DD)
- `end_date`: ISO format (YYYY-MM-DD)

**Returns:** number of days, start date, end date.

### find_longest_rain_streak
Find the longest consecutive stretch of days with measured rainfall in a date range. Uses `archive_day_rain.sum` for per-day totals.

**Parameters:**
- `start_date`: ISO format (YYYY-MM-DD)
- `end_date`: ISO format (YYYY-MM-DD)

**Returns:** number of days, start date, end date.

### summarize_temperature
Summarize temperature statistics aggregated by daily, weekly, or monthly buckets. Uses `archive_day_outTemp`.

**Parameters:**
- `granularity`: One of `daily`, `weekly`, `monthly`
- `start_date`: ISO format (YYYY-MM-DD)
- `end_date`: ISO format (YYYY-MM-DD)

**Returns:** Array of buckets with `min`, `max`, `avg` temperature.

### summarize_rain
Summarize rainfall aggregated by daily, weekly, or monthly buckets. Uses `archive_day_rain`.

**Parameters:**
- `granularity`: One of `daily`, `weekly`, `monthly`
- `start_date`: ISO format (YYYY-MM-DD)
- `end_date`: ISO format (YYYY-MM-DD)

**Returns:** Array of buckets with `total_rain`, `days`, `avg_daily_rain`.

### summarize_wind
Summarize wind statistics aggregated by daily, weekly, or monthly buckets. Uses `archive_day_windSpeed` and `archive_day_windGust`.

**Parameters:**
- `granularity`: One of `daily`, `weekly`, `monthly`
- `start_date`: ISO format (YYYY-MM-DD)
- `end_date`: ISO format (YYYY-MM-DD)

**Returns:** Array of buckets with `avg_wind_speed` and `max_gust`.

## Examples

### Quick Test via Python

If you have a local Python environment with the server code:

```bash
# Activate your virtual environment
source .venv/bin/activate

# Get current conditions
python -c 'from src.weewx_mcp_server import WeeWXMCPServer; s=WeeWXMCPServer(); import json; print(json.dumps(s.get_current_conditions(), indent=2))'

# Temperature range for January 2025
python -c 'from src.weewx_mcp_server import WeeWXMCPServer; s=WeeWXMCPServer(); import json; print(json.dumps(s.query_temperature_range("2025-01-01","2025-01-31"), indent=2))'

# Longest dry spell in 2025
python -c 'from src.weewx_mcp_server import WeeWXMCPServer; s=WeeWXMCPServer(); import json; print(json.dumps(s.find_longest_dry_spell("2025-01-01","2025-12-31"), indent=2))'

# Monthly temperature summary for 2025
python -c 'from src.weewx_mcp_server import WeeWXMCPServer; s=WeeWXMCPServer(); import json; print(json.dumps(s.summarize_temperature("monthly","2025-01-01","2025-12-31"), indent=2))'

# Weekly rain summary for June 2025
python -c 'from src.weewx_mcp_server import WeeWXMCPServer; s=WeeWXMCPServer(); import json; print(json.dumps(s.summarize_rain("weekly","2025-06-01","2025-06-30"), indent=2))'
```

### Testing SSE Endpoint

Start the server:

```bash
python src/weewx_mcp_server.py --transport sse --host 127.0.0.1 --port 8080
```

Test the SSE endpoint from another terminal:

```bash
# Check SSE stream is active
curl -v http://127.0.0.1:8080/sse

# Should return HTTP/1.1 200 OK and keep connection open
```

### Natural Language Queries via Claude

Once connected to Claude Code or Claude Desktop, you can ask natural language questions:

- "What's the current temperature and humidity?"
- "Show me the hottest and coldest days in January 2025"
- "What was the longest dry spell last year?"
- "Give me monthly rainfall totals for 2025"
- "Find all days when wind speed exceeded 25 mph in March"
- "Show weekly temperature trends for the summer months"

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
