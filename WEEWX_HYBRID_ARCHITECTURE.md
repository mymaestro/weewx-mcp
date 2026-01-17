# WeeWX Hybrid Architecture: Native Skin + Claude API Integration

## Executive Summary

This document proposes an elegant hybrid approach that combines the best of both previous proposals:

1. **Native WeeWX Skin** - Lightweight, efficient dashboard with pre-generated charts (no LLM required)
2. **Claude API Integration** - Natural language query processing for intelligent weather questions

This hybrid solution provides a modern web interface with smart conversational capabilities while remaining lightweight and maintainable. Users get a responsive dashboard for browsing weather data plus an intelligent query interface for complex natural language questions.

## Why This Hybrid Approach?

### Addresses Limitations of Previous Approaches

| Approach | Strength | Limitation |
|----------|----------|-----------|
| **Native Skin Only** | Lightweight, simple | No NLP, users must know what to query |
| **Ollama + WebUI** | Conversational, local | Requires 8GB+ RAM, complex setup |
| **Hybrid (This)** | Best of both | Small API calls to Claude |

### Unique Advantages
- **Lightweight Infrastructure**: Run dashboard on Raspberry Pi
- **Intelligent Queries**: Claude processes natural language questions
- **Flexible Cost**: Use Claude API only when needed (pay-per-use)
- **Optional NLP**: Users without Claude API still get full dashboard
- **Privacy Balanced**: Data stays local, queries sent to Claude for processing
- **Simple Architecture**: No Docker, no Ollama, no GPU required
- **Rapid Development**: Leverage existing Claude API and weewx-mcp tools

### Perfect For
- Users with Claude API access (free tier available)
- Organizations wanting lightweight local dashboard + smart queries
- Developers who want to extend with Claude integrations
- Users wanting balance between simplicity and intelligence

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   User Web Browser                           │
│            (Desktop, Tablet, Mobile)                         │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP
                         │
        ┌────────────────┴────────────────┐
        │                                  │
        ▼                                  ▼
┌──────────────────┐          ┌──────────────────────────┐
│  Static Skin     │          │ Claude Query Interface   │
│  Dashboard       │          │ (Web Form)               │
│  Pre-generated   │          │                          │
│  Charts          │          │ Natural Language Input   │
└────────┬─────────┘          └──────────┬───────────────┘
         │                               │
         └───────────────┬───────────────┘
                         │
        ┌────────────────▼────────────────────┐
        │   WeeWX Service Extension           │
        │   (REST API + Claude Integration)   │
        │                                      │
        │  • Static data endpoints             │
        │  • Chart generation                  │
        │  • Claude query handler              │
        │  • MCP tool invocation               │
        └────────────────┬────────────────────┘
                         │
        ┌────────────────▼────────────────────┐
        │   Dual Data Path                    │
        │                                      │
        │   Path 1: Direct DB Query           │
        │   (for dashboard & simple API)      │
        │                                      │
        │   Path 2: Claude + MCP Tools        │
        │   (for natural language queries)    │
        └────────────────┬────────────────────┘
                         │
        ┌────────────────▼────────────────────┐
        │   WeeWX Database Access             │
        │   • Real-time data                  │
        │   • Historical archive              │
        │   • Pre-computed aggregations       │
        └─────────────────────────────────────┘
                         │
                         ▼
        ┌─────────────────────────────────────┐
        │ Claude API (Optional)                │
        │ (For NLP query processing)          │
        │ Uses weewx-mcp tool definitions     │
        └─────────────────────────────────────┘
