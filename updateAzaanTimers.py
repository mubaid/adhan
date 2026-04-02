#!/usr/bin/env python3

import datetime
import time
import json
import sys
import os
from os.path import dirname, abspath, join as pathjoin
import argparse

root_dir = dirname(abspath(__file__))
sys.path.insert(0, pathjoin(root_dir, 'crontab'))

from praytimes import PrayTimes
PT = PrayTimes()

from crontab import CronTab
system_cron = CronTab(user='root')

# Import timezone utilities from settings_manager
import sys
sys.path.insert(0, pathjoin(root_dir))
from settings_manager import get_timezone_offset

#HELPER FUNCTIONS
#---------------------------------
#---------------------------------
#Function to add azaan time to cron
def parseArgs():
    parser = argparse.ArgumentParser(description='Calculate prayer times and install cronjobs to play Adhan')
    parser.add_argument('--lat', type=float, dest='lat',
                        help='Latitude of the location, for example 30.345621')
    parser.add_argument('--lng', type=float, dest='lng',
                        help='Longitude of the location, for example 60.512126')
    parser.add_argument('--method', choices=['MWL', 'ISNA', 'Egypt', 'Makkah', 'Karachi', 'Tehran', 'Jafari'],
                        dest='method',
                        help='Method of calculation')
    parser.add_argument('--fajr-azaan-volume', type=int, dest='fajr_azaan_vol',
                        help='Volume for fajr azaan in millibels, 1500 is loud and -30000 is quiet (default 0)')
    parser.add_argument('--azaan-volume', type=int, dest='azaan_vol',
                        help='Volume for azaan (other than fajr) in millibels, 1500 is loud and -30000 is quiet (default 0)')
    return parser

def mergeArgs(args):
    json_path = pathjoin(root_dir, '.settings.json')
    csv_path = pathjoin(root_dir, '.settings')

    # Try loading JSON settings first
    settings = None
    if os.path.exists(json_path):
        try:
            with open(json_path, 'rt') as f:
                settings = json.load(f)
            print('Loaded settings from .settings.json')
        except Exception:
            print('Failed to read .settings.json, falling back to CSV')

    if settings:
        lat = settings.get('latitude')
        lng = settings.get('longitude')
        timezone = settings.get('timezone', 'UTC')
        method = settings.get('method')
        fajr_azaan_vol = settings.get('fajr_volume', 0)
        azaan_vol = settings.get('azaan_volume', 150)
        asr_method = settings.get('asr_method', 'Hanafi')
        enabled_prayers = settings.get('enabled_prayers', ['dahwaekubra', 'dhuhr', 'asr', 'maghrib', 'isha', 'surahbaqarah'])
        audio_files = settings.get('audio_files', {})
        time_offsets = settings.get('time_offsets', {'fajr': 0, 'sunrise': -6, 'dhuhr': 3, 'asr': 3, 'maghrib': 3, 'isha': 0})
        surahbaqarah_vol = settings.get('surahbaqarah_volume', 75)
        surahbaqarah_time = settings.get('surahbaqarah_time', '10:15')
    else:
        # Fall back to CSV
        lat = lng = timezone = method = fajr_azaan_vol = azaan_vol = None
        asr_method = 'Hanafi'
        enabled_prayers = ['dahwaekubra', 'dhuhr', 'asr', 'maghrib', 'isha', 'surahbaqarah']
        audio_files = {}
        time_offsets = {'fajr': 0, 'sunrise': -6, 'dhuhr': 3, 'asr': 3, 'maghrib': 3, 'isha': 0}
        surahbaqarah_vol = 75
        surahbaqarah_time = '10:15'
        try:
            with open(csv_path, 'rt') as f:
                lat, lng, method, fajr_azaan_vol, azaan_vol = f.readlines()[0].split(',')
        except:
            print('No .settings file found')

    # CLI args override file values
    if args.lat:
        lat = args.lat
    if lat:
        lat = float(lat)
    if args.lng:
        lng = args.lng
    if lng:
        lng = float(lng)
    if args.method:
        method = args.method
    if args.fajr_azaan_vol:
        fajr_azaan_vol = args.fajr_azaan_vol
    if fajr_azaan_vol:
        fajr_azaan_vol = int(fajr_azaan_vol)
    if args.azaan_vol:
        azaan_vol = args.azaan_vol
    if azaan_vol:
        azaan_vol = int(azaan_vol)

    # Save to CSV for backward compatibility (if no JSON exists)
    if not os.path.exists(json_path):
        with open(csv_path, 'wt') as f:
            f.write('{},{},{},{},{}'.format(lat or '', lng or '', method or '',
                    fajr_azaan_vol or 0, azaan_vol or 0))

    return lat or None, lng or None, timezone or 'UTC', method or None, fajr_azaan_vol or 0, azaan_vol or 0, asr_method, enabled_prayers, audio_files, time_offsets, surahbaqarah_vol or 75, surahbaqarah_time or '10:15'

