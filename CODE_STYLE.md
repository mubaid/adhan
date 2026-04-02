# Adhan Clock - Code Style

## Language & Standards

| Aspect | Standard |
|--------|----------|
| **Primary Language** | Python 3 |
| **Scripting** | Bash (playAzaan.sh) |
| **Style Guide** | PEP 8 |
| **Shebang** | `#!/usr/bin/env python3` |

## Python Style Guidelines

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Functions | `snake_case` | `parseArgs()`, `addAzaanTime()` |
| Variables | `snake_case` | `lat`, `lng`, `fajr_azaan_vol` |
| Constants | `UPPER_SNAKE_CASE` | `strJobComment` |
| Classes | `PascalCase` | (none currently used) |
| Modules | `snake_case` | `praytimes.py`, `updateAzaanTimers.py` |

### Function Guidelines

- **Max line length**: 100 characters
- **Blank lines**: 2 between top-level definitions, 1 between functions
- **Docstrings**: Use for public APIs only
- **Type hints**: Optional but encouraged for new code

### Current Code Patterns

**Argument Parser Setup:**
```python
def parseArgs():
    parser = argparse.ArgumentParser(description='...')
    parser.add_argument('--lat', type=float, dest='lat',
                        help='Latitude of the location')
    return parser
```

**Cron Job Creation:**
```python
def addAzaanTime(strPrayerName, strPrayerTime, objCronTab, strCommand):
    job = objCronTab.new(command=strCommand, comment=strPrayerName)
    timeArr = strPrayerTime.split(':')
    job.minute.on(int(timeArr[1]))
    job.hour.on(int(timeArr[0]))
    print(job)
    return
```

**Settings File Management:**
```python
def mergeArgs(args):
    file_path = pathjoin(root_dir, '.settings')
    # Load existing values first
    # Merge with command-line arguments
    # Save updated values
```

## Shell Script Style (playAzaan.sh)

- Use `#!/usr/bin/env bash`
- Use `set -e` for error handling
- Quote all variable expansions
- Use `$(command)` over backticks

## File Organization

```
adhan/
├── updateAzaanTimers.py    # Main entry point
├── praytimes.py            # Prayer time calculations
├── playAzaan.sh            # Audio playback script
├── ARCHITECTURE.md         # This file
├── CODE_STYLE.md           # Code standards
├── .settings               # Saved configuration
├── *.mp3                   # Audio files
├── before-hooks.d/        # Pre-adhan scripts
├── after-hooks.d/          # Post-adhan scripts
└── crontab/               # python-crontab library
```

## Error Handling

- Use `try/except` for file I/O operations
- Print errors to stdout (for cron logging)
- Exit with `sys.exit(1)` on critical failures

## Cron Job Comments

All cron jobs created by this script use the comment `rpiAdhanClockJob` for identification and removal.

## Future Improvements (Code Quality)

1. Add type hints to function signatures
2. Replace string formatting with f-strings
3. Add unit tests for prayer time calculations
4. Use dataclasses for configuration objects
5. Add logging instead of print statements
6. Create proper exception classes