```

## Technical Stack

### Core Components

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Dashboard UI** | HTML/CSS/JavaScript | Static interface with charts |
| **API Server** | Flask/FastAPI | REST endpoints + Claude integration |
| **MCP Tools** | Python/weewx-mcp | Weather data queries |
| **Claude Integration** | Anthropic SDK | NLP processing + tool invocation |
| **WeeWX Integration** | Native extensions | Database access + skin templates |

### Why This Stack

**WeeWX Native Skin**:
- Already built-in to WeeWX
- Efficient Cheetah template processing
- Direct data access, no external queries

**Flask/FastAPI Service Extension**:
- Lightweight HTTP framework
- Easy Claude API integration
- Minimal dependencies

**Claude API** (Optional):
- No infrastructure to manage
- Excellent natural language understanding
- Tool use/function calling support
- Free tier available ($0.03 per 1M input tokens)

## Implementation Architecture

### Part 1: WeeWX Skin (Unchanged)

Reuse the standard WeeWX skin from the native approach:
- `index.html.tmpl` - Main dashboard
- `history.html.tmpl` - Historical data
- Pre-generated charts
- Responsive CSS

### Part 2: Service Extension with Claude Integration

```
extensions/weather-api/
├── bin/user/
│   ├── __init__.py
│   ├── weather_api.py              # Main service + Flask app
│   ├── api_handlers.py             # Standard API endpoints
│   ├── claude_integration.py        # Claude API wrapper
│   └── tool_schemas.py             # MCP tool definitions for Claude
├── install.py
└── README.md
```

#### API Handler: `api_handlers.py`
```python
"""Standard REST API endpoints for dashboard and programmatic use"""

from flask import jsonify, request
import sqlite3

def current_conditions():
    """GET /api/current - Current weather conditions"""
    db = get_db_connection()
    record = db.execute(
        'SELECT * FROM archive ORDER BY dateTime DESC LIMIT 1'
    ).fetchone()
    
    return jsonify({
        'timestamp': record['dateTime'],
        'temperature': record['outTemp'],
        'humidity': record['outHumidity'],
        'pressure': record['barometer'],
        'wind_speed': record['windSpeed'],
        'wind_dir': record['windDir'],
        'rain_rate': record['rainRate']
    })

def temperature_range():
    """GET /api/temperature?start=2025-01-01&end=2025-01-31"""
    start = request.args.get('start')
    end = request.args.get('end')
    
    db = get_db_connection()
    stats = db.execute('''
        SELECT 
            MIN(outTemp) as min_temp,
            MAX(outTemp) as max_temp,
            AVG(outTemp) as avg_temp,
            COUNT(*) as records
        FROM archive 
        WHERE dateTime >= ? AND dateTime <= ?
    ''', (start, end)).fetchone()
    
    return jsonify(stats)

# ... more endpoints (rainfall, wind, charts, etc.)
```

#### Claude Integration: `claude_integration.py`
```python
"""Natural language query processing via Claude API"""

from anthropic import Anthropic
import json
import sqlite3

