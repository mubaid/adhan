---
date: 2026-03-20
topic: "Web Configuration Server for Adhan Clock"
status: draft
---

# Web Configuration Server Design

## Problem Statement

The Adhan Clock currently requires SSH access and CLI commands to configure settings. Users need to:
- Run Python scripts with command-line arguments to set location and preferences
- Manually edit files to change audio selections
- Use terminal commands to view logs and scheduled jobs

A web-based UI would make configuration accessible from any device on the local network without requiring terminal access.

## Constraints

- **Raspberry Pi environment** - Must be lightweight, minimal resource usage
- **Python ecosystem** - Should integrate with existing Python codebase
- **Local network only** - No external cloud services required
- **Root permissions needed** - Cron management requires root access
- **No existing web framework** - Fresh implementation needed

## Approach

**Flask with Jinja2 templates + HTMX** for the following reasons:

1. **Lightweight** - Flask has minimal footprint, suitable for Raspberry Pi
2. **No build process** - No npm, webpack, or compilation steps
3. **Python-native** - Direct integration with existing `praytimes.py` and `updateAzaanTimers.py`
4. **HTMX for interactivity** - Dynamic updates without heavy JavaScript frameworks
5. **Jinja2 templates** - Server-side rendering, simple to maintain

**Alternatives considered:**
- FastAPI + React: Overkill for config UI, requires build step
- Streamlit/NiceGUI: Heavier dependencies, less UI control
- Node.js: Different ecosystem from existing Python code

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Web Configuration Server                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Browser UI ◄──────► Flask Server ◄──────► Existing Components │
│  (Jinja2/HTMX)        (REST API)          (PrayTimes, CronTab)  │
│                              │                                  │
│                              ▼                                  │
│                       ┌────────────┐                            │
│                       │ Settings   │                            │
│                       │ Manager    │                            │
│                       │ (.json)    │                            │
│                       └────────────┘                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Flask Web Server (`web_server.py`)

**Responsibilities:**
- Serve HTML pages and static assets
- Expose REST API for settings management
- Integrate with existing prayer time calculation
- Manage settings persistence

**Routes:**

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Dashboard with today's times |
| `/settings` | GET | Settings configuration page |
| `/api/settings` | GET/POST | Get or update settings |
| `/api/times` | GET | Calculate times for a date |
| `/api/schedule` | GET | List current cron jobs |
| `/api/logs` | GET | Recent log entries |
| `/api/apply` | POST | Regenerate cron jobs |
| `/api/audio-files` | GET | List available MP3 files |

### 2. Settings Manager

**Responsibilities:**
- Load/save settings to JSON file (migrating from CSV)
- Validate all input values
- Provide defaults for missing values
- Migration from existing `.settings` CSV format

**New Settings Structure (JSON):**

```json
{
  "latitude": 25.28255,
  "longitude": 55.3622,
  "method": "Karachi",
  "fajr_volume": 0,
  "azaan_volume": 150,
  "asr_method": "Standard",
  "enabled_prayers": ["fajr", "dhuhr", "asr", "maghrib", "isha"],
  "audio_files": {
    "fajr": "Adhan-fajr.mp3",
    "dhuhr": "azaan-dua-new.mp3",
    "asr": "azaan-dua-new.mp3",
    "maghrib": "azaan-dua-new.mp3",
    "isha": "azaan-dua-new.mp3"
  }
}
```

### 3. Prayer Times Service

**Responsibilities:**
- Wrap existing `PrayTimes` class
- Calculate times for any given date
- Apply current settings (method, adjustments)
- Return structured response with all events

### 4. Cron Manager

**Responsibilities:**
- Read current scheduled jobs
- Generate new jobs from settings
- Apply changes to system cron
- Handle the update job (daily recalculation at 3:15 AM)

### 5. Frontend Templates

**Pages:**

1. **Dashboard (`/`)**
   - Today's prayer times display
   - Current settings summary
   - Quick status indicators
   - Next upcoming prayer highlight

2. **Settings (`/settings`)**
   - Location input (lat/lng)
   - Calculation method dropdown
   - Volume sliders
   - Audio file selectors (populated from available MP3s)
   - Enable/disable individual prayers
   - Save and Apply buttons

3. **Schedule (`/schedule`)**
   - List of current cron jobs
   - Readable time format
   - Job status indicators

4. **Logs (`/logs`)**
   - Recent log entries from `adhan.log`
   - Timestamp formatting
   - Error highlighting

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interaction                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  GET /                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Load settings from .settings.json                    │   │
│  │ 2. Calculate today's prayer times using PrayTimes       │   │
│  │ 3. Render dashboard template with data                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  POST /api/settings (Save Settings)                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Validate input (lat/lng range, method enum, etc.)    │   │
│  │ 2. Save to .settings.json                               │   │
│  │ 3. Return success/error response                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  POST /api/apply (Apply Changes)                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Load settings                                        │   │
│  │ 2. Calculate prayer times for today                     │   │
│  │ 3. Clear existing rpiAdhanClockJob cron entries         │   │
│  │ 4. Create new cron jobs for each enabled prayer         │   │
│  │ 5. Ensure daily update job exists                       │   │
│  │ 6. Write to system cron                                 │   │
│  │ 7. Return success/error response                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Error Handling

| Error Type | Detection | Response |
|------------|-----------|----------|
| Invalid latitude | Range check (-90 to 90) | 400 error, UI message |
| Invalid longitude | Range check (-180 to 180) | 400 error, UI message |
| Invalid method | Enum validation | 400 error, UI message |
| Missing settings file | File not found | Create with defaults |
| Cron write failure | Exception catch | 500 error, log warning |
| Audio file missing | File existence check | Validation error on save |
| Permission denied | Exception catch | Clear error, suggest root |

**UI Error Display:**
- Toast notifications for save errors
- Inline validation for form fields
- Warning banner for non-critical failures

## Testing Strategy

### Unit Tests
- Settings manager: load, save, validate, defaults
- Prayer times service: calculation accuracy
- API endpoint handlers

### Integration Tests
- Full save → apply → cron verification flow
- Settings migration from old CSV format

### Manual Testing
- UI responsiveness on mobile devices
- Cron job creation verification
- Audio playback after configuration

## Open Questions

1. **Port Configuration**
   - Default: 5000 (Flask default)
   - Configurable via environment variable or settings file?

2. **Authentication**
   - Option A: No auth (local network trust)
   - Option B: Simple password protection
   - Recommendation: Start with no auth, add if needed

3. **HTTPS**
   - Option A: HTTP only (local network)
   - Option B: Self-signed certificate
   - Recommendation: HTTP for simplicity, HTTPS optional

4. **Mobile Responsiveness**
   - High priority - users likely configure from phones
   - CSS framework: minimal custom CSS or lightweight framework

## File Structure

```
/root/adhan/
├── web_server.py          # Flask application
├── settings_manager.py    # Settings handling
├── templates/             # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── settings.html
│   ├── schedule.html
│   └── logs.html
├── static/                # CSS, JS, images
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── htmx.min.js
├── .settings.json         # New JSON settings file
├── updateAzaanTimers.py   # Existing (minimal changes)
├── praytimes.py           # Existing (no changes)
└── playAzaan.sh           # Existing (no changes)
```

## Migration Path

1. **Phase 1**: Create web server with read-only dashboard
2. **Phase 2**: Add settings editing capability
3. **Phase 3**: Migrate settings from CSV to JSON
4. **Phase 4**: Add cron management via UI

The existing CLI interface (`updateAzaanTimers.py`) remains functional for users who prefer it.
