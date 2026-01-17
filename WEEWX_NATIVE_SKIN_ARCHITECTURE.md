# WeeWX Native Skin + Service Extension Architecture

## Executive Summary

This document proposes a lightweight, efficient alternative to the Ollama integration by leveraging WeeWX's native skin and extension architecture. Instead of adding external dependencies like Ollama and Open WebUI, we build directly on WeeWX's proven templating engine, report generator, and image creation capabilities. This approach provides a modern web interface with dynamic querying while remaining fully integrated with WeeWX's architecture.

## Why This Approach?

### Advantages Over Ollama Solution
- **Zero Additional Hardware**: Runs within WeeWX's existing process
- **No LLM Required**: No GPU/massive RAM needed for inference
- **Native Integration**: Uses WeeWX's built-in systems (no external services)
- **Instant Setup**: No Docker orchestration, fewer dependencies
- **Proven Architecture**: Built on WeeWX's decades-old, tested design
- **Minimal Resource Footprint**: Ideal for lightweight systems, Raspberry Pi, etc.
- **Familiarity**: Leverages existing WeeWX ecosystem knowledge

### Perfect For
- Users without powerful hardware (Raspberry Pi, ARM devices)
- Organizations wanting self-contained solutions
- Users preferring transparency (no neural network black box)
- Quick deployment scenarios
- Integration with existing WeeWX ecosystems

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
┌──────────────────┐          ┌──────────────────────┐
│  Static Skin     │          │  REST API Service    │
│  HTML Interface  │          │  (Flask/FastAPI)     │
│  Pre-generated   │          │  Dynamic Queries     │
│  Charts          │          │  Custom Charts       │
└────────┬─────────┘          └──────────┬───────────┘
         │                               │
         └───────────────┬───────────────┘
                         │
        ┌────────────────▼────────────────┐
        │    WeeWX Service Extension      │
        │                                  │
        │  • REST API Endpoints            │
        │  • Chart Generation on Demand    │
        │  • Data Aggregation              │
        │  • Custom Formatters             │
        └────────────────┬────────────────┘
                         │
        ┌────────────────▼────────────────┐
        │   WeeWX Report Engine           │
        │                                  │
        │  • Skin/Template Processing     │
        │  • Report Generation            │
        │  • Chart Creation               │
        │  • Image Generators             │
        └────────────────┬────────────────┘
                         │
        ┌────────────────▼────────────────┐
        │   WeeWX Database Access         │
        │                                  │
        │  • SQLite/MySQL Tables          │
        │  • Real-time Data               │
        │  • Historical Archive           │
        │  • Aggregations (day/week/etc)  │
        └─────────────────────────────────┘
```

## Technical Stack

### Core Technologies

| Component | Purpose | Technology | Role |
|-----------|---------|-----------|------|
| **Skin** | Static interface generation | Cheetah Templates | Pre-rendered HTML/CSS with charts |
| **Service Extension** | Dynamic API | Flask or FastAPI | HTTP endpoints for real-time queries |
| **Chart Generator** | Visual data | WeeWX image generators | PNG/SVG charts (built-in or custom) |
| **Report Engine** | Scheduled generation | WeeWX reporting | Runs skin templates on interval |
| **Data Access** | Database queries | WeeWX DB API | Structured access to all weather data |

### Why Each Technology

**Cheetah Templates**:
- Already integrated into WeeWX
- Direct access to all weather variables
- Built-in unit conversions (F to C, mph to kph, etc.)
- Inheritance and composition for code reuse

**Flask/FastAPI**:
- Lightweight HTTP frameworks
- Easy to embed in WeeWX extensions
- Minimal dependencies
- Great for REST APIs

**WeeWX Image Generators**:
- Already built-in (no extra packages)
- Customizable via CSS and configuration
- Generates daily/weekly/monthly charts
- Outputs PNG for broad compatibility

## Implementation Architecture

### Part 1: WeeWX Skin (`weewx-weather-dashboard`)

A modern, responsive skin that:

```
skins/weather-dashboard/
├── skin.conf                    # Skin configuration
├── HTML/
│   ├── index.html.tmpl          # Main dashboard (Cheetah template)
│   ├── history.html.tmpl        # Historical data view
│   ├── trends.html.tmpl         # Trend analysis
│   ├── analytics.html.tmpl      # Advanced analytics
│   └── base.html.tmpl           # Template inheritance base
├── CSS/
│   ├── style.css                # Main styling
│   ├── responsive.css           # Mobile responsiveness
│   └── charts.css               # Chart styling
├── JS/
│   ├── main.js                  # JavaScript functionality
│   ├── charts.js                # Chart interactions
│   └── api-client.js            # REST API client
├── include/
│   ├── current_conditions.inc    # Reusable template components
│   ├── daily_summary.inc
│   ├── charts.inc
│   └── stats.inc
└── images/
    └── [pre-generated charts]
