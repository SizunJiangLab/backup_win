# Windows Backup System

A secure and reliable folder backup tool that supports intelligent subfolder backup with time-based filtering, file integrity verification and progress tracking with rich console output.

## 1. Main Features

- Intelligent subfolder backup with time-based filtering
- Automatic detection of inactive subfolders (not modified in the last n days)
- File integrity verification using MD5 checksum
- Rich console output with progress bars
- Detailed backup logs and reports
- Optional source folder deletion after backup
- Configurable file exclusion patterns
- Command-line interface with configuration overrides

## 2. Installation

```bash
uv build
pip install dist/backup_win-0.1.1-py3-none-any.whl
```

## 3. Configuration

- `src_dir`: Source directory to backup
- `dst_dir`: Destination directory for backups
- `log_dir`: Directory for storing logs and reports
- `verify_copy`: Whether perform MD5 checksum verification after copying
- `delete_source`: Whether delete source folders after successful backup
- `excluded_patterns`: List of glob patterns for folders to exclude
- `backup_age_days`: Number of days a folder must be unmodified to be eligible for backup

## 4. Backup Strategy

The system implements an intelligent backup strategy:

1. It only backs up subfolders where all files haven't been modified in the last n days
2. Each backup creates a new timestamped folder in the destination directory
3. Complete subfolder structure is preserved in the backup
4. Optional source folder deletion after successful backup and verification
5. Comprehensive verification ensures backup integrity

## 5. Usage

Run backup with default configuration:

```plain
usage: backup-win [-h] [-c CONFIG] [--src SRC] [--dst DST] [--log-dir LOG_DIR] [--no-verify] [--delete-source] [--exclude EXCLUDE] [--backup-age-days BACKUP_AGE_DAYS]

Folder Backup Tool

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file path (default: config.json)
  --src SRC             Source directory path (optional, overrides config file setting)
  --dst DST             Destination directory path (optional, overrides config file setting)
  --log-dir LOG_DIR     Directory for storing logs (optional, overrides config file setting)
  --no-verify           Skip file verification
  --delete-source       Delete source files after backup
  --exclude EXCLUDE     File patterns to exclude (can be used multiple times)
  --backup-age-days BACKUP_AGE_DAYS
                        Number of days a folder must be unmodified to be eligible for backup (default: 30)`
```

## 6. Output Structure

The backup process creates the following structure:

```tree
dst_dir/YYYYMMDD_HHMMSS
├── subfolder1
│   └── files...
├── subfolder2
│   ├── folder1
│   │   └── files...
│   └── folder2
│       └── files...
└── subfolders...

logs
├── YYYYMMDD_HHMMSS_backup.log
└── YYYYMMDD_HHMMSS_report.txt
```

## 7. Windows Setup

### `bat` Script

```bat
@echo off
"C:\Users\Akoya Biosciences\AppData\Local\Programs\Python\Python313\Scripts\backup-win.exe" -c "D:\script\backup-win\config.json"
```

### Configuration

```json
{
    "src_dir": "D:\\Data\\Fusion",
    "dst_dir": "Z:\\Storage\\00_storage",
    "log_dir": "Z:\\Storage\\00_storage_log",
    "verify_copy": true,
    "delete_source": true,
    "excluded_patterns": [],
    "backup_age_days": 30
}
```

### Setup Task Scheduler

1. `Win + R` ➡️ `taskschd.msc` ➡️ OK.
2. Actions (right panel) ➡️ Create Basic Task...
    - Create Basic Task: `[Name]`
    - Trigger: ...
    - Action: `Start a program`
        - Program: `D:\script\backup-win\backup-win.bat`
