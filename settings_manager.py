#!/usr/bin/env python3

import json
import os
from os.path import dirname, abspath, join as pathjoin

root_dir = dirname(abspath(__file__))
SETTINGS_JSON = pathjoin(root_dir, '.settings.json')
SETTINGS_CSV = pathjoin(root_dir, '.settings')

VALID_METHODS = ['MWL', 'ISNA', 'Egypt', 'Makkah', 'Karachi', 'Tehran', 'Jafari']
VALID_ASR_METHODS = ['Standard', 'Hanafi']
VALID_PRAYERS = ['fajr', 'imsak', 'dahwaekubra', 'dhuhr', 'asr', 'maghrib', 'iftardua', 'isha', 'surahbaqarah']

# Common IANA timezones for prayer time locations
VALID_TIMEZONES = [
    'UTC',
    'Africa/Cairo',
    'Africa/Johannesburg',
    'Africa/Lagos',
    'Africa/Nairobi',
    'America/Anchorage',
    'America/Argentina/Buenos_Aires',
    'America/Bogota',
    'America/Chicago',
    'America/Denver',
    'America/Edmonton',
    'America/Halifax',
    'America/Havana',
    'America/Los_Angeles',
    'America/Manaus',
    'America/Mexico_City',
    'America/New_York',
    'America/Panama',
    'America/Phoenix',
    'America/Santiago',
    'America/Sao_Paulo',
    'America/Toronto',
    'America/Vancouver',
    'Asia/Baghdad',
    'Asia/Bahrain',
    'Asia/Bangkok',
    'Asia/Colombo',
    'Asia/Dhaka',
    'Asia/Dubai',
    'Asia/Ho_Chi_Minh',
    'Asia/Hong_Kong',
    'Asia/Jakarta',
    'Asia/Jerusalem',
    'Asia/Karachi',
    'Asia/Kolkata',
    'Asia/Kuala_Lumpur',
    'Asia/Kuwait',
    'Asia/Manila',
    'Asia/Qatar',
    'Asia/Riyadh',
    'Asia/Seoul',
    'Asia/Shanghai',
    'Asia/Singapore',
    'Asia/Taipei',
    'Asia/Tehran',
    'Asia/Tokyo',
    'Australia/Adelaide',
    'Australia/Brisbane',
    'Australia/Melbourne',
    'Australia/Perth',
    'Australia/Sydney',
    'Europe/Amsterdam',
    'Europe/Athens',
    'Europe/Berlin',
    'Europe/Brussels',
    'Europe/Budapest',
    'Europe/Copenhagen',
    'Europe/Dublin',
    'Europe/Helsinki',
    'Europe/Istanbul',
    'Europe/Lisbon',
    'Europe/London',
    'Europe/Madrid',
    'Europe/Moscow',
    'Europe/Oslo',
    'Europe/Paris',
    'Europe/Rome',
    'Europe/Stockholm',
    'Europe/Vienna',
    'Europe/Warsaw',
    'Europe/Zurich',
    'Pacific/Auckland',
    'Pacific/Fiji',
    'Pacific/Honolulu',
]

# Map common timezone names to UTC offsets (for reference/validation)
TIMEZONE_UTC_OFFSETS = {
    'UTC': 0,
    'Africa/Cairo': 2,
    'Africa/Johannesburg': 2,
    'Africa/Lagos': 1,
    'Africa/Nairobi': 3,
    'America/Anchorage': -9,
    'America/Argentina/Buenos_Aires': -3,
    'America/Bogota': -5,
    'America/Chicago': -6,
    'America/Denver': -7,
    'America/Edmonton': -7,
    'America/Halifax': -4,
    'America/Havana': -5,
    'America/Los_Angeles': -8,
    'America/Manaus': -4,
    'America/Mexico_City': -6,
    'America/New_York': -5,
    'America/Panama': -5,
    'America/Phoenix': -7,
    'America/Santiago': -4,
    'America/Sao_Paulo': -3,
    'America/Toronto': -5,
    'America/Vancouver': -8,
    'Asia/Baghdad': 3,
    'Asia/Bahrain': 3,
    'Asia/Bangkok': 7,
    'Asia/Colombo': 5.5,
    'Asia/Dhaka': 6,
    'Asia/Dubai': 4,
    'Asia/Ho_Chi_Minh': 7,
    'Asia/Hong_Kong': 8,
    'Asia/Jakarta': 7,
    'Asia/Jerusalem': 2,
    'Asia/Karachi': 5,
    'Asia/Kolkata': 5.5,
    'Asia/Kuala_Lumpur': 8,
    'Asia/Kuwait': 3,
    'Asia/Manila': 8,
    'Asia/Qatar': 3,
    'Asia/Riyadh': 3,
    'Asia/Seoul': 9,
    'Asia/Shanghai': 8,
    'Asia/Singapore': 8,
    'Asia/Taipei': 8,
    'Asia/Tehran': 3.5,
    'Asia/Tokyo': 9,
    'Australia/Adelaide': 9.5,
    'Australia/Brisbane': 10,
    'Australia/Melbourne': 10,
    'Australia/Perth': 8,
    'Australia/Sydney': 10,
    'Europe/Amsterdam': 1,
    'Europe/Athens': 2,
    'Europe/Berlin': 1,
    'Europe/Brussels': 1,
    'Europe/Budapest': 1,
    'Europe/Copenhagen': 1,
    'Europe/Dublin': 0,
    'Europe/Helsinki': 2,
    'Europe/Istanbul': 3,
    'Europe/Lisbon': 0,
    'Europe/London': 0,
    'Europe/Madrid': 1,
    'Europe/Moscow': 3,
    'Europe/Oslo': 1,
    'Europe/Paris': 1,
    'Europe/Rome': 1,
    'Europe/Stockholm': 1,
    'Europe/Vienna': 1,
    'Europe/Warsaw': 1,
    'Europe/Zurich': 1,
    'Pacific/Auckland': 12,
    'Pacific/Fiji': 12,
    'Pacific/Honolulu': -10,
}

