# WeeWX + Ollama + Open WebUI Integration Architecture

## Executive Summary

This document proposes a parallel solution that enhances the weewx-mcp project by integrating with Ollama and Open WebUI to provide a full-fledged, user-friendly chat interface for querying personal weather station data. The solution maintains backward compatibility with the existing MCP implementation while adding a modern, locally-hosted web UI for weather intelligence queries.

## Current State

### weewx-mcp Overview
- **Purpose**: MCP (Model Context Protocol) server that bridges AI language models with WeeWX weather station databases
- **Core Functionality**: 
  - Query current weather conditions
  - Retrieve temperature statistics over date ranges
  - Analyze rainfall patterns
  - Identify wind events
  - Natural language processing of weather queries
- **Transport**: Stdio (local/SSH) and SSE (HTTP) support
- **Dependencies**: MCP SDK, SQLite, optional Starlette/Uvicorn for HTTP transport

### Limitations of Current Approach
- Requires Claude Desktop or custom MCP client integration
- No standalone web interface for non-technical users
- Limited to environments supporting MCP protocol
- Requires separate configuration for different client applications

## Proposed Enhancement

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Open WebUI                                 │
│          User-friendly web chat interface                    │
│     (Handles conversation UI and history)                    │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/WebSocket
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Ollama                                     │
│            Local LLM Runtime & Inference Engine              │
│    (Runs open-source models: Mistral, Llama, etc.)          │
│    (Manages tool/function calling orchestration)             │
└────────────────────────┬────────────────────────────────────┘
                         │ Tool Invocation API
                         │
┌────────────────────────▼────────────────────────────────────┐
│              weewx-mcp Server (Enhanced)                     │
│                                                               │
│  • HTTP REST API endpoint                                    │
│  • Function calling interface for Ollama                     │
│  • Tools:                                                     │
│    - get_current_conditions()                                │
│    - query_temperature_range()                               │
│    - get_rainfall_stats()                                    │
│    - find_wind_events()                                      │
│    - get_humidity_trends()                                   │
│  • Custom weather analysis prompts                           │
│  • Response formatting and context management                │
└────────────────────────┬────────────────────────────────────┘
                         │ SQLite Query
                         │
┌────────────────────────▼────────────────────────────────────┐
│          WeeWX Database (weewx.sdb)                          │
│     Personal weather station data and archives               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Example

1. **User Input**: "What was the hottest day last week?"
2. **Open WebUI**: Sends message to Ollama
3. **Ollama**: Determines it needs weather data, evaluates available tools
4. **Tool Selection**: Decides to call `query_temperature_range()` with last 7 days
5. **weewx-mcp**: Receives request, queries WeeWX database
6. **Database**: Returns historical temperature data
7. **weewx-mcp**: Formats response with timestamp, temperature, and context
8. **Ollama**: Receives tool result, synthesizes natural language response
9. **Open WebUI**: Displays answer to user with full context and confidence

## Technical Stack

### Components

| Component | Role | Technology | Deployment |
|-----------|------|-----------|------------|
| **Open WebUI** | User Interface | Web UI (React-based) | Docker container |
| **Ollama** | LLM Runtime | Local inference engine | Docker/native binary |
| **weewx-mcp** | Weather Data Service | Python (FastAPI/Starlette) | Docker/standalone |
| **WeeWX Database** | Data Storage | SQLite | Host filesystem |

### Technology Choices

**Ollama**:
- Privacy-first: Runs entirely locally
- No API costs
- Support for multiple model architectures
- Tool-use/function-calling capabilities
- Fast inference on consumer hardware

**Open WebUI**:
- Beautiful, intuitive chat interface
- Conversation history management
- Multiple model support via Ollama
- Customizable system prompts
- Open source with active community

**weewx-mcp Enhancement**:
- Leverage existing MCP tools
- Add HTTP API layer (use existing Starlette optional dependency)
- Implement function calling schema compatible with Ollama
- Minimal changes to core weather query logic

## Implementation Plan

### Phase 1: API Layer Enhancement (1-2 weeks)

#### 1.1 Create HTTP API Server
- Wrap existing weewx-mcp tools in FastAPI/Starlette endpoints
- Create unified `/tools` endpoint describing available functions
- Implement `/invoke` endpoint for tool execution
- Add request validation and error handling

**Files to Create**:
- `src/weewx_api_server.py` - HTTP API wrapper
- `src/tools_schema.py` - Ollama-compatible function schemas
- `docker/api.dockerfile` - Container configuration

