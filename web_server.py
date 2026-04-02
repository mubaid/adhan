#!/usr/bin/env python3

import datetime
import time
import os
import sys
from os.path import dirname, abspath, join as pathjoin

root_dir = dirname(abspath(__file__))
sys.path.insert(0, pathjoin(root_dir, 'crontab'))

from flask import Flask, render_template, request, jsonify
from praytimes import PrayTimes
from crontab import CronTab
from settings_manager import load_settings, save_settings, get_available_audio_files, get_timezone_offset

app = Flask(__name__)
JOB_COMMENT = 'rpiAdhanClockJob'

# Volume multipliers for special prayers
VOLUME_MULTIPLIERS = {
    'iftardua': 2.0,
}


def calculate_times(settings, date=None):
    """Calculate prayer times for a given date using current settings."""
    pt = PrayTimes()
    pt.setMethod(settings['method'])
    pt.adjust({'asr': settings.get('asr_method', 'Hanafi')})
    pt.tune(settings.get('time_offsets', {'fajr': 0, 'sunrise': -6, 'dhuhr': 3, 'asr': 3, 'maghrib': 3, 'isha': 0}))

    if date is None:
        date = datetime.datetime.now()

    # Use timezone from settings if available, otherwise fallback to system timezone
    timezone_name = settings.get('timezone', 'UTC')
    utc_offset, is_dst = get_timezone_offset(timezone_name, date)

    lat = settings.get('latitude')
    lng = settings.get('longitude')
    if lat is None or lng is None:
        return None

    times = pt.getTimes((date.year, date.month, date.day), (lat, lng), utc_offset, is_dst)
    return times


def build_cron_command(prayer, settings):
    """Build the playAzaan.sh command for a given prayer."""
    audio_files = settings.get('audio_files', {})
    audio_file = audio_files.get(prayer, 'azaan-dua-new.mp3')

    azaan_vol = settings.get('azaan_volume', 150)
    fajr_vol = settings.get('fajr_volume', 0)

    if prayer == 'fajr':
        vol = fajr_vol
    elif prayer == 'surahbaqarah':
        vol = settings.get('surahbaqarah_volume', 75)
    elif prayer in VOLUME_MULTIPLIERS:
        vol = int(azaan_vol * VOLUME_MULTIPLIERS[prayer])
    else:
        vol = azaan_vol

    return '{}/playAzaan.sh {}/{} {}'.format(root_dir, root_dir, audio_file, vol)


def apply_cron_jobs(settings):
    """Regenerate all cron jobs from settings. Returns (success, message)."""
    lat = settings.get('latitude')
    lng = settings.get('longitude')
    if lat is None or lng is None:
        return False, 'Latitude and longitude must be configured before applying.'

    times = calculate_times(settings)
    if times is None:
        return False, 'Could not calculate prayer times. Check your location settings.'

    try:
        system_cron = CronTab(user='root')
        system_cron.remove_all(comment=JOB_COMMENT)

        enabled_prayers = settings.get('enabled_prayers', [])

        # Prayer time keys that map to calculated times
        prayer_time_keys = {
            'fajr': 'fajr',
            'imsak': 'imsak',
            'dahwaekubra': 'dahwaekubra',
            'dhuhr': 'dhuhr',
            'asr': 'asr',
            'maghrib': 'maghrib',
            'iftardua': 'iftardua',
            'isha': 'isha',
        }

        for prayer in enabled_prayers:
            if prayer == 'surahbaqarah':
                # Use configurable time from settings
                prayer_time = settings.get('surahbaqarah_time', '10:15')
            elif prayer in prayer_time_keys:
                prayer_time = times.get(prayer_time_keys[prayer])
            else:
                continue

            if not prayer_time:
                continue

            command = build_cron_command(prayer, settings)
            job = system_cron.new(command=command, comment=JOB_COMMENT)
            parts = prayer_time.split(':')
            job.hour.on(int(parts[0]))
            job.minute.on(int(parts[1]))

        # Daily self-update at 3:15 AM
        update_cmd = '{}/updateAzaanTimers.py >> {}/adhan.log 2>&1'.format(root_dir, root_dir)
        update_job = system_cron.new(command=update_cmd, comment=JOB_COMMENT)
        update_job.hour.on(3)
        update_job.minute.on(15)

        # Monthly log truncation
        clear_cmd = 'truncate -s 0 {}/adhan.log 2>&1'.format(root_dir)
        clear_job = system_cron.new(command=clear_cmd, comment=JOB_COMMENT)
        clear_job.day.on(1)
        clear_job.hour.on(0)
        clear_job.minute.on(0)

        system_cron.write_to_user(user='root')
        return True, 'Cron jobs applied successfully.'

    except PermissionError:
        return False, 'Permission denied. Run the server as root to manage cron jobs.'
    except Exception as e:
        return False, 'Failed to apply cron jobs: {}'.format(str(e))


# --- Page Routes ---