```

#### Cheetah Template Features

**Current Conditions Block** (`index.html.tmpl`):
```cheetah
#set $current = $latest
<div class="current-conditions">
    <h2>Current Conditions</h2>
    <div class="metric">
        <span class="label">Temperature</span>
        <span class="value">$current.outTemp.format()</span>
    </div>
    <div class="metric">
        <span class="label">Humidity</span>
        <span class="value">$current.outHumidity</span>
    </div>
    <div class="metric">
        <span class="label">Pressure</span>
        <span class="value">$current.barometer.format()</span>
    </div>
</div>
```

**Historical Data with Aggregations**:
```cheetah
#set $month_stats = $monthly_data[month]
<div class="monthly-summary">
    <h3>$month_name Summary</h3>
    <ul>
        <li>High: $month_stats.outTemp_max</li>
        <li>Low: $month_stats.outTemp_min</li>
        <li>Average: $month_stats.outTemp_avg</li>
        <li>Total Rain: $month_stats.rain_sum</li>
    </ul>
</div>
```

**Built-in Chart Inclusion**:
```cheetah
<div class="charts">
    <img src="daytemp.png" alt="Daily Temperature">
    <img src="monthtemp.png" alt="Monthly Temperature">
    <img src="yearrain.png" alt="Yearly Rainfall">
</div>
```

**Unit Conversions** (automatic via skin.conf):
```cheetah
## User configured for Celsius, this auto-converts:
<span class="temperature">$current.outTemp.format()</span>
## Displays: "22.5°C" (automatically converted from Fahrenheit)
```

### Part 2: WeeWX Service Extension (`weewx-weather-api`)

A Python service extension providing REST API endpoints:

```
extensions/weather-api/
├── bin/
│   └── user/
│       ├── __init__.py
│       ├── weather_api.py         # Main service extension
│       └── api_handlers.py         # Endpoint handlers
├── install.py                      # Installation script
└── README.md
```

#### Service Extension Features

**Flask-based API Server** (`weather_api.py`):
```python
from flask import Flask, jsonify, request
from weewx.engine import StdEngine

class WeatherAPIService(StdEngine):
    """WeeWX Service Extension providing REST API"""
    
    def __init__(self, engine, config_dict):
        super().__init__(engine, config_dict)
        self.app = Flask(__name__)
        self.setup_routes()
        self.start_flask_thread()
    
    def setup_routes(self):
        @self.app.route('/api/current', methods=['GET'])
        def current_conditions():
            """Get current weather conditions"""
            record = self.engine.db.getLatestRecord()
            return jsonify({
                'timestamp': record['dateTime'],
                'temperature': record['outTemp'],
                'humidity': record['outHumidity'],
                'pressure': record['barometer'],
                'wind_speed': record['windSpeed'],
                'wind_dir': record['windDir'],
                'rain_rate': record['rainRate']
            })
        
        @self.app.route('/api/temperature', methods=['GET'])
        def temperature_range():
            """Get temperature stats for date range"""
            start = request.args.get('start')
            end = request.args.get('end')
            
            stats = self.engine.db.getAggregates(
                start_date=start,
                end_date=end,
                field='outTemp'
            )
            return jsonify(stats)
        
        @self.app.route('/api/chart', methods=['GET'])
        def generate_chart():
            """Generate custom chart on-demand"""
            chart_type = request.args.get('type')  # 'temp', 'rain', 'wind'
            days = request.args.get('days', 7)
            
            chart_path = self.generate_custom_chart(
                chart_type=chart_type,
                days=int(days)
            )
            return send_file(chart_path, mimetype='image/png')
