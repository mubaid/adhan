# Raspberry Pi Adhan Clock

This project automatically calculates [adhan](https://en.wikipedia.org/wiki/Adhan) times every day and plays all prayers at their scheduled time using cron.

Includes a **web-based configuration server** so you can manage settings from any browser on your local network.

## Prerequisites

1. Any Linux system running Python 3 (Raspberry Pi recommended)
2. Speakers with auxiliary audio cable
3. `mpg321` — audio player (`sudo apt install mpg321`)
4. `python3`, `flask`, `python-crontab` — Python dependencies

> **Note:** `mpg321` is the audio player used by `playAzaan.sh`. Install it before first run.

## Quick Start

### 1. Clone the repository

```bash
sudo apt-get install git
cd ~
git clone <repo-url> adhan
cd adhan
```

### 2. Install dependencies

```bash
sudo apt install mpg321 python3-flask
```

### 3. First run

Run the script with your location coordinates and calculation method:

```bash
python3 updateAzaanTimers.py --lat 25.28255 --lng 55.3622 --method Karachi
```

- `--lat` / `--lng` — your city's latitude and longitude
- `--method` — prayer time calculation method (`MWL`, `ISNA`, `Egypt`, `Makkah`, `Karachi`, `Tehran`, `Jafari`)
- `--fajr-azaan-volume` — Fajr adhan volume in millibels (default `0`)
- `--azaan-volume` — volume for all other adhans in millibels (default `0`)

This creates `.settings.json` and schedules cron jobs for daily prayer times.

> Volume values use millibels: `1500` is loud, `-30000` is quiet, `0` is default.

### 4. Start the web server

```bash
sudo cp adhan-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now adhan-web
```

The web UI is now available at `http://<your-pi-ip>:5001`.

To start it manually without systemd:

```bash
python3 web_server.py
```

The port defaults to `5001`. Override with `PORT=8080 python3 web_server.py`.

## Web UI

The web server provides four pages:

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/` | Today's prayer times with next-prayer highlight |
| Settings | `/settings` | Location, volumes, prayer enable/disable, time offsets, timezone, audio files |
| Schedule | `/schedule` | View active cron jobs |
| Logs | `/logs` | Recent log output with error highlighting |

Changes made in the web UI are saved to `.settings.json` and can be applied to cron from the Settings page.

## Configuration

### Settings file

Settings are stored in `.settings.json` in the project root. The CLI script (`updateAzaanTimers.py`) and web server both read from this file.

If migrating from the legacy `.settings` CSV format, the web server or CLI will automatically migrate to JSON on first load.

### Default configuration

```json
{
  "latitude": null,
  "longitude": null,
  "timezone": "UTC",
  "method": "Karachi",
  "asr_method": "Hanafi",
  "fajr_volume": 0,
  "azaan_volume": 150,
  "surahbaqarah_volume": 75,
  "enabled_prayers": [
    "dahwaekubra", "dhuhr", "asr", "maghrib", "isha", "surahbaqarah"
  ],
  "time_offsets": {
    "fajr": 0,
    "sunrise": -6,
    "dhuhr": 3,
    "asr": 3,
    "maghrib": 3,
    "isha": 0
  },
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
  },
  "surahbaqarah_time": "10:15"
}
```

### Settings reference

| Setting | Range | Description |
|---------|-------|-------------|
| `latitude` | -90 to 90 | Location latitude |
| `longitude` | -180 to 180 | Location longitude |
| `timezone` | IANA timezone name | Timezone for prayer time calculation (e.g. `Asia/Dubai`, `America/New_York`) |
| `method` | `MWL`, `ISNA`, `Egypt`, `Makkah`, `Karachi`, `Tehran`, `Jafari` | Prayer time calculation method |
| `asr_method` | `Standard`, `Hanafi` | Asr shadow calculation method |
| `fajr_volume` | -30000 to 1500 | Fajr adhan volume in millibels |
| `azaan_volume` | -30000 to 1500 | General adhan volume in millibels |
| `surahbaqarah_volume` | -30000 to 1500 | Surah Baqarah playback volume in millibels |
| `enabled_prayers` | list of prayer names | Which prayers to schedule |
| `time_offsets` | minutes | Per-prayer minute offset |
| `audio_files` | MP3 filename per prayer | Which audio file plays for each prayer |
| `surahbaqarah_time` | `HH:MM` | Fixed time for Surah Baqarah playback |

### Available prayers

`fajr`, `imsak`, `dahwaekubra`, `dhuhr`, `asr`, `maghrib`, `iftardua`, `isha`, `surahbaqarah`

The `surahbaqarah` prayer is scheduled at a fixed time (default `10:15`) regardless of prayer time calculations.

## REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/settings` | `GET` | Get current settings as JSON |
| `/api/settings` | `POST` | Save settings (JSON or form-encoded) |
| `/api/times` | `GET` | Calculate prayer times. Optional `?date=YYYY-MM-DD` |
| `/api/apply` | `POST` | Apply settings to cron |
| `/api/schedule` | `GET` | List active cron jobs |
| `/api/logs` | `GET` | Get recent logs. Optional `?lines=50` |
| `/api/audio-files` | `GET` | List available MP3 files |

## Hooks

Run custom commands before/after adhan playback by placing scripts in:

- `before-hooks.d/` — runs before adhan
- `after-hooks.d/` — runs after adhan

Example to pause/resume Quran playback:

```bash
# before-hooks.d/01-pause-quran.sh
#!/usr/bin/env bash
/home/pi/RPi_QuranSpeaker/pauser.py pause

# after-hooks.d/01-resume-quran.sh
#!/usr/bin/env bash
/home/pi/RPi_QuranSpeaker/pauser.py resume
```

Make scripts executable with `chmod u+x`.

## Service Management

The adhan web server runs as a systemd service (`adhan-web.service`).

| Command | Description |
|---------|-------------|
| `sudo systemctl start adhan-web` | Start the web server |
| `sudo systemctl stop adhan-web` | Stop the web server |
| `sudo systemctl restart adhan-web` | Restart the web server |
| `sudo systemctl status adhan-web` | Check service status |
| `sudo systemctl enable adhan-web` | Enable auto-start on boot |

The service is configured with **auto-restart on failure** (`Restart=on-failure`, `RestartSec=5`) and a **start rate limit** of 5 attempts per 60 seconds to prevent crash loops.

## Tips

1. View scheduled jobs: `crontab -l`
2. Logs are at `adhan.log`, truncated on the 1st of each month
3. The port can be changed in the systemd unit file (`Environment=PORT=5001`) or via env var when running manually

## Credits

* Prayer time calculation: http://praytimes.org/code/
* Adhan clock concept: http://randomconsultant.blogspot.co.uk/2013/07/turn-your-raspberry-pi-into-azaanprayer.html
* Cron scheduler: https://pypi.python.org/pypi/python-crontab/
