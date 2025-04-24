# Windows Backup System

A secure and reliable folder backup tool that supports intelligent subfolder backup with time-based filtering, file integrity verification and progress tracking with rich console output.

## Main Features

- Intelligent subfolder backup with time-based filtering
- Automatic detection of inactive subfolders (not modified in the last 30 days)
- File integrity verification using MD5 checksum
- Rich console output with progress bars
- Detailed backup logs and reports
- Optional source folder deletion after backup
- Configurable file exclusion patterns
- Command-line interface with configuration overrides

## Installation

1. This project requires Python 3.10 or higher. Install dependencies using:

```bash
pip install -e .
```

## Configuration

Create or edit `config.json` with the following options:

```json
{
   "src_dir": "/path/to/source",
   "dst_dir": "/path/to/destination",
   "log_dir": "/path/to/logs",
   "verify_copy": true,
   "delete_source": false,
   "excluded_patterns": []
}
```

### Configuration Options

- `src_dir`: Source directory to backup
- `dst_dir`: Destination directory for backups
- `log_dir`: Directory for storing logs and reports
- `verify_copy`: Enable MD5 checksum verification (default: true)
- `delete_source`: Delete source folders after successful backup (default: false)
- `excluded_patterns`: List of glob patterns for folders to exclude

## Backup Strategy

The system implements an intelligent backup strategy:

1. It only backs up subfolders where all files haven't been modified in the last 30 days
2. Each backup creates a new timestamped folder in the destination directory
3. Complete subfolder structure is preserved in the backup
4. Optional source folder deletion after successful backup and verification
5. Comprehensive verification ensures backup integrity

## Usage

Run backup with default configuration:

```bash
python backup.py
```

### Command Line Arguments

- `-c`, `--config`: Configuration file path (default: config.json)
- `--src`: Override source directory from config
- `--dst`: Override destination directory from config
- `--no-verify`: Skip file verification
- `--delete-source`: Delete source files after backup

Example with command line options:

```bash
python backup.py --src /data/source --dst /data/backup --no-verify
```

## Output Structure

The backup process creates the following structure:

```tree
dst_dir/YYYYMMDD_HHMMSS
├── df_run
│   └── files...
├── output
│   ├── folder1
│   │   ├── md5sum_1.txt
│   │   ├── md5sum_2.txt
│   │   └── checksum_diff.txt
│   └── folder2
│       ├── md5sum.csv
│       ├── md5sum_1.txt
│       ├── md5sum_2.txt
│       └── md5sum_diff.csv
└── other_folders
    └── ...

logs
├── backup_YYYYMMDD_HHMMSS.log
└── report_YYYYMMDD_HHMMSS.txt
```

### Backup Report Contents

The backup report includes:

- Start and end times
- Total duration
- Number of successful/failed subfolder backups
- List of any failed subfolders
- Verification status for each backed up folder