#### 1.2 Tool Schemas for Ollama
Define each MCP tool in Ollama's function format:
```
{
  "name": "query_temperature_range",
  "description": "Get min/max/average temperatures for a date range",
  "parameters": {
    "type": "object",
    "properties": {
      "start_date": {"type": "string", "description": "ISO format start date"},
      "end_date": {"type": "string", "description": "ISO format end date"}
    },
    "required": ["start_date", "end_date"]
  }
}
```

#### 1.3 Testing & Validation
- Unit tests for HTTP endpoints
- Integration tests with mock WeeWX database
- Schema validation against Ollama expectations

### Phase 2: Ollama Integration (1 week)

#### 2.1 Configure Ollama Function Calling
- Define weewx-mcp tools in Ollama's function format
- Create custom system prompts for weather intelligence
- Configure model to use weewx-mcp as primary tool provider

#### 2.2 Weather-Specific Prompts
Craft system prompts that:
- Guide the model to ask clarifying questions
- Suggest relevant analysis based on user context
- Format responses with charts/tables when appropriate
- Include weather domain knowledge

Example:
```
You are a personal weather assistant with access to detailed weather station data.
When users ask about weather:
1. Ask about the timeframe if not specified
2. Provide specific numbers with units
3. Suggest comparative analysis (vs. historical averages)
4. Explain weather patterns and their implications
```

### Phase 3: Docker Orchestration (1 week)

#### 3.1 Docker Compose Setup
Create `docker-compose.yml` that orchestrates:
- Ollama container with model management
- Open WebUI container with Ollama integration
- weewx-mcp API server container
- Volume mounts for WeeWX database

#### 3.2 Environment Configuration
- `.env` file for customizable settings
- Database path configuration
- Model selection (Mistral recommended for speed/quality balance)
- Port mappings and networking

#### 3.3 Deployment Documentation
- Quick-start guide
- Configuration options
- Troubleshooting guide
- Hardware requirements

### Phase 4: Polish & Documentation (1 week)

#### 4.1 User Documentation
- Getting started guide
- Example queries and responses
- Customization instructions
- Troubleshooting

#### 4.2 Developer Documentation
- Architecture decisions
- Adding new weather analysis functions
- Extending tool schemas
- Contributing guidelines

## Key Features & Benefits

### User-Facing Benefits
- **Accessible Interface**: No need to understand MCP protocol
- **Natural Conversation**: Ask questions in natural language
- **Conversation History**: Remember context across queries
- **No Internet Required**: Completely private, runs locally
- **Rich Responses**: Formatted answers with relevant context
- **Instant Answers**: Local inference = fast response times

### Technical Benefits
- **Backward Compatible**: Existing MCP functionality unchanged
- **Modular Design**: Easy to add new weather analysis functions
- **Scalable Architecture**: Can add multiple LLM models
- **Container-Ready**: Docker deployment for any environment
- **Open Source Stack**: No vendor lock-in
- **Cost Effective**: No API charges or subscriptions

### Operational Benefits
- **Privacy**: Weather data never leaves the network
- **Control**: Full control over prompts, models, and data
- **Customization**: Adapt prompts to regional weather patterns
- **Reliability**: No dependency on external services
- **Maintenance**: Automated container updates, simple backup strategy

## Hardware Requirements

### Minimum (Functional)
- **CPU**: 2+ cores
- **RAM**: 8 GB (4 GB minimum for small models)
- **Storage**: 20 GB free (for model files)
- **Network**: Local network connectivity

### Recommended
- **CPU**: 4+ cores (8+ for faster inference)
- **RAM**: 16 GB (enables larger models like Llama 2 13B)
- **Storage**: 50+ GB free (multiple model support)
- **Network**: Wired for stability

### Optimal
- **CPU**: 8+ cores with AVX2 support
- **RAM**: 32+ GB
- **Storage**: 100+ GB with NVMe SSD
- **GPU**: NVIDIA/Apple Silicon for 10-30x faster inference

## Getting Started

### Prerequisites
- Docker and Docker Compose installed
- WeeWX installed and operational with SQLite database
- Database file accessible at `/var/lib/weewx/weewx.sdb` (or configurable)

### Quick Start (3 commands)
```bash
git clone https://github.com/yourusername/weewx-mcp.git
cd weewx-mcp
docker-compose up -d
```

Then:
1. Open browser to `http://localhost:8080` (Open WebUI)
2. Select Ollama model from dropdown
3. Start asking weather questions