DEFAULTS = {
    'latitude': None,
    'longitude': None,
    'timezone': 'UTC',
    'method': 'Karachi',
    'fajr_volume': 0,
    'azaan_volume': 150,
    'surahbaqarah_volume': 75,
    'asr_method': 'Hanafi',
    'enabled_prayers': ['dahwaekubra', 'dhuhr', 'asr', 'maghrib', 'isha', 'surahbaqarah'],
    'time_offsets': {
        'fajr': 0,
        'sunrise': -6,
        'dhuhr': 3,
        'asr': 3,
        'maghrib': 3,
        'isha': 0
    },
    'audio_files': {
        'fajr': 'Adhan-fajr.mp3',
        'imsak': 'imsak_start.mp3',
        'dahwaekubra': 'zawaal_start.mp3',
        'dhuhr': 'azaan-dua-new.mp3',
        'asr': 'azaan-dua-new.mp3',
        'maghrib': 'azaan-dua-new.mp3',
        'isha': 'azaan-dua-new.mp3',
        'iftardua': 'iftardua.mp3',
        'surahbaqarah': 'surahalbaqarah.mp3'
    },
    'surahbaqarah_time': '10:15'
}


def _migrate_from_csv():
    """Parse legacy .settings CSV and return as dict."""
    try:
        with open(SETTINGS_CSV, 'rt') as f:
            parts = f.readlines()[0].strip().split(',')
        if len(parts) < 5:
            return None
        lat, lng, method, fajr_vol, azaan_vol = parts[:5]
        settings = dict(DEFAULTS)
        if lat:
            settings['latitude'] = float(lat)
        if lng:
            settings['longitude'] = float(lng)
        if method and method in VALID_METHODS:
            settings['method'] = method
        if fajr_vol:
            settings['fajr_volume'] = int(fajr_vol)
        if azaan_vol:
            settings['azaan_volume'] = int(azaan_vol)
        return settings
    except Exception:
        return None


def load_settings():
    """Load settings from .settings.json, falling back to CSV migration."""
    if os.path.exists(SETTINGS_JSON):
        try:
            with open(SETTINGS_JSON, 'rt') as f:
                data = json.load(f)
            # Merge with defaults for any missing keys
            merged = dict(DEFAULTS)
            merged.update(data)
            return merged
        except Exception:
            pass

    # Try CSV migration
    if os.path.exists(SETTINGS_CSV):
        migrated = _migrate_from_csv()
        if migrated:
            save_settings(migrated)
            return migrated

    return dict(DEFAULTS)


