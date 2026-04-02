---
date: 2026-03-20
topic: "Web Configuration Server - Implementation Plan"
design: thoughts/shared/designs/2026-03-20-web-config-server-design.md
status: ready
---

# Implementation Plan: Web Configuration Server

## Overview

Implement a Flask + HTMX web configuration server for the Adhan Clock, migrating settings from CSV (`.settings`) to JSON (`.settings.json`), and providing a browser-based UI for configuration, schedule viewing, and log access.

## Prerequisites

- Flask 3.1.1 and Jinja2 3.1.6 are already installed on the system
- python-crontab is bundled in `/root/adhan/crontab/`
- No new pip dependencies required (HTMX loaded via CDN)

## Implementation Phases

---

### Phase 1: Settings Manager (`settings_manager.py`)

**Goal**: Create a standalone module for loading, validating, and saving settings in JSON format, with migration support from the legacy CSV `.settings` file.

**File**: `/root/adhan/settings_manager.py`

**Tasks**:

1. **Define settings schema and defaults**
   ```python
   DEFAULTS = {
       "latitude": None,
       "longitude": None,
       "method": "Karachi",
       "fajr_volume": 0,
       "azaan_volume": 150,
       "asr_method": "Hanafi",
       "enabled_prayers": ["dahwaekubra", "dhuhr", "asr", "maghrib", "isha", "surahbaqarah"],
       "audio_files": {
           "fajr": "Adhan-fajr.mp3",
           "imsak": "imsak_start.mp3",
           "dahwaekubra": "zawaal_start.mp3",
           "dhuhr": "azaan-dua-new.mp3",
           "asr": "azaan-dua-new.mp3",
           "maghrib": "azaan-dua-new.mp3",
           "isha": "azaan-dua-new.mp3",
           "iftardua": "iftardua.mp3",
           "surahbaqarah": "surahalbaqarah.mp3"
       }
   }
   ```
   - Matches current behavior: `enabled_prayers` defaults reflect what's currently active in `updateAzaanTimers.py` (lines 165-171), excluding the commented-out fajr/imsak/iftardua
   - `asr_method` defaults to `"Hanafi"` matching the hardcoded `PT.adjust({'asr': 'Hanafi'})` on line 128

2. **Implement `load_settings()`**
   - Try loading `.settings.json` first
   - If not found, attempt migration from `.settings` (CSV): parse the 5-field CSV (`lat,lng,method,fajr_vol,azaan_vol`) and merge with defaults
   - If neither exists, return defaults with `None` lat/lng
   - Return a validated settings dict

3. **Implement `save_settings(settings)`**
   - Validate all fields:
     - `latitude`: float, range -90 to 90
     - `longitude`: float, range -180 to 180
     - `method`: one of `["MWL", "ISNA", "Egypt", "Makkah", "Karachi", "Tehran", "Jafari"]`
     - `fajr_volume`: int, range -30000 to 1500
     - `azaan_volume`: int, range -30000 to 1500
     - `asr_method`: one of `["Standard", "Hanafi"]`
     - `enabled_prayers`: list of valid prayer names
     - `audio_files`: dict of prayer->filename, verify files exist in root_dir
   - Write to `.settings.json` with pretty-printing
   - Return `(success: bool, errors: list)` tuple

4. **Implement `migrate_from_csv()`**
   - Parse existing `.settings` CSV format
   - Map fields: `lat`->`latitude`, `lng`->`longitude`, `fajr_azaan_vol`->`fajr_volume`, `azaan_vol`->`azaan_volume`
   - Preserve `.settings` file (do not delete)

5. **Implement `get_available_audio_files()`**
   - List all `*.mp3` files in `root_dir`
   - Return list of filenames

**Testing**: Manual test by loading existing `.settings` CSV and verifying JSON output.

---

### Phase 2: Flask Web Server (`web_server.py`)

**Goal**: Create the Flask application with all routes, API endpoints, and integration with existing components.

**File**: `/root/adhan/web_server.py`

**Tasks**:

1. **App setup**
   - Import Flask, sys path setup for bundled crontab
   - Import `settings_manager` functions
   - Import `PrayTimes` from `praytimes.py`
   - Configure: `root_dir`, template/static folders
   - Port: 5000 (Flask default), configurable via `PORT` env var

2. **Implement page routes**

   | Route | Handler Logic |
   |-------|--------------|
   | `GET /` | Load settings, calculate today's times via PrayTimes, find next prayer, render `dashboard.html` |
   | `GET /settings` | Load settings, list available audio files, render `settings.html` |
   | `GET /schedule` | Load cron jobs with comment `rpiAdhanClockJob`, render `schedule.html` |
   | `GET /logs` | Read last N lines from `adhan.log`, render `logs.html` |