class WeatherClaude:
    def __init__(self, api_key):
        self.client = Anthropic()
        self.api_key = api_key
        self.tools = self.define_tools()
    
    def define_tools(self):
        """Define MCP tools for Claude"""
        return [
            {
                "name": "get_current_conditions",
                "description": "Get the most recent weather reading",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "query_temperature_range",
                "description": "Get temperature statistics for a date range",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "ISO format (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "ISO format (YYYY-MM-DD)"}
                    },
                    "required": ["start_date", "end_date"]
                }
            },
            {
                "name": "query_rainfall",
                "description": "Get rainfall statistics for a date range",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "ISO format (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "ISO format (YYYY-MM-DD)"}
                    },
                    "required": ["start_date", "end_date"]
                }
            },
            {
                "name": "find_wind_events",
                "description": "Find wind speed events above threshold",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "min_speed": {"type": "number", "description": "Wind speed threshold"},
                        "start_date": {"type": "string", "description": "ISO format (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "ISO format (YYYY-MM-DD)"}
                    },
                    "required": ["min_speed", "start_date", "end_date"]
                }
            },
            # ... more tools
        ]
    
    def process_query(self, user_query: str) -> str:
        """Process natural language query using Claude with tool use"""
        
        messages = [
            {
                "role": "user",
                "content": f"""You are a helpful weather assistant with access to a personal 
weather station database. Answer questions about weather data using the available tools.
Always provide specific numbers with units. Be conversational but accurate.

User query: {user_query}"""
            }
        ]
        
        # Agentic loop with tool use
        while True:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                tools=self.tools,
                messages=messages
            )
            
            # If Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Find tool use blocks
                tool_calls = [block for block in response.content 
                             if block.type == "tool_use"]
                
                # Process each tool call
                tool_results = []
                for tool_call in tool_calls:
                    result = self.invoke_tool(
                        tool_call.name,
                        tool_call.input
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": json.dumps(result)
                    })
                
                # Add Claude's response and tool results to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                
            else:
                # Claude finished, extract text response
                return response.content[0].text
    
    def invoke_tool(self, tool_name: str, params: dict):
        """Invoke actual weather data tool"""
        
        db = sqlite3.connect('/var/lib/weewx/weewx.sdb')
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        if tool_name == "get_current_conditions":
            cursor.execute("""
                SELECT dateTime, outTemp, outHumidity, barometer, 
                       windSpeed, windDir, rain, rainRate
                FROM archive ORDER BY dateTime DESC LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row)
        
        elif tool_name == "query_temperature_range":
            start_ts = int(datetime.fromisoformat(params['start_date']).timestamp())
            end_ts = int(datetime.fromisoformat(params['end_date']).timestamp())
            
            cursor.execute("""
                SELECT MIN(outTemp) as min_temp, MAX(outTemp) as max_temp,
                       AVG(outTemp) as avg_temp
                FROM archive WHERE dateTime >= ? AND dateTime <= ?
            """, (start_ts, end_ts))
            
            return dict(cursor.fetchone())
        
        elif tool_name == "query_rainfall":
            start_ts = int(datetime.fromisoformat(params['start_date']).timestamp())
            end_ts = int(datetime.fromisoformat(params['end_date']).timestamp())
            
            cursor.execute("""
                SELECT SUM(rain) as total_rain, COUNT(*) as records
                FROM archive WHERE dateTime >= ? AND dateTime <= ?
            """, (start_ts, end_ts))
            
            return dict(cursor.fetchone())
        
        # ... more tools
        
        return {"error": f"Unknown tool: {tool_name}"}
```

#### Main Service: `weather_api.py`
```python
"""WeeWX Service Extension with REST API and Claude Integration"""

from flask import Flask, jsonify, request
from weewx.engine import StdEngine
from claude_integration import WeatherClaude
import os

class WeatherAPIService(StdEngine):
    def __init__(self, engine, config_dict):
        super().__init__(engine, config_dict)
        
        self.app = Flask(__name__)
        self.engine = engine
        
        # Initialize Claude integration if API key provided
        claude_key = os.getenv('CLAUDE_API_KEY')
        self.claude = WeatherClaude(claude_key) if claude_key else None
        
        self.setup_routes()
        self.start_flask_thread()
    
    def setup_routes(self):
        @self.app.route('/api/current', methods=['GET'])
        def current_conditions():
            """Standard API endpoint"""
            from api_handlers import current_conditions
            return current_conditions()
        
        @self.app.route('/api/temperature', methods=['GET'])
        def temperature_range():
            """Standard API endpoint"""
            from api_handlers import temperature_range
            return temperature_range()
        
        @self.app.route('/api/query', methods=['POST'])
        def natural_language_query():
            """Natural language query endpoint - requires Claude API"""
            
            if not self.claude:
                return jsonify({
                    "error": "Claude API not configured. Set CLAUDE_API_KEY environment variable."
                }), 400
            
            data = request.get_json()
            query = data.get('query')
            
            if not query:
                return jsonify({"error": "Missing 'query' field"}), 400
            
            try:
                response = self.claude.process_query(query)
                return jsonify({
                    "query": query,
                    "response": response,
                    "source": "Claude API with WeeWX tools"
                })
            except Exception as e:
                return jsonify({
                    "error": str(e)
                }), 500
```

### Part 3: Frontend Integration

#### Dashboard Query Widget (HTML in skin template)

```html
<!-- In index.html.tmpl or separate query.html.tmpl -->
<div class="query-panel">
    <h2>Ask About Your Weather</h2>
    <form id="queryForm">
        <textarea 
            id="queryInput" 
            placeholder="Examples: What was the hottest day last week? When did it last rain? How humid has it been?"
            rows="3"></textarea>
        <button type="submit">Ask</button>
    </form>
    
    <div id="queryResult" class="hidden">
        <h3>Response</h3>
        <p id="resultText"></p>
    </div>
</div>

<script>
document.getElementById('queryForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const query = document.getElementById('queryInput').value;
    
    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        
        const data = await response.json();
        
        if (data.error) {
            document.getElementById('resultText').textContent = 
                'Error: ' + data.error;
        } else {
            document.getElementById('resultText').textContent = 
                data.response;
        }
        
        document.getElementById('queryResult').classList.remove('hidden');
    } catch (error) {
        document.getElementById('resultText').textContent = 
            'Connection error: ' + error.message;
    }
});
</script>
```

## Data Flow Examples

### Scenario 1: Browse Dashboard (No API Used)
```
1. User opens browser to http://myweather.local/
2. Skin renders static HTML from Cheetah templates
3. Pre-generated charts display
4. No API calls, no Claude involved
5. Instant load, works offline if needed
```

### Scenario 2: Standard API Query (Direct Database)
```
1. User submits date range form
2. JavaScript: GET /api/temperature?start=2025-01-01&end=2025-01-31
3. Flask handler queries WeeWX database
4. Returns JSON: {min: 32, max: 78, avg: 55}
5. JavaScript renders response
6. No Claude API call
```

### Scenario 3: Natural Language Query (Claude)
```
1. User types: "What was the highest temperature this month?"
2. JavaScript: POST /api/query with query JSON
3. Flask passes to Claude with tool definitions
4. Claude sees available tools, determines it needs temperature data
5. Claude calls: query_temperature_range("2025-01-01", "2025-01-31")
6. Flask invokes actual WeeWX query
7. Claude receives result and formats response
8. Returns: "The highest temperature this month was 78°F on January 15th"
9. JavaScript displays response
```

## Implementation Plan

### Phase 1: Base Skin + Simple API (1 week)
- [ ] Create WeeWX skin with responsive dashboard
- [ ] Implement basic REST API endpoints
- [ ] Add pre-generated chart support
- [ ] Test without Claude (works standalone)

### Phase 2: Claude Integration (1 week)
- [ ] Add Anthropic SDK dependency
- [ ] Implement tool schema definitions
- [ ] Create `/api/query` endpoint
- [ ] Add query form to dashboard
- [ ] Implement agentic loop with tool use

### Phase 3: Refinement (1 week)
- [ ] Add query history (stored in browser)
- [ ] Implement response caching
- [ ] Add error handling and retry logic
- [ ] Create example queries
- [ ] Write documentation

### Phase 4: Deployment (1 week)
- [ ] Package for distribution
- [ ] Create installation guide
- [ ] Write configuration docs
- [ ] Add troubleshooting guide
- [ ] Create example integrations

## Cost Analysis

### Claude API Usage (Typical)
- **Small user** (10 queries/day): ~$0.90/month
- **Medium user** (50 queries/day): ~$4.50/month  
- **Heavy user** (200 queries/day): ~$18/month

Reference: 1M input tokens = $0.03, output roughly 2-3x cheaper

### Infrastructure Cost
- **Hosting**: Free (runs on your machine)
- **Database**: Free (local WeeWX)
- **API**: Optional (only pay for queries you make)

## API Endpoints

### Standard Endpoints (Always Available)
- `GET /api/current` - Current conditions
- `GET /api/temperature` - Temperature range
- `GET /api/rainfall` - Rainfall statistics
- `GET /api/wind` - Wind data
- `GET /api/humidity` - Humidity statistics
- `GET /api/chart` - Generate charts on-demand

### Claude-Powered Endpoints (Optional)
- `POST /api/query` - Natural language query (requires Claude API key)

### Example Natural Language Queries

```javascript
// "What was the hottest day last week?"
// "How much rain have we had this month?"
// "Has humidity been high lately?"
// "Show me wind speeds from last March"
// "What's the trend in temperature?"
// "When was the last day without rain?"
// "Compare this month to last month"
```

## Configuration

### Minimal Setup (Dashboard Only)
```bash
# No API key needed
# Skin works standalone
# Standard API endpoints functional
```

### With Claude (Add NLP)
```bash
# Set environment variable
export CLAUDE_API_KEY="sk-ant-..."

# Restart WeeWX
sudo systemctl restart weewx

# Query endpoint now available at /api/query
```

## Advantages Over Alternatives

### vs. Native Skin Only
- ✅ Intelligent natural language understanding
- ✅ No pattern matching required
- ✅ Conversational interactions
- ❌ Requires Claude API key

### vs. Ollama + WebUI
- ✅ Minimal hardware requirement
- ✅ No setup complexity (no Docker)
- ✅ Faster responses (Claude > local Llama)
- ✅ Better NLP quality
- ✅ Optional (works without Claude)
- ❌ Requires API key
- ❌ Small per-query cost

### vs. Current MCP + Claude
- ✅ Web interface included
- ✅ Dashboard with pre-generated charts
- ✅ Works offline for basic browsing
- ✅ Simpler installation
- ❌ Need to learn MCP protocol

## Comparison: All Four Approaches

| Feature | MCP Only | Ollama+WebUI | Native Skin | Hybrid |
|---------|----------|---|---|---|
| **Interface** | Claude Desktop | Web UI | Web UI | Web UI |
| **NLP Quality** | Excellent | Good | None | Excellent |
| **Hardware** | Minimal | 8GB+ RAM | Minimal | Minimal |
| **Setup Time** | 15 min | 45 min | 20 min | 25 min |
| **Cost** | Claude API | Free | Free | $0-20/mo |
| **Offline Mode** | ❌ | ✓ (dashboard) | ✓ (full) | ✓ (dashboard) |
| **Privacy** | ✓ | ✓ | ✓ | ✓ (local data) |
| **Extensibility** | High | High | Medium | High |
| **Ideal For** | Claude users | Power users | Everyone | Balance |

## Example Queries & Responses

### Query 1: Current Conditions
**User**: "What's the weather like right now?"
**Response**: "Your weather station shows 68°F with 52% humidity, calm winds at 2 mph, and a barometric pressure of 30.15 inches. It's a pleasant day with clear skies."

### Query 2: Historical Analysis  
**User**: "How many days did it rain in December?"
**Response**: "In December, you had 8 rainy days with a total of 3.14 inches of rainfall. The heaviest rain was on December 12th with 0.87 inches."

### Query 3: Trend Analysis
**User**: "Has it been getting colder?"
**Response**: "Yes, there's a clear cooling trend. The average temperature in early January was 45°F, but by late January it's down to 38°F—about 7 degrees colder overall."

## Future Enhancements

- [ ] Query history and saved queries
- [ ] Response caching to reduce API calls
- [ ] Support for other LLM providers (OpenAI, etc.)
- [ ] Voice input/output
- [ ] Scheduled alerts based on natural language
- [ ] Integration with forecast APIs
- [ ] Multi-language support
- [ ] Mobile app with same interface

## Conclusion

This hybrid approach delivers:

1. **Best of Both Worlds**: Lightweight dashboard + intelligent NLP
2. **Flexible Cost**: Pay only for Claude queries you make
3. **Simple Architecture**: No complex orchestration needed
4. **Great UX**: Modern web interface + conversational AI
5. **Easy Maintenance**: Leverage proven technologies
6. **Optional**: Works great without Claude if you prefer

Perfect for users who want a modern weather dashboard with the option to add conversational intelligence through Claude API—without the infrastructure complexity of Ollama or the need to understand MCP.

---

**Document Version**: 1.0  
**Last Updated**: January 17, 2026  
**Status**: Proposed Architecture