```

**API Endpoints**:

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/api/current` | GET | Current conditions | JSON with latest readings |
| `/api/temperature` | GET | Temperature range stats | Min/max/avg with timestamps |
| `/api/rainfall` | GET | Rainfall analysis | Daily totals, trends |
| `/api/wind` | GET | Wind statistics | Speed/gust/direction data |
| `/api/humidity` | GET | Humidity data | Min/max/avg humidity |
| `/api/chart` | GET | Generate chart on-demand | PNG image of custom chart |
| `/api/history` | GET | Historical data | Full data dump for range |
| `/api/aggregates` | GET | Pre-computed aggregates | Day/week/month/year stats |

#### Dynamic Chart Generation

**On-Demand Chart Creation**:
```python
def generate_custom_chart(self, chart_type, days):
    """Generate custom chart for specified period"""
    
    from PIL import Image, ImageDraw
    import datetime
    
    # Query data for period
    end_ts = time.time()
    start_ts = end_ts - (days * 86400)
    
    records = self.engine.db.getRecords(start_ts, end_ts)
    
    # Create chart (using PIL or similar)
    img = Image.new('RGB', (800, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    # Plot data
    for record in records:
        if chart_type == 'temp':
            # Plot temperature line
            x, y = self.scale_point(record, img.width, img.height)
            draw.point((x, y), fill='red')
    
    # Save and return
    img.save('/tmp/custom_chart.png')
    return '/tmp/custom_chart.png'
```

## Data Flow Examples

### Scenario 1: User Views Dashboard

```
1. User opens browser to http://myweather.local/
2. Web server serves index.html from skin
3. Cheetah template processes:
   - Accesses $latest record from WeeWX database
   - Accesses $monthly_data aggregations
   - Includes pre-generated chart images
   - Applies user-configured unit conversions
4. HTML/CSS/JS renders in browser
5. JavaScript makes AJAX calls to REST API for interactivity
6. CSS Media Queries adapt for mobile/tablet
```

### Scenario 2: User Queries Temperature Range

```
1. User enters date range in dashboard form
2. JavaScript sends: GET /api/temperature?start=2025-01-01&end=2025-01-31
3. Service Extension receives request
4. Queries WeeWX database for temperature records
5. Calculates aggregates (min, max, avg)
6. Returns JSON:
   {
     "min": 32.1,
     "max": 78.5,
     "avg": 55.3,
     "min_timestamp": "2025-01-15T06:23:00Z",
     "max_timestamp": "2025-01-28T14:45:00Z"
   }
7. JavaScript renders response in UI
```

### Scenario 3: User Requests Custom Chart

```
1. User selects "7-day Temperature" chart type
2. JavaScript sends: GET /api/chart?type=temp&days=7
3. Service Extension:
   - Queries last 7 days of temperature data
   - Generates PNG chart using PIL/Matplotlib
   - Returns image to browser
4. Browser displays chart inline
5. User can click to download or share
```

## Implementation Plan

### Phase 1: Skin Development (1-2 weeks)

#### 1.1 Create Skin Structure
```bash
# Create skin directory
mkdir -p ~/weewx/skins/weather-dashboard/{html,css,js,include,images}

# Create base configuration
touch ~/weewx/skins/weather-dashboard/skin.conf
```

#### 1.2 Develop Templates
- `index.html.tmpl`: Main dashboard with current conditions
- `history.html.tmpl`: Historical data browser
- `trends.html.tmpl`: Trend analysis view
- `base.html.tmpl`: Template base for inheritance

#### 1.3 Create Responsive CSS
- **Mobile-first design approach**
- **Touch-optimized interactions** (44px minimum touch targets)
- **Responsive grid layout** (stacks on mobile, 2-col tablet, 3-col desktop)
- **Dark/light theme support** with `prefers-color-scheme`
- **Accessible color scheme** with high contrast support
- **Viewport meta tags** for proper mobile scaling
- **Swipe-friendly charts** with horizontal scroll and momentum
- **Progressive enhancement** - works without JavaScript

