#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
from .utils import BackupManager
from rich.console import Console

console = Console()


def parse_args():
    parser = argparse.ArgumentParser(description="Folder Backup Tool")
    parser.add_argument(
        "-c",
        "--config",
        default="config.json",
        help="Configuration file path (default: config.json)",
    )
    parser.add_argument(
        "--src", help="Source directory path (optional, overrides config file setting)"
    )
    parser.add_argument(
        "--dst",
        help="Destination directory path (optional, overrides config file setting)",
    )
    parser.add_argument(
        "--log-dir",
        help="Directory for storing logs (optional, overrides config file setting)",
    )
    parser.add_argument(
        "--no-verify", action="store_true", help="Skip file verification"
    )
    parser.add_argument(
        "--delete-source", action="store_true", help="Delete source files after backup"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        help="File patterns to exclude (can be used multiple times)",
        default=None,
    )
    parser.add_argument(
        "--backup-age-days",
        type=int,
        help="Number of days a folder must be unmodified to be eligible for backup (default: 30)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        # Initialize backup manager with config file first
        config_overrides = {}
        if args.src:
            config_overrides["src_dir"] = args.src
        if args.dst:
            config_overrides["dst_dir"] = args.dst
        if args.log_dir:
            config_overrides["log_dir"] = args.log_dir
        if args.no_verify:
            config_overrides["verify_copy"] = False
        if args.delete_source:
            config_overrides["delete_source"] = True
        if args.exclude:
            config_overrides["excluded_patterns"] = args.exclude
        if (
            args.backup_age_days is not None
        ):  # Changed this condition to properly handle 0
            config_overrides["backup_age_days"] = args.backup_age_days

        # Initialize backup manager with config file and overrides
        manager = BackupManager(args.config, config_overrides)

        # Validate required configuration
        if not manager.config["src_dir"] or not manager.config["dst_dir"]:
            console.print(
                "[red]Error: Both source and destination directories must be set[/red]"
            )
            console.print(
                "Please set them in the config file or specify via command line arguments"
            )
            sys.exit(1)

        # Convert to Path objects and validate paths
        src_path = Path(manager.config["src_dir"])
        dst_path = Path(manager.config["dst_dir"])

        if not src_path.exists():
            console.print(
                f"[red]Error: Source directory does not exist: {src_path}[/red]"
            )
            sys.exit(1)

        # Create destination directory if it doesn't exist
        dst_path.mkdir(parents=True, exist_ok=True)

        # Run backup
        console.print("[green]Starting backup process...[/green]")
        manager.run_backup()
        console.print("[green]Backup completed![/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
