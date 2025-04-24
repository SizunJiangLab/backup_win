#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
from backup_win.utils import BackupManager
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
        "--no-verify", action="store_true", help="Skip file verification"
    )
    parser.add_argument(
        "--delete-source", action="store_true", help="Delete source files after backup"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        # Initialize backup manager
        manager = BackupManager(args.config)

        # Override config file settings if command line arguments are provided
        if args.src:
            manager.config["src_dir"] = args.src
        if args.dst:
            manager.config["dst_dir"] = args.dst
        if args.no_verify:
            manager.config["verify_copy"] = False
        if args.delete_source:
            manager.config["delete_source"] = True

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