**Mobile-First CSS Example**:
```css
/* Base mobile styles */
body {
    font-size: 16px; /* Prevents zoom on iOS input focus */
    margin: 0;
    padding: 0;
}

.container {
    width: 100%;
    padding: 16px;
}

/* Touch-friendly buttons */
button, a.button {
    min-height: 44px; /* iOS HIG minimum */
    min-width: 44px;
    padding: 12px 24px;
    font-size: 16px;
}

/* Responsive grid */
.metrics-grid {
    display: grid;
    grid-template-columns: 1fr; /* Mobile: single column */
    gap: 16px;
}

/* Tablet: 2 columns */
@media (min-width: 640px) {
    .container {
        padding: 24px;
        max-width: 640px;
        margin: 0 auto;
    }
    .metrics-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Desktop: 3 columns */
@media (min-width: 1024px) {
    .container {
        max-width: 1024px;
    }
    .metrics-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
    body {
        background: #1f2937;
        color: #f9fafb;
    }
}
```

#### 1.4 Build Interactive JavaScript
- Form submission for date range queries
- API client for REST calls
- Chart zooming/interactivity
- Theme switching
- Touch gesture support
- Progressive Web App (PWA) service worker
- Loading indicators and smooth scrolling

**Mobile-Optimized JavaScript**:
```javascript
// Smooth scroll to element (mobile-friendly)
function smoothScrollTo(element) {
    element.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'nearest' 
    });
}

// Touch-friendly form handling
document.getElementById('queryForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Provide immediate feedback
    const button = e.target.querySelector('button');
    button.disabled = true;
    button.textContent = 'Loading...';
    
    // ... API call ...
    
    // Scroll result into view on mobile
    smoothScrollTo(document.getElementById('result'));
    
    button.disabled = false;
    button.textContent = 'Submit';
});

// PWA Service Worker Registration
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').then(registration => {
        console.log('PWA ready for offline use');
    });
}
```

### Phase 2: Service Extension (1 week)

#### 2.1 Create Extension Structure
```bash
# Create extension directory
mkdir -p ~/weewx/extensions/weather-api/bin/user
```

#### 2.2 Implement REST API
- `/api/current` endpoint
- `/api/temperature` endpoint
- `/api/rainfall` endpoint
- `/api/chart` endpoint
- Error handling and validation

#### 2.3 Add Chart Generation
- Use WeeWX's image generators or PIL
- Support multiple chart types
- Implement caching to avoid regenerating

#### 2.4 Integration Testing
- Test API endpoints with curl
- Verify data accuracy against WeeWX database
- Check chart generation quality

### Phase 3: Configuration & Documentation (1 week)

#### 3.1 Create Configuration Templates
- `skin.conf`: Skin-specific settings
- `weewx.conf`: Service extension registration
- `.env.example`: User-customizable variables

#### 3.2 Write Documentation
- Installation guide
- Customization guide
- API documentation
- Troubleshooting

#### 3.3 Package for Distribution
- Create installable package
- Generate installation script
- Create GitHub releases

### Phase 4: Polish & Examples (1 week)

#### 4.1 Example Queries
- Query form templates
- Example API calls with curl
- JavaScript integration examples

#### 4.2 Styling Themes
- Default theme
- Alternative color schemes
- Dark mode support

#### 4.3 Performance Optimization
- Caching strategies
- Database query optimization
- Chart generation caching

## Key Features

### Static Skin Features
- **Current Conditions Display**: Latest reading with icons
- **Today Summary**: High/low/avg for current day
- **History Browser**: View past days/weeks/months
- **Pre-Generated Charts**: Daily, weekly, monthly, yearly trends
- **Responsive Design**: Mobile-first, works on phones/tablets/desktop
- **Touch-Optimized**: 44px minimum tap targets, swipe gestures
- **PWA-Ready**: Install to home screen like native app
- **Offline Capable**: View cached data without connection
- **Timezone-Aware**: Converts to user's local time
- **Unit Conversion**: Automatic F/C, mph/kph, in/mm conversions
- **Dark Mode**: Respects system preference automatically

