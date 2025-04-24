# Windows Backup System

A secure and reliable folder backup tool that supports file integrity verification and progress tracking with rich console output.

## Main Features

- File integrity verification using MD5 checksum
- Rich console output with progress bars
- Detailed backup logs and reports
- Optional source file deletion after backup
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
- `delete_source`: Delete source files after successful backup (default: false)
- `excluded_patterns`: List of glob patterns for files to exclude

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

## Output Files

The backup process generates the following files in the log directory:

- `backup_YYYYMMDD_HHMMSS.log`: Detailed backup operation log
- `report_YYYYMMDD_HHMMSS.txt`: Backup summary report including:
    - Start and end times
    - Total duration
    - Number of successful/failed files
    - List of any failed files