def save_settings(settings):
    """Validate and save settings to .settings.json.

    Returns (success, errors) tuple.
    """
    errors = []

    # Validate latitude
    lat = settings.get('latitude')
    if lat is not None:
        try:
            lat = float(lat)
            if lat < -90 or lat > 90:
                errors.append('Latitude must be between -90 and 90')
            settings['latitude'] = lat
        except (ValueError, TypeError):
            errors.append('Latitude must be a number')

    # Validate longitude
    lng = settings.get('longitude')
    if lng is not None:
        try:
            lng = float(lng)
            if lng < -180 or lng > 180:
                errors.append('Longitude must be between -180 and 180')
            settings['longitude'] = lng
        except (ValueError, TypeError):
            errors.append('Longitude must be a number')

    # Validate timezone
    timezone = settings.get('timezone', DEFAULTS['timezone'])
    if timezone not in VALID_TIMEZONES:
        errors.append(f'Invalid timezone. Must be one of the valid IANA timezones.')
    settings['timezone'] = timezone

    # Validate method
    method = settings.get('method', DEFAULTS['method'])
    if method not in VALID_METHODS:
        errors.append(f'Invalid method. Must be one of: {", ".join(VALID_METHODS)}')
    settings['method'] = method

    # Validate asr_method
    asr_method = settings.get('asr_method', DEFAULTS['asr_method'])
    if asr_method not in VALID_ASR_METHODS:
        errors.append(f'Invalid ASR method. Must be one of: {", ".join(VALID_ASR_METHODS)}')
    settings['asr_method'] = asr_method

    # Validate volumes
    for field, label in [('fajr_volume', 'Fajr volume'), ('azaan_volume', 'Azaan volume'), ('surahbaqarah_volume', 'Surah Baqarah volume')]:
        vol = settings.get(field)
        try:
            vol = int(vol)
            if vol < 0 or vol > 300:
                errors.append(f'{label} must be between -30000 and 1500')
            settings[field] = vol
        except (ValueError, TypeError):
            errors.append(f'{label} must be an integer')
            settings[field] = DEFAULTS[field]

    # Validate enabled_prayers
    enabled = settings.get('enabled_prayers', DEFAULTS['enabled_prayers'])
    if not isinstance(enabled, list):
        errors.append('enabled_prayers must be a list')
        enabled = DEFAULTS['enabled_prayers']
    else:
        for p in enabled:
            if p not in VALID_PRAYERS:
                errors.append(f'Invalid prayer: {p}')
    settings['enabled_prayers'] = enabled

    # Validate time_offsets
    offsets = settings.get('time_offsets', DEFAULTS['time_offsets'])
    if not isinstance(offsets, dict):
        errors.append('time_offsets must be a dict')
        offsets = DEFAULTS['time_offsets']
    else:
        valid_offset_keys = ['fajr', 'sunrise', 'dhuhr', 'asr', 'maghrib', 'isha']
        cleaned_offsets = {}
        for key in valid_offset_keys:
            val = offsets.get(key, 0)
            try:
                val = int(val)
                if val < -30 or val > 30:
                    errors.append(f'Time offset for {key} must be between -30 and 30 minutes')
                cleaned_offsets[key] = val
            except (ValueError, TypeError):
                errors.append(f'Time offset for {key} must be an integer')
                cleaned_offsets[key] = 0
        offsets = cleaned_offsets
    settings['time_offsets'] = offsets

    # Validate audio_files
    audio_files = settings.get('audio_files', DEFAULTS['audio_files'])
    if not isinstance(audio_files, dict):
        errors.append('audio_files must be a dict')
        audio_files = DEFAULTS['audio_files']
    else:
        for prayer, filename in audio_files.items():
            if prayer not in VALID_PRAYERS:
                errors.append(f'Unknown prayer in audio_files: {prayer}')
            filepath = pathjoin(root_dir, filename)
            if not os.path.exists(filepath):
                errors.append(f'Audio file not found: {filename}')
    settings['audio_files'] = audio_files

    # Validate surahbaqarah_time
    import re
    surah_time = settings.get('surahbaqarah_time', DEFAULTS['surahbaqarah_time'])
    if surah_time:
        # Validate time format HH:MM
        if not re.match(r'^\d{1,2}:\d{2}$', str(surah_time)):
            errors.append('Surah Baqarah time must be in HH:MM format (e.g., 10:15)')
        else:
            parts = str(surah_time).split(':')
            hour = int(parts[0])
            minute = int(parts[1])
            if hour < 0 or hour > 23:
                errors.append('Surah Baqarah time hour must be between 0 and 23')
            if minute < 0 or minute > 59:
                errors.append('Surah Baqarah time minute must be between 0 and 59')
            settings['surahbaqarah_time'] = surah_time
    else:
        settings['surahbaqarah_time'] = DEFAULTS['surahbaqarah_time']

    if errors:
        return False, errors

    with open(SETTINGS_JSON, 'wt') as f:
        json.dump(settings, f, indent=2)

    return True, []


def get_available_audio_files():
    """Return list of MP3 files in the root directory."""
    files = []
    for f in os.listdir(root_dir):
        if f.lower().endswith('.mp3'):
            files.append(f)
    return sorted(files)


def get_timezone_offset(timezone, date=None):
    """Get the UTC offset for a timezone at a given date.
    
    Args:
        timezone: IANA timezone name (e.g., 'Asia/Dubai')
        date: datetime object (defaults to now)
    
    Returns:
        Tuple of (utc_offset, is_dst) where offset is in hours
    """
    if date is None:
        import datetime as dt
        date = dt.datetime.now()
    
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(timezone)
        # Get the offset at the given date
        dt_aware = date.replace(tzinfo=tz)
        offset_seconds = dt_aware.utcoffset().total_seconds()
        utc_offset = offset_seconds / 3600.0
        # Check if DST is in effect
        is_dst = bool(dt_aware.dst())
        return utc_offset, is_dst
    except (ImportError, KeyError):
        # Fallback to static offsets if zoneinfo is not available
        offset = TIMEZONE_UTC_OFFSETS.get(timezone, 0)
        return offset, False


def get_timezone_display_name(timezone):
    """Get a human-readable display name for a timezone."""
    if timezone in TIMEZONE_UTC_OFFSETS:
        offset = TIMEZONE_UTC_OFFSETS[timezone]
        offset_str = f"+{offset}" if offset >= 0 else str(offset)
        return f"{timezone} (UTC{offset_str})"
    return timezone