3. **Implement API routes**

   - `GET /api/settings` → Return settings JSON
   - `POST /api/settings` → Validate + save settings, return success/errors
   - `GET /api/times?date=YYYY-MM-DD` → Calculate times for given date (default: today), return JSON with all prayer times
   - `GET /api/schedule` → Return cron jobs as JSON array
   - `GET /api/logs?lines=50` → Return last N log lines as JSON
   - `POST /api/apply` → Regenerate cron jobs:
     1. Load settings
     2. Calculate today's prayer times
     3. Remove existing `rpiAdhanClockJob` cron entries
     4. Create cron jobs for each enabled prayer
     5. Add daily 3:15 AM update job
     6. Add monthly log truncation job
     7. Write to system cron
     8. Return success/error
   - `GET /api/audio-files` → Return list of available MP3 filenames

4. **Prayer time calculation helper**
   - Reuse `PrayTimes` class exactly as `updateAzaanTimers.py` does
   - Apply same tune offsets: `{'fajr': 0, 'sunrise': -6, 'dhuhr': 3, 'asr': 3, 'maghrib': 3, 'isha': 0}`
   - Compute UTC offset from system timezone
   - Return dict with all computed times

5. **Cron management helper**
   - Use bundled `crontab.CronTab(user='root')`
   - Tag all jobs with comment `rpiAdhanClockJob` (matches existing convention, see `updateAzaanTimers.py:142`)
   - Build play commands: `{root_dir}/playAzaan.sh {root_dir}/{audio_file} {volume}`
   - Handle `fajr` volume separately (`fajr_volume` vs `azaan_volume`)
   - Special case: `surahbaqarah` uses `azaan_volume * 0.5` (matching line 139)
   - Special case: `iftardua` uses `azaan_volume * 2` (matching line 138)
   - `dahwaekubra` uses `zawaal_start.mp3` (matching line 165)

6. **Entry point**
   ```python
   if __name__ == '__main__':
       port = int(os.environ.get('PORT', 5000))
       app.run(host='0.0.0.0', port=port, debug=False)
   ```

---

### Phase 3: Frontend Templates

**Goal**: Create mobile-responsive HTML templates using Jinja2 and HTMX for dynamic updates.

**Directory**: `/root/adhan/templates/`

**Tasks**:

1. **`base.html`** - Base template
   - HTML5 doctype, responsive viewport meta
   - Include HTMX from CDN: `https://unpkg.com/htmx.org@2.0.4`
   - Inline minimal CSS (no external build step):
     - CSS variables for colors (green/amber/red status indicators)
     - Mobile-first responsive grid
     - Simple nav bar with links: Dashboard, Settings, Schedule, Logs
   - `{% block content %}` for child templates
   - Toast notification container (for HTMX response messages)

2. **`dashboard.html`** - Main dashboard (`/`)
   - Today's date display
   - Prayer times table with columns: Prayer, Time, Audio File
   - Next prayer highlighted (green background)
   - Current settings summary card: location, method, volumes
   - "Apply Settings" button (posts to `/api/apply`, shows toast on success/error)
   - Settings validation warnings if lat/lng not configured

3. **`settings.html`** - Configuration page (`/settings`)
   - Form with `hx-post="/api/settings"` and `hx-target="#result"`
   - Fields:
     - Latitude (number input, step 0.00001, -90 to 90)
     - Longitude (number input, step 0.00001, -180 to 180)
     - Calculation method (select: MWL, ISNA, Egypt, Makkah, Karachi, Tehran, Jafari)
     - ASR method (select: Standard, Hanafi)
     - Fajr volume (range slider, -30000 to 1500, with live value display)
     - Azaan volume (range slider, -30000 to 1500, with live value display)
     - Enabled prayers (checkboxes for each prayer)
     - Audio file selectors (select dropdown per prayer, populated from available MP3s)
   - Save button (saves settings only)
   - "Save & Apply" button (saves then calls `/api/apply`)

4. **`schedule.html`** - Cron schedule page (`/schedule`)
   - Table of current `rpiAdhanClockJob` cron entries
   - Columns: Job, Schedule (raw cron expression), Next Run (computed)
   - Refresh button with `hx-get="/api/schedule" hx-target="#schedule-table"`
   - Auto-refresh via `hx-trigger="every 60s"` (optional)

5. **`logs.html`** - Log viewer (`/logs`)
   - Pre-formatted log output in a scrollable container
   - Last 100 lines by default
   - Refresh button with `hx-get="/api/logs" hx-target="#log-content"`
   - Red highlighting for lines containing "error" or "failed"

**Static assets**: `/root/adhan/static/`
- `static/css/style.css` - Minimal custom CSS
- `static/js/` - Only if needed beyond HTMX (likely not)

---

### Phase 4: Integration with Existing CLI

**Goal**: Update `updateAzaanTimers.py` to read from `.settings.json` when available, while maintaining backward compatibility.

**File**: `/root/adhan/updateAzaanTimers.py` (minimal changes)

**Tasks**:

1. **Add JSON settings loading** in `mergeArgs()`:
   - Try loading `.settings.json` via `settings_manager.load_settings()` first
   - Fall back to CSV `.settings` if JSON not found
   - CLI args still override file values (preserving existing behavior)

2. **Support new settings fields**:
   - Read `enabled_prayers` from JSON settings
   - Read `audio_files` mapping from JSON settings
   - Only schedule cron jobs for prayers in `enabled_prayers`
   - Use `audio_files[prayer]` for the audio file per prayer

3. **Preserve existing behavior**:
   - Self-update cron job at 3:15 AM (unchanged)
   - Monthly log truncation (unchanged)
   - `strJobComment = 'rpiAdhanClockJob'` (unchanged)
   - Time tune offsets (unchanged)

---

### Phase 5: Systemd Service & Deployment

**Goal**: Make the web server start automatically on boot.

**Tasks**:

1. **Create systemd service file** `/etc/systemd/system/adhan-web.service`:
   ```ini
   [Unit]
   Description=Adhan Clock Web Configuration Server
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/root/adhan
   ExecStart=/usr/bin/python3 /root/adhan/web_server.py
   Restart=on-failure
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable and start**:
   ```bash
   systemctl daemon-reload
   systemctl enable adhan-web
   systemctl start adhan-web
   ```

3. **Update `.gitignore`**:
   - Add `.settings.json` (per-instance config, like `.settings`)

---

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `settings_manager.py` | **Create** | Settings load/save/validate/migrate module |
| `web_server.py` | **Create** | Flask app with all routes and API endpoints |
| `templates/base.html` | **Create** | Base template with nav, HTMX, CSS |
| `templates/dashboard.html` | **Create** | Dashboard page |
| `templates/settings.html` | **Create** | Settings configuration page |
| `templates/schedule.html` | **Create** | Cron schedule viewer |
| `templates/logs.html` | **Create** | Log viewer page |
| `static/css/style.css` | **Create** | Minimal responsive CSS |
| `updateAzaanTimers.py` | **Modify** | Add JSON settings support (backward compatible) |
| `.gitignore` | **Modify** | Add `.settings.json` |

## Prayer-to-Audio Mapping (Current Behavior)

This mapping must be preserved when generating cron jobs:

| Prayer | Audio File | Volume Source | Notes |
|--------|-----------|---------------|-------|
| fajr | `Adhan-fajr.mp3` | `fajr_volume` | Currently commented out |
| imsak | `imsak_start.mp3` | `azaan_volume` | Currently commented out |
| dahwaekubra | `zawaal_start.mp3` | `azaan_volume` | Active |
| dhuhr | `azaan-dua-new.mp3` | `azaan_volume` | Active |
| asr | `azaan-dua-new.mp3` | `azaan_volume` | Active |
| maghrib | `azaan-dua-new.mp3` | `azaan_volume` | Active |
| iftardua | `iftardua.mp3` | `azaan_volume * 2` | Currently commented out |
| isha | `azaan-dua-new.mp3` | `azaan_volume` | Active |
| surahbaqarah | `surahalbaqarah.mp3` | `azaan_volume * 0.5` | Active, hardcoded 10:15 |

## Implementation Order

```
Phase 1: settings_manager.py     (no dependencies, standalone)
   │
   ▼
Phase 2: web_server.py           (depends on Phase 1)
   │
   ▼
Phase 3: Templates + Static      (depends on Phase 2)
   │
   ▼
Phase 4: CLI integration         (depends on Phase 1)
   │
   ▼
Phase 5: Deployment              (depends on Phase 2+3)
```

Phases 4 and 5 are independent of each other and can be done in parallel.

## Verification

After each phase:

1. **Phase 1**: Run `python3 -c "from settings_manager import load_settings; print(load_settings())"` and verify it loads/migrates settings correctly
2. **Phase 2**: Run `python3 web_server.py` and test each API endpoint with `curl`:
   - `curl localhost:5000/api/settings`
   - `curl localhost:5000/api/times`
   - `curl -X POST localhost:5000/api/settings -H 'Content-Type: application/json' -d '{"latitude":25.28,"longitude":55.36,"method":"Karachi"}'`
   - `curl localhost:5000/api/schedule`
   - `curl -X POST localhost:5000/api/apply`
3. **Phase 3**: Open `http://<pi-ip>:5000/` in a browser, verify all pages render, forms submit, HTMX updates work
4. **Phase 4**: Run `python3 updateAzaanTimers.py --lat 25.28 --lng 55.36 --method Karachi` and verify it reads from `.settings.json`
5. **Phase 5**: Reboot Pi, verify `systemctl status adhan-web` shows running, access web UI from phone

## Open Decisions

These match the design doc's open questions - recommend the following defaults:

1. **Port**: 5000 (hardcoded default, env var override)
2. **Auth**: None initially (local network trust)
3. **HTTPS**: None initially (HTTP only)
4. **CSS**: Custom minimal CSS (no framework dependency)