def addAzaanTime (strPrayerName, strPrayerTime, objCronTab, strCommand):
  job = objCronTab.new(command=strCommand,comment=strPrayerName)  
  timeArr = strPrayerTime.split(':')
  hour = timeArr[0]
  min = timeArr[1]
  job.minute.on(int(min))
  job.hour.on(int(hour))
  job.set_comment(strJobComment)
  print(job)
  return

def addSurahBaqarahTime (strPrayerName, strPrayerTime, objCronTab, strCommand):
  job = objCronTab.new(command=strCommand,comment=strPrayerName)  
  timeArr = strPrayerTime.split(':')
  hour = timeArr[0]
  min = timeArr[1]
  job.minute.on(int(min))
  job.hour.on(int(hour))
  job.set_comment(strJobComment)
  print(job)
  return

def addUpdateCronJob (objCronTab, strCommand):
  job = objCronTab.new(command=strCommand)
  job.minute.on(15)
  job.hour.on(3)
  job.set_comment(strJobComment)
  print(job)
  return

def addClearLogsCronJob (objCronTab, strCommand):
  job = objCronTab.new(command=strCommand)
  job.day.on(1)
  job.minute.on(0)
  job.hour.on(0)
  job.set_comment(strJobComment)
  print(job)
  return
#---------------------------------
#---------------------------------
#HELPER FUNCTIONS END

#Parse arguments
parser = parseArgs()
args = parser.parse_args()
#Merge args with saved values if any
lat, lng, timezone, method, fajr_azaan_vol, azaan_vol, asr_method, enabled_prayers, audio_files, time_offsets, surahbaqarah_vol, surahbaqarah_time = mergeArgs(args)
print(lat, lng, timezone, method, fajr_azaan_vol, azaan_vol, surahbaqarah_time)
#Complain if any mandatory value is missing
if not lat or not lng or not method:
    parser.print_usage()
    sys.exit(1)

#Set calculation method, utcOffset and dst here
#By default uses timezone from settings
#--------------------
now = datetime.datetime.now()
PT.setMethod(method)
PT.adjust({'asr': asr_method})
utcOffset, isDst = get_timezone_offset(timezone, now)

# Build command builder using settings
def build_command(prayer):
    audio_file = audio_files.get(prayer, 'azaan-dua-new.mp3')
    if prayer == 'fajr':
        vol = fajr_azaan_vol
    elif prayer == 'iftardua':
        vol = azaan_vol * 2
    elif prayer == 'surahbaqarah':
        vol = surahbaqarah_vol
    else:
        vol = azaan_vol
    return '{}/playAzaan.sh {}/{} {}'.format(root_dir, root_dir, audio_file, vol)

strUpdateCommand = '{}/updateAzaanTimers.py >> {}/adhan.log 2>&1'.format(root_dir, root_dir)
strClearLogsCommand = 'truncate -s 0 {}/adhan.log 2>&1'.format(root_dir)
strJobComment = 'rpiAdhanClockJob'

# Remove existing jobs created by this script
system_cron.remove_all(comment=strJobComment)

PT.tune(time_offsets)

# Calculate prayer times

# If you need to setup Offsets / Tune the timings as precautions, uncomment this line
#PT.tune({ 'fajr': 2, 'sunrise': 0, 'dhuhr': 3, 'asr': 3, 'maghrib': 3, 'isha': 3 })

# If you need to use Hanafi asr timings instead of standard, uncomment this line
#PT.adjust({'asr': 'Hanafi'})

times = PT.getTimes((now.year,now.month,now.day), (lat, lng), utcOffset, isDst) 
print(times['imsak'])
print(times['fajr'])
print(times['dahwaekubra'])
print(times['dhuhr'])
print(times['asr'])
print(times['maghrib'])
print(times['isha'])

# Prayer name to time key mapping
prayer_time_keys = {
    'fajr': 'fajr',
    'imsak': 'imsak',
    'dahwaekubra': 'dahwaekubra',
    'dhuhr': 'dhuhr',
    'asr': 'asr',
    'maghrib': 'maghrib',
    'iftardua': 'maghrib',
    'isha': 'isha',
}

# Add times to crontab based on enabled_prayers
for prayer in enabled_prayers:
    if prayer == 'surahbaqarah':
        prayer_time = surahbaqarah_time
    elif prayer in prayer_time_keys:
        prayer_time = times.get(prayer_time_keys[prayer])
    else:
        continue
    if not prayer_time:
        continue
    command = build_command(prayer)
    addAzaanTime(prayer, prayer_time, system_cron, command)

# Run this script again overnight
addUpdateCronJob(system_cron, strUpdateCommand)

# Clear the logs every month
addClearLogsCronJob(system_cron,strClearLogsCommand)

system_cron.write_to_user(user='root')
print('Script execution finished at: ' + str(now))
