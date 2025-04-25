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
    def __init__(self, config_file: str, config_overrides: dict = None):
        """
        Initialize the BackupManager with a configuration file.

        Parameters:
        -----------
        config_file : str
            Path to the configuration file.
        config_overrides : dict
            Dictionary containing configuration overrides.
        """
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.config = self.load_config(config_file)
        self.setup_logging()

        # Apply config overrides if provided
        if config_overrides:
            self.config.update(config_overrides)
        backup_age_days = self.config.get("backup_age_days", 30)
        self.backup_age_seconds = backup_age_days * 24 * 60 * 60

    def setup_logging(self):
        """
        Set up logging for the backup process.
        """
        log_dir = Path(self.config["log_dir"])
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{self.timestamp}_backup.log"

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self, config_file: str) -> dict:
        """
        Load configuration from a JSON file.

        Parameters:
        -----------
        config_file : str
            Path to the configuration file.
        """
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
            return config
        except Exception as e:
            raise RuntimeError(f"Fail to load configuration: {str(e)}")

    def update_config(self, updates: dict):
        """
        Update the configuration with new values.

        Parameters:
        -----------
        updates : dict
            Dictionary containing the configuration updates
        """
        self.config.update(updates)

    def verify_files(self, src_file: Path, dst_file: Path) -> bool:
        """
        Verify if source and destination files are identical.

        Parameters:
        -----------
        src_file : Path
            Path to the source file.
        dst_file : Path
            Path to the destination file.
        """

        def calculate_md5(path_file: Path) -> str:
            """
            Calculate the MD5 hash of a file.

            Parameters:
            -----------
            path_file : Path
                Path to the file to calculate the MD5 hash.
            """
            hash_md5 = hashlib.md5()
            with open(path_file, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()

        try:
            src_md5 = calculate_md5(src_file)
            dst_md5 = calculate_md5(dst_file)
            return src_md5 == dst_md5
        except Exception as e:
            self.logger.error(f"File verification failed {src_file}: {str(e)}")
            return False

    def safe_delete_subfolder(self, path_subfolder: Path) -> bool:
        """
        Safely delete a folder.

        Parameters:
        -----------
        path_subfolder : Path
            Path to the folder to be deleted.
        """
        try:
            if self.config["delete_source"]:
                shutil.rmtree(path_subfolder)
                self.logger.info(f"Source folder deleted: {path_subfolder}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to delete {path_subfolder}: {str(e)}")
        return False

    def generate_report(
        self,
        successful: List[Path],
        failed: List[Path],
        start_time: datetime,
    ):
        """
        Generate backup report.

        Parameters:
        -----------
        successful : List[Path]
            List of successfully backed up folders.
        failed : List[Path]
            List of folders that failed to back up.
        start_time : datetime
            Start time of the backup process.
        """
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

        for path_file in failed:
            report.append(f"- {path_file}")

        report_file = Path(self.config["log_dir"]) / f"{self.timestamp}_report.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report))

        self.logger.info(f"Backup report generated: {report_file}")

    def get_subfolders_to_backup(self) -> List[Path]:
        """
        Get list of subfolders to backup.
        """

        def should_backup_subfolder(path_subfolder: Path) -> bool:
            """
            Check if a subfolder needs to be backed up

            Condition:
                All files in the folder haven't been modified in the configured
                number of days

            Parameters:
            -----------
            path_subfolder : Path
                Path to the subfolder to check.
            """

            try:
                for path_file in path_subfolder.rglob("*"):
                    if path_file.is_file():
                        now = datetime.now().timestamp()
                        last_modified = path_file.stat().st_mtime
                        time_diff = now - last_modified
                        # Skip the entire folder if any file was modified within the configured time
                        if time_diff < self.backup_age_seconds:
                            self.logger.info(
                                f"Skipping subfolder {path_subfolder} - recent changes detected"
                            )
                            return False
                return True
            except Exception as e:
                self.logger.error(
                    f"Error checking subfolder {path_subfolder}: {str(e)}"
                )
                return False

        src_dir = Path(self.config["src_dir"])
        subfolders_to_backup = []
        excluded = set(self.config["excluded_patterns"])

        self.logger.info("Starting subfolder scan...")
        console.print("[cyan]Scanning subfolders...[/cyan]")

        try:
            for path_subfolder in src_dir.iterdir():
                if path_subfolder.is_dir():
                    if not any(path_subfolder.match(pattern) for pattern in excluded):
                        if should_backup_subfolder(path_subfolder):
                            subfolders_to_backup.append(path_subfolder)
                            self.logger.info(
                                f"Subfolder {path_subfolder} queued for backup"
                            )

            console.print(
                f"[green]Scanning complete, found {len(subfolders_to_backup)} subfolders to backup[/green]"
            )
            return subfolders_to_backup
        except Exception as e:
            self.logger.error(f"Error scanning subfolders: {str(e)}")
            return []

    def backup_subfolder(self, path_subfolder: Path) -> bool:
        """
        Backup a single subfolder
        """
        try:
            dst_dir = Path(self.config["dst_dir"])
            timestamped_dst_dir = dst_dir / self.timestamp
            relative_path = path_subfolder.relative_to(Path(self.config["src_dir"]))
            dst_subfolder = timestamped_dst_dir / relative_path

            # Copy the entire folder
            dst_subfolder.mkdir(parents=True, exist_ok=True)
            all_files = list(path_subfolder.rglob("*"))
            all_files = [f for f in all_files if f.is_file()]
            with Progress() as progress:
                task = progress.add_task(
                    f"[yellow]Copying {len(all_files)} files[/yellow]",
                    total=len(all_files),
                )
                for src_file in all_files:
                    dst_file = dst_subfolder / src_file.relative_to(path_subfolder)
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                    progress.update(task, advance=1)

            # Verify all files
            if self.config["verify_copy"]:
                with Progress() as progress:
                    task = progress.add_task(
                        f"[yellow]Verifying {len(all_files)} files[/yellow]",
                        total=len(all_files),
                    )
                    for src_file in all_files:
                        dst_file = dst_subfolder / src_file.relative_to(path_subfolder)
                        if not self.verify_files(src_file, dst_file):
                            raise ValueError(f"File verification failed for {src_file}")
                        progress.update(task, advance=1)
            return True
        except Exception as e:
            self.logger.error(f"Failed to backup subfolder {path_subfolder}: {str(e)}")
            return False

    def run_backup(self):
        """
        Execute backup process
        """
        start_time = datetime.now()
        self.logger.info("Starting backup process")

        try:
            path_subfolders = self.get_subfolders_to_backup()
            if not path_subfolders:
                self.logger.info("No subfolders found to backup")
                return

            successful_backups = []
            failed_backups = []

            total_folders = len(path_subfolders)
            for idx, path_subfolder in enumerate(path_subfolders, 1):
                console.print(
                    f"[blue]Processing folder ({idx}/{total_folders}): {path_subfolder.name}[/blue]"
                )
                if self.backup_subfolder(path_subfolder):
                    successful_backups.append(path_subfolder)
                    if self.config["delete_source"]:
                        self.safe_delete_subfolder(path_subfolder)
                else:
                    failed_backups.append(path_subfolder)

            # Generate report
            self.generate_report(successful_backups, failed_backups, start_time)

        except Exception as e:
            self.logger.error(f"Error during backup process: {str(e)}")
            raise


# %%
if __name__ == "__main__":
    config_file = "/mnt/nfs/home/wenruiwu/projects/backup_win/config.json"
    backup_manager = BackupManager(config_file)
    backup_manager.run_backup()