@app.route('/')
def dashboard():
    settings = load_settings()
    times = calculate_times(settings)
    now = datetime.datetime.now()

    prayer_list = []
    next_prayer = None
    prayer_keys = ['imsak', 'fajr', 'dahwaekubra', 'dhuhr', 'asr', 'maghrib', 'iftardua', 'isha']
    prayer_labels = {
        'imsak': 'Imsak', 'fajr': 'Fajr', 'dahwaekubra': 'Dahwa Ekubra',
        'dhuhr': 'Dhuhr', 'asr': 'Asr', 'maghrib': 'Maghrib',
        'iftardua': 'Iftar Dua', 'isha': 'Isha'
    }

    if times:
        for key in prayer_keys:
            t = times.get(key, '--:--')
            is_enabled = key in settings.get('enabled_prayers', [])
            prayer_list.append({
                'key': key,
                'label': prayer_labels.get(key, key),
                'time': t,
                'enabled': is_enabled,
                'audio': settings.get('audio_files', {}).get(key, ''),
            })
            if not next_prayer and is_enabled and t != '--:--':
                try:
                    h, m = map(int, t.split(':'))
                    prayer_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
                    if prayer_dt > now:
                        next_prayer = key
                except ValueError:
                    pass

    configured = settings.get('latitude') is not None and settings.get('longitude') is not None

    return render_template('dashboard.html',
                           settings=settings,
                           prayer_list=prayer_list,
                           next_prayer=next_prayer,
                           configured=configured,
                           now=now)


@app.route('/settings')
def settings_page():
    settings = load_settings()
    audio_files = get_available_audio_files()
    return render_template('settings.html',
                           settings=settings,
                           audio_files=audio_files)


@app.route('/schedule')
def schedule_page():
    try:
        system_cron = CronTab(user='root')
        jobs = []
        for job in system_cron:
            if job.comment == JOB_COMMENT:
                jobs.append({
                    'command': str(job.command),
                    'schedule': str(job.slices),
                    'comment': job.comment,
                })
    except Exception:
        jobs = []
    return render_template('schedule.html', jobs=jobs)


@app.route('/logs')
def logs_page():
    log_path = pathjoin(root_dir, 'adhan.log')
    lines = []
    try:
        with open(log_path, 'rt') as f:
            lines = f.readlines()[-100:]
    except FileNotFoundError:
        pass
    return render_template('logs.html', log_lines=lines)


# --- API Routes ---

@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    settings = load_settings()
    return jsonify(settings)


@app.route('/api/settings', methods=['POST'])
def api_save_settings():
    if request.is_json:
        data = request.get_json()
    else:
        data = parse_form_data(request.form)
    success, errors = save_settings(data)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'errors': errors}), 400


def parse_form_data(form):
    """Parse form-encoded data into settings dict."""
    data = {}
    # Simple numeric/string fields
    for field in ['latitude', 'longitude', 'timezone', 'method', 'asr_method', 'surahbaqarah_time']:
        val = form.get(field)
        if val:
            data[field] = val
    for field in ['fajr_volume', 'azaan_volume', 'surahbaqarah_volume']:
        val = form.get(field)
        if val is not None:
            try:
                data[field] = int(val)
            except ValueError:
                pass
    # Enabled prayers (repeated key)
    data['enabled_prayers'] = form.getlist('enabled_prayers')
    # Time offsets from offset_* keys
    offsets = {}
    for key in ['fajr', 'sunrise', 'dhuhr', 'asr', 'maghrib', 'isha']:
        val = form.get('offset_' + key)
        if val is not None:
            try:
                offsets[key] = int(val)
            except ValueError:
                offsets[key] = 0
    data['time_offsets'] = offsets
    # Audio files from audio_* keys
    audio = {}
    for key in form:
        if key.startswith('audio_'):
            prayer = key[6:]
            audio[prayer] = form[key]
    if audio:
        data['audio_files'] = audio
    return data


@app.route('/api/times', methods=['GET'])
def api_times():
    settings = load_settings()
    date_str = request.args.get('date')
    if date_str:
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400
    else:
        date = datetime.datetime.now()

    times = calculate_times(settings, date)
    if times is None:
        return jsonify({'error': 'Location not configured.'}), 400
    return jsonify(times)


@app.route('/api/schedule', methods=['GET'])
def api_schedule():
    try:
        system_cron = CronTab(user='root')
        jobs = []
        for job in system_cron:
            if job.comment == JOB_COMMENT:
                jobs.append({
                    'command': str(job.command),
                    'schedule': str(job.slices),
                })
        return jsonify(jobs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs', methods=['GET'])
def api_logs():
    log_path = pathjoin(root_dir, 'adhan.log')
    n = request.args.get('lines', 50, type=int)
    try:
        with open(log_path, 'rt') as f:
            lines = f.readlines()[-n:]
        return jsonify({'lines': lines})
    except FileNotFoundError:
        return jsonify({'lines': []})


@app.route('/api/apply', methods=['POST'])
def api_apply():
    settings = load_settings()
    success, message = apply_cron_jobs(settings)
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400


@app.route('/api/audio-files', methods=['GET'])
def api_audio_files():
    return jsonify(get_available_audio_files())


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
