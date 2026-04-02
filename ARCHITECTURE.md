# Adhan Clock - Architecture

## Overview

**Adhan Clock** is a Raspberry Pi-based Islamic prayer times application that calculates daily prayer times and automatically plays Adhan (call to prayer) audio at scheduled intervals using cron.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Adhan Clock System                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │   User       │    │   Cron       │    │   Audio          │  │
│  │   Input      │───▶│   Scheduler  │───▶│   Player         │  │
│  │ (args/file)  │    │              │    │   (playAzaan.sh) │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│         │                   │                      │          │
│         ▼                   ▼                      ▼          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              updateAzaanTimers.py                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │  │
│  │  │ Arg Parser │  │ Settings  │  │ Prayer Time        │  │  │
│  │  │            │  │ Manager   │  │ Calculator         │  │  │
│  │  │            │  │ (.settings)│  │ (PrayTimes)       │  │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              CronTab (System Cron)                        │  │
│  │  • Fajr    • Dhuhr  • Asr  • Maghrib  • Isha            │  │
│  │  • Imsak   • Zawaal • Iftar • Surah Al-Baqarah          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. updateAzaanTimers.py (Main Entry Point)

**Responsibilities:**
- Parse command-line arguments (latitude, longitude, calculation method)
- Load/save settings to `.settings` file
- Calculate prayer times using PrayTimes library
- Schedule cron jobs for each prayer time
- Manage audio playback commands

**Flow:**
```
User Run → Parse Args → Load Settings → Calculate Times → Schedule Cron → Exit
     │
     └── (via cron at 3:15 AM daily) → Load Settings → Recalculate → Reschedule
```

### 2. praytimes.py (Prayer Time Calculator)

**Responsibilities:**
- Implement Islamic prayer time calculation algorithms
- Support multiple calculation methods (MWL, ISNA, Egypt, Makkah, Karachi, Tehran, Jafari)
- Apply adjustments (Hanafi/asr, time offsets)
- Return times for all prayer events

### 3. playAzaan.sh (Audio Player)

**Responsibilities:**
- Play MP3 files for Adhan
- Apply volume control via command-line argument
- Execute before/after hooks for custom actions

### 4. Hook System

**Directories:**
- `before-hooks.d/` - Scripts executed before Adhan plays
- `after-hooks.d/` - Scripts executed after Adhan plays

**Use Cases:**
- Pause/resume Quran playback
- Network blocking/unblocking (Pi-hole)
- Social media status updates

## Data Flow

```
1. Initial Setup (User Run)
   CLI Args ──▶ mergeArgs() ──▶ .settings file
                              │
                              ▼
                        PrayTimes.getTimes()
                              │
                              ▼
                        Calculate 8 prayer times
                              │
                              ▼
                        CronTab.remove_all()
                              │
                              ▼
                        CronTab.new() × 8 jobs
                              │
                              ▼
                        system_cron.write_to_user()

2. Daily Update (Cron Run at 3:15 AM)
   cron triggers updateAzaanTimers.py
         │
         ▼
   Load from .settings (no args needed)
         │
         ▼
   Recalculate for today's date
         │
         ▼
   Reschedule all cron jobs
```

## Prayer Times Scheduled

| Prayer | Description | Audio File |
|--------|-------------|------------|
| Imsak | Start of fasting period | imsak_start.mp3 |
| Zawaal | Solar noon | zawaal_start.mp3 |
| Dhuhr | Noon prayer | azaan-dua-new.mp3 |
| Asr | Afternoon prayer | azaan-dua-new.mp3 |
| Maghrib | Sunset prayer | azaan-dua-new.mp3 |
| Iftar | Breaking fast | iftardua.mp3 |
| Isha | Night prayer | azaan-dua-new.mp3 |
| Surah Al-Baqarah | Daily recitation (10:15) | surahalbaqarah.mp3 |

## Configuration

### Settings File (`.settings`)
```
lat,lng,method,fajr_volume,azaan_volume
```

### Command-Line Arguments
- `--lat`: Latitude (-90 to 90)
- `--lng`: Longitude (-180 to 180)
- `--method`: Calculation method (MWL, ISNA, Egypt, Makkah, Karachi, Tehran, Jafari)
- `--fajr-azaan-volume`: Fajr adhan volume in millibels
- `--azaan-volume`: Other adhan volumes in millibels

## Cron Schedule

- **Daily update**: 3:15 AM
- **Log rotation**: 1st of each month at midnight

## Extension Points

1. **Additional prayer times**: Add new entries in prayer calculation loop
2. **Custom audio**: Replace MP3 files in project root
3. **Hook integrations**: Add scripts to before/after hooks.d directories
4. **Calculation methods**: Extend PrayTimes with custom algorithms
