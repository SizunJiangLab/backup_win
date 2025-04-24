# %%
import hashlib
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from rich.console import Console
from rich.progress import Progress

console = Console()


class BackupManager:
    def __init__(self, config_path: str):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.config = self.load_config(config_path)
        self.setup_logging()

    def load_config(self, config_path: str) -> dict:
        """
        Load configuration from a JSON file.
        """
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            return config
        except Exception as e:
            raise RuntimeError(f"Fail to load configuration: {str(e)}")

    def setup_logging(self):
        """
        Set up logging for the backup process.
        """
        log_dir = Path(self.config["log_dir"])
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"backup_{self.timestamp}.log"

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def calculate_md5(self, file_path: Path) -> str:
        """
        Calculate the MD5 hash of a file.
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get_files_to_backup(self) -> List[Path]:
        """
        Get a list of files to back up, excluding those matching the patterns in the config.
        """
        src_dir = Path(self.config["src_dir"])
        files_to_backup = []
        excluded = set(self.config["excluded_patterns"])

        self.logger.info("Starting file scan (single-thread mode)...")
        console.print("[cyan]Scanning file list...[/cyan]")

        for path in src_dir.rglob("*"):
            if path.is_file():
                # Check if file is in exclude list
                if not any(path.match(pattern) for pattern in excluded):
                    files_to_backup.append(path)

        console.print(
            f"[green]Scan complete, found {len(files_to_backup)} files[/green]"
        )
        return files_to_backup

    def verify_files(self, src_file: Path, dst_file: Path) -> bool:
        """Verify if source and destination files are identical"""
        try:
            src_md5 = self.calculate_md5(src_file)
            dst_md5 = self.calculate_md5(dst_file)
            return src_md5 == dst_md5
        except Exception as e:
            self.logger.error(f"File verification failed {src_file}: {str(e)}")
            return False

    def backup_file(self, src_file: Path, relative_path: Path) -> bool:
        """Backup a single file"""
        try:
            dst_dir = Path(self.config["dst_dir"])
            timestamped_dst_dir = dst_dir / self.timestamp
            dst_file = timestamped_dst_dir / relative_path

            # Create destination directory
            dst_file.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(src_file, dst_file)

            # Verify file
            if self.config["verify_copy"]:
                if not self.verify_files(src_file, dst_file):
                    raise ValueError("File verification failed")

            return True
        except Exception as e:
            self.logger.error(f"Failed to backup file {src_file}: {str(e)}")
            return False

    def safe_delete(self, file_path: Path) -> bool:
        """Safely delete a file"""
        try:
            if self.config["delete_source"]:
                file_path.unlink()
                self.logger.info(f"Source file deleted: {file_path}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to delete file {file_path}: {str(e)}")
        return False

    def generate_report(
        self, successful: List[Path], failed: List[Path], start_time: datetime
    ):
        """Generate backup report"""
        end_time = datetime.now()
        duration = end_time - start_time

        report = [
            "Backup Task Report",
            "=" * 50,
            f"Start Time: {start_time}",
            f"End Time: {end_time}",
            f"Total Duration: {duration}",
            f"Successful: {len(successful)}",
            f"Failed: {len(failed)}",
            "\nFailed Files:",
        ]

        for file in failed:
            report.append(f"- {file}")

        report_path = Path(self.config["log_dir"]) / f"report_{self.timestamp}.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report))

        self.logger.info(f"Backup report generated: {report_path}")

    def run_backup(self):
        """Execute backup process"""
        start_time = datetime.now()
        self.logger.info("Starting backup process (single-thread mode)")

        try:
            files = self.get_files_to_backup()
            if not files:
                self.logger.info("No files found to backup")
                return

            src_base = Path(self.config["src_dir"])
            successful_backups = []
            failed_backups = []

            with Progress() as progress:
                backup_task = progress.add_task(
                    "[green]Backing up files sequentially...", total=len(files)
                )

                for idx, src_file in enumerate(files, 1):
                    relative_path = src_file.relative_to(src_base)
                    console.print(
                        f"[cyan]Processing ({idx}/{len(files)}): {relative_path}[/cyan]"
                    )

                    if self.backup_file(src_file, relative_path):
                        successful_backups.append(src_file)
                        if self.config["delete_source"]:
                            self.safe_delete(src_file)
                    else:
                        failed_backups.append(src_file)
                    progress.update(backup_task, advance=1)

            # Generate report
            self.generate_report(successful_backups, failed_backups, start_time)

        except Exception as e:
            self.logger.error(f"Error during backup process: {str(e)}")
            raise


# %%
if __name__ == "__main__":
    config_path = "/mnt/nfs/home/wenruiwu/projects/backup_win/config.json"
    backup_manager = BackupManager(config_path)
    backup_manager.run_backup()