### Configuration
Copy `.env.example` to `.env` and customize:
```bash
# WeeWX Database
DB_PATH=/var/lib/weewx/weewx.sdb

# Ollama Settings
OLLAMA_MODEL=mistral
OLLAMA_PORT=11434

# API Server
API_PORT=8000
API_HOST=0.0.0.0

# Open WebUI
WEBUI_PORT=8080
WEBUI_OLLAMA_BASE_URL=http://ollama:11434
```

## Example Interactions

### Query 1: Current Conditions
**User**: "What's the weather like right now?"

**System Flow**:
1. Ollama calls `get_current_conditions()`
2. weewx-mcp returns latest reading
3. Model formats human-readable response

**Response**: "Your weather station shows 72°F with 65% humidity, light winds at 3 mph from the west, and a barometric pressure of 30.12 inches. Conditions are pleasant."

### Query 2: Historical Analysis
**User**: "How many days did it rain last month?"

**System Flow**:
1. Ollama determines date range (previous month)
2. Calls `get_rainfall_stats()` with calculated dates
3. Model interprets rainfall data and patterns
4. Suggests interesting correlations

**Response**: "There were 8 rainy days last month with a total of 4.32 inches of rainfall. The heaviest rain occurred on the 15th with 1.2 inches in a single day. The average daily rainfall on rainy days was 0.54 inches."

### Query 3: Trend Analysis
**User**: "Has it been getting hotter lately?"

**System Flow**:
1. Ollama recognizes trend question
2. Calls `query_temperature_range()` for last 30 days
3. Calls historical data from 30 days prior for comparison
4. Model calculates deltas and trend direction

**Response**: "Yes, it's been warming up. The average temperature over the last 30 days was 68°F compared to 62°F during the same period last month—about 6 degrees warmer overall. The trend shows consistent warming with fewer cold nights."

## Future Enhancements

### Short Term (2-3 months)
- [ ] Custom analysis functions (growing degree days, pollen counts, etc.)
- [ ] Multi-language support via Ollama models
- [ ] Mobile-responsive Open WebUI improvements
- [ ] Data export functionality (CSV, JSON)

### Medium Term (3-6 months)
- [ ] Predictive analytics integration
- [ ] Alerts and notifications system
- [ ] Integration with other weather services for comparisons
- [ ] Advanced charting and visualization
- [ ] Voice interface support

### Long Term (6+ months)
- [ ] Multi-station support
- [ ] Community forecast integration
- [ ] Machine learning for anomaly detection
- [ ] Climate pattern analysis
- [ ] Integration with smart home systems

## Comparison: Current vs. Enhanced Architecture

| Feature | Current MCP | Enhanced (Ollama + WebUI) |
|---------|-------------|--------------------------|
| **Interface** | Claude Desktop / CLI | Web browser |
| **Accessibility** | Technical users | All users |
| **Local Operation** | ✓ | ✓ |
| **Conversation History** | Limited | Full with management |
| **Deployment** | Manual | Docker-based |
| **Cost** | Free (Claude API required) | Free (fully local) |
| **Privacy** | ✓ | ✓ |
| **Setup Complexity** | Medium | Low (with Docker) |
| **Model Selection** | Fixed | Flexible |

## Alternative: WeeWX Native Skin Approach

**Note**: There's also a lightweight alternative that doesn't require Ollama. See [WEEWX_NATIVE_SKIN_ARCHITECTURE.md](WEEWX_NATIVE_SKIN_ARCHITECTURE.md) for a solution that uses WeeWX's native skin and service extension system to provide a modern web dashboard with dynamic querying—no LLM or significant hardware required.

## Conclusion

This integrated architecture provides a practical, user-friendly solution for weather data intelligence while maintaining the technical rigor of the MCP protocol. By layering Open WebUI and Ollama on top of weewx-mcp, we create a system that is:

- **Accessible** to users of any technical level
- **Powerful** with advanced natural language understanding
- **Private** with completely local operation
- **Maintainable** with clear separation of concerns
- **Extensible** for future weather analysis capabilities

The phased implementation approach allows for incremental development with testable milestones and clear deliverables.

This approach is ideal for users with adequate hardware and who want advanced natural language capabilities. For users with limited hardware or simpler requirements, the native WeeWX skin approach offers a lightweight alternative.

## References & Resources

- [WeeWX Documentation](https://weewx.com/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [Open WebUI GitHub](https://github.com/open-webui/open-webui)
- [Ollama Function Calling Docs](https://github.com/ollama/ollama/blob/main/docs/api.md)

---

**Document Version**: 1.0  
**Last Updated**: January 17, 2026  
**Status**: Proposed Architecture