### Dynamic API Features
- **Real-Time Data**: Live weather readings
- **Custom Date Ranges**: Query any period
- **Aggregated Statistics**: Min/max/avg for any parameter
- **On-Demand Charts**: Generate visualizations for selected period
- **JSON Responses**: Easy integration with external tools
- **CORS Support**: Use from other applications

### Combined Features
- **Single Deployment**: One skin, one service extension
- **Zero External Dependencies**: No Ollama, no GPUs needed
- **Automatic Updates**: Skin updates on WeeWX data archive
- **Extensible**: Easy to add new endpoints and templates
- **Private**: All data stays local, no cloud calls

## Hardware Requirements

### Minimum
- **CPU**: Single core sufficient
- **RAM**: 256 MB (most for WeeWX itself)
- **Storage**: 10 MB for skin + extension
- **Network**: Local network (no internet required)

### Recommended
- **CPU**: 2+ cores
- **RAM**: 512 MB - 1 GB
- **Storage**: 50 MB with chart cache
- **Network**: Wired Ethernet preferred

## Comparison: All Three Approaches

| Feature | Current MCP | Ollama + WebUI | WeeWX Native Skin |
|---------|-------------|---|---|
| **Interface** | CLI/Claude Desktop | Web UI | Web UI |
| **Accessibility** | Technical | All users | All users |
| **Hardware Required** | Minimal | Significant (8GB+ RAM) | Minimal |
| **Setup Complexity** | Medium | High (Docker) | Low |
| **Deployment Time** | Minutes | 30+ minutes | 10-15 minutes |
| **External Services** | None | Ollama + WebUI | None |
| **NLP Capability** | Full (Claude/LLM) | Full (Ollama) | Pattern-based |
| **Cost** | Free | Free | Free |
| **Privacy** | ✓ | ✓ | ✓ |
| **Maintenance** | Minimal | Moderate | Minimal |
| **Ideal For** | Claude integration | Power users | Everyone |

## Example: Query Sequences

### Via Skin Template
User opens dashboard → Cheetah template processes → Displays current temp + pre-generated charts

### Via REST API
User form → AJAX request → Flask endpoint → WeeWX database query → JSON response → JavaScript renders

### Hybrid (Most Powerful)
Skin shows pre-generated daily charts + JavaScript loads 7-day interactive chart from API on demand

## Future Enhancements

### Short Term
- [ ] Additional chart types (polar wind, humidity rose, etc.)
- [ ] Email alert notifications
- [ ] CSV export functionality
- [ ] Dark mode toggle

### Medium Term
- [ ] Dashboard customization (reorderable widgets)
- [ ] Comparison views (vs. last year, etc.)
- [ ] Integration with weather forecast APIs
- [ ] Mobile app (React Native sharing code)

### Long Term
- [ ] Machine learning anomaly detection
- [ ] Climate statistics and patterns
- [ ] Integration with smart home systems
- [ ] Multi-station support

## Deployment Example

### Quick Start
```bash
# 1. Install skin
cd ~/weewx
mkdir -p skins/weather-dashboard
# Copy skin files...

# 2. Install extension
mkdir -p extensions/weather-api/bin/user
# Copy extension files...

# 3. Update weewx.conf to register skin and service

# 4. Restart WeeWX
sudo systemctl restart weewx

# 5. Open browser
# http://localhost:8000/ (default WeeWX port)
```

## Conclusion

This native WeeWX approach offers:

1. **Accessibility**: Modern web interface without LLM complexity
2. **Efficiency**: Uses only WeeWX resources, minimal overhead
3. **Reliability**: Proven WeeWX architecture, no external dependencies
4. **Simplicity**: Straightforward installation and configuration
5. **Maintainability**: Integrates naturally with WeeWX ecosystem

Perfect for users wanting a modern web dashboard without the hardware requirements of Ollama, while still providing dynamic querying and custom chart generation through a clean REST API.

---

**Document Version**: 1.0  
**Last Updated**: January 17, 2026  
**Status**: Proposed Architecture
